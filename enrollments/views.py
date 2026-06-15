import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

ENROLLMENTS_PER_PAGE = 25

from .models import Enrollment, EnrollmentNote
from .forms import EnrollmentForm, EnrollmentUpdateForm, EnrollmentNoteForm

User = get_user_model()


# ─── AI KURS TAVSIYA MOTORI (Claude API) ─────────────────────────────────────

# Daraja kodlarini tartiblash (lokal tahlilda "keyingi bosqich" ni topish uchun).
# English (CEFR) va IT yo'nalishlari uchun alohida o'sish tartibi.
LEVEL_ORDER = {
    'beginner': 1, 'elementary': 2, 'pre_intermediate': 3, 'intermediate': 4,
    'upper_intermediate': 5, 'advanced': 6, 'ielts': 7,
    'foundation': 1, 'standard': 2, 'bootcamp': 3, 'pro': 4,
}


def _collect_recommendation_data(student):
    """Talabaning o'qish tarixi + markazdagi mavjud kurslar ro'yxati.

    Returns: (data, available)
        data       — Claude promptiga yuboriladigan toza ma'lumot
        available  — lokal tahlil uchun boyitilgan ro'yxat (raw kodlar bilan)
    """
    from attendance.models import Attendance
    from courses.models import Course

    enrollments = list(
        student.enrollments.select_related('course').all()
    )

    def course_info(e):
        return {
            'kurs':       e.course.title if e.course else "Noma'lum",
            'daraja':     e.course.get_level_display() if e.course else '',
            'yonalish':   e.course.get_category_display() if e.course else '',
            'holat':      e.get_status_display(),
        }

    completed = [course_info(e) for e in enrollments if e.status == 'completed']
    active    = [course_info(e) for e in enrollments if e.status == 'active']
    enrolled_course_ids = {e.course_id for e in enrollments if e.course_id}

    # Talabaning yo'nalish/daraja tarixi — lokal "keyingi qadam" mantig'i uchun
    hist_categories = [e.course.category for e in enrollments if e.course]
    hist_levels     = [LEVEL_ORDER.get(e.course.level, 0) for e in enrollments if e.course]
    max_level     = max(hist_levels) if hist_levels else 0
    main_category = (
        max(set(hist_categories), key=hist_categories.count) if hist_categories else None
    )

    # Davomat (umumiy)
    att_qs = (
        Attendance.objects.filter(student__user=student.user)
        if student.user else Attendance.objects.none()
    )
    att_total   = att_qs.count()
    att_present = att_qs.filter(Q(status='present') | Q(status='late')).count()
    att_percent = round(att_present / att_total * 100, 1) if att_total else None

    # Tavsiya qilish mumkin bo'lgan kurslar (hali yozilmaganlari)
    courses_qs = Course.objects.filter(is_active=True).exclude(pk__in=enrolled_course_ids)

    # AI promptiga — toza ro'yxat
    ai_available = [
        {
            'id':          c.pk,
            'nomi':        c.title,
            'yonalish':    c.get_category_display(),
            'daraja':      c.get_level_display(),
            'davomiyligi': c.duration_display,
            'narxi':       float(c.price),
        }
        for c in courses_qs
    ]
    # Lokal tahlilga — raw kategoriya/daraja kodlari bilan
    available = [
        dict(ai, _cat=c.category, _level=LEVEL_ORDER.get(c.level, 0))
        for ai, c in zip(ai_available, courses_qs)
    ]

    return {
        'talaba': {
            'ism':                  student.full_name,
            'tugatgan_kurslar':     completed,
            'faol_kurslar':         active,
            'umumiy_davomat_foizi': att_percent,
            'asosiy_yonalish':      main_category,
            'eng_yuqori_daraja':    max_level,
        },
        'mavjud_kurslar': ai_available,
    }, available


def _recommendation_reason(c, main_cat, max_level, has_history, cheapest):
    """Bitta kurs uchun lokal, mazmunli izoh — har bir kursga turlicha chiqadi."""
    same_cat = bool(main_cat) and c.get('_cat') == main_cat
    lvl      = c.get('_level', 0)
    parts    = []

    if has_history and same_cat and lvl > max_level:
        parts.append(
            f"Sizning {c['yonalish']} yo'nalishingizdagi mantiqiy keyingi bosqich "
            f"({c['daraja']})."
        )
    elif has_history and same_cat:
        parts.append(
            f"{c['yonalish']} yo'nalishini mustahkamlash uchun {c['daraja']} darajadagi kurs."
        )
    elif has_history:
        parts.append(
            f"Bilimlaringizni kengaytirish uchun yangi yo'nalish: "
            f"{c['yonalish']} ({c['daraja']})."
        )
    else:
        parts.append(
            f"Boshlash uchun qulay: {c['yonalish']} yo'nalishi, {c['daraja']} darajadagi kurs."
        )

    parts.append(f"Davomiyligi: {c['davomiyligi']}.")
    if cheapest is not None and c.get('narxi', 0) <= cheapest:
        parts.append("Narxi eng qulaylaridan biri.")
    return " ".join(parts)


def _fallback_recommendations(data, available):
    """AI kreditsiz rejimda qoidaviy tavsiya — talabaning tarixiga moslab tartiblaydi.

    - Tarixi bor talaba: avval shu yo'nalishdagi keyingi bosqich kurslari.
    - Tarixi yo'q talaba: avval boshlovchi (past daraja) kurslari, yo'nalishlar aralash.
    """
    talaba      = data['talaba']
    main_cat    = talaba.get('asosiy_yonalish')
    max_level   = talaba.get('eng_yuqori_daraja', 0)
    # Tarix faqat haqiqiy kurs ma'lumoti bo'lganda hisobga olinadi
    has_history = bool(main_cat) or max_level > 0

    prices   = [c['narxi'] for c in available if c.get('narxi')]
    cheapest = min(prices) if prices else None

    def rank_key(c):
        same_cat = 0 if (main_cat and c.get('_cat') == main_cat) else 1
        lvl      = c.get('_level', 0)
        if has_history:
            # keyingi bosqichga (max_level+1) eng yaqin darajalar oldinda
            level_gap = abs(lvl - (max_level + 1))
        else:
            # tarixsiz — past (boshlovchi) darajalar oldinda
            level_gap = lvl
        return (same_cat, level_gap, c.get('narxi', 0))

    ranked = sorted(available, key=rank_key)

    return [
        {
            'id':    c['id'],
            'nomi':  c['nomi'],
            'sabab': _recommendation_reason(c, main_cat, max_level, has_history, cheapest),
        }
        for c in ranked[:3]
    ]


def recommend_next_course(student_id, user=None):
    """
    Talabaga eng mos keyingi 3 ta kursni Claude API orqali tavsiya qiladi.

    Returns:
        dict: {'success': bool, 'recommendations': list, 'error': str}
    """
    from students.models import Student
    from ai.services import ask_claude, extract_json

    student = get_object_or_404(Student, pk=student_id)
    data, available = _collect_recommendation_data(student)

    if not available:
        return {'success': False,
                'error': "Tavsiya qilish uchun mavjud kurslar topilmadi!"}

    system_prompt = (
        "Siz ta'lim markazi CRM tizimining kurs-tavsiya yordamchisisiz. "
        "Sizga talabaning tugatgan/faol kurslari, davomati va markazdagi "
        "mavjud kurslar ro'yxati beriladi. Mavjud kurslar ichidan talabaga "
        "ENG MOS 3 TASINI tanlang (3 tadan kam bo'lsa — borini).\n\n"
        "Qoidalar:\n"
        "- Faqat 'mavjud_kurslar' ro'yxatidagi kurslardan tanlang, id ni o'zgartirmang\n"
        "- Talabaning darajasi va yo'nalishiga mantiqan mos keladigan keyingi qadamni tanlang\n"
        "- Har bir tavsiyaga o'zbek tilida 1-2 jumlali sabab yozing\n\n"
        "Javobni FAQAT quyidagi JSON formatda qaytaring:\n"
        '{"tavsiyalar": [{"id": <kurs id>, "nomi": "<kurs nomi>", '
        '"sabab": "<o\'zbekcha izoh>"}]}'
    )

    user_prompt = (
        f"Ma'lumotlar (JSON):\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    )

    success, text = ask_claude(
        feature='course_recommend',
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        related_object=f"student:{student.pk}",
        max_tokens=800,
        user=user,
    )

    offline = False
    recommendations = []

    if success:
        parsed = extract_json(text)
        if parsed and isinstance(parsed.get('tavsiyalar'), list):
            # Faqat haqiqatda mavjud kurslarni qoldiramiz
            valid_ids = {c['id'] for c in available}
            recommendations = [
                {
                    'id':    r.get('id'),
                    'nomi':  str(r.get('nomi', '')),
                    'sabab': str(r.get('sabab', '')),
                }
                for r in parsed['tavsiyalar']
                if r.get('id') in valid_ids
            ][:3]

    if not recommendations:
        # AI ishlamadi (kredit/kalit yo'q yoki javob buzilgan) — lokal tavsiya
        offline = True
        recommendations = _fallback_recommendations(data, available)

    return {
        'success':         True,
        'student_name':    student.full_name,
        'recommendations': recommendations,
        'offline':         offline,
    }


@login_required
@require_POST
def enrollment_ai_recommend(request, student_id):
    """AJAX: talaba uchun AI kurs tavsiyasi."""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': "Ruxsat yo'q!"}, status=403)

    result = recommend_next_course(student_id, user=request.user)
    return JsonResponse(result)


# ─── helpers ────────────────────────────────────────────────────────────────

def _get_or_create_student(form_data):
    """
    Telefon raqamiga qarab Student topadi yoki yangisini yaratadi.
    Yangi Student uchun avtomatik User ham yaratiladi.
    """
    from students.models import Student  # circular import oldini olish uchun

    phone = form_data.get('phone', '').strip()
    qs    = Student.objects.filter(phone=phone)

    if qs.exists():
        return qs.first(), False   # (student, created)

    # ── username va parol ─────────────────────────────────────────────────
    username = (form_data.get('username') or '').strip() or phone
    password = (form_data.get('password') or '').strip() or '12345678'

    # username unique bo'lishini ta'minlaymiz
    base_uname = username
    counter    = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_uname}_{counter}"
        counter += 1

    # ── User yaratish ─────────────────────────────────────────────────────
    user = User.objects.create_user(
        username   = username,
        password   = password,
        first_name = form_data.get('first_name', ''),
        last_name  = form_data.get('last_name', ''),
        email      = form_data.get('email', '') or '',
    )
    # Agar User modelida role maydoni bo'lsa
    if hasattr(user, 'role'):
        user.role = 'student'
        update_fields = ['role']
        # Ochiq parol nusxasi (sozlamalarda ko'rinishi uchun)
        if hasattr(user, 'plain_password'):
            user.plain_password = password
            update_fields.append('plain_password')
        user.save(update_fields=update_fields)

    # ── Student yaratish ──────────────────────────────────────────────────
    student = Student.objects.create(
        user         = user if hasattr(Student, 'user') else None,
        first_name   = form_data.get('first_name', ''),
        last_name    = form_data.get('last_name', ''),
        phone        = phone,
        parent_phone = form_data.get('parent_phone', '') or '',
        email        = form_data.get('email', '') or '',
        gender       = form_data.get('gender', '') or '',
        birth_date   = form_data.get('birth_date') or None,
        address      = form_data.get('address', '') or '',
        is_active    = True,
    )
    return student, True


# ─── Enrollment list ─────────────────────────────────────────────────────────

def enrollment_list(request):
    qs = Enrollment.objects.select_related(
        'student', 'student__user', 'course', 'course__teacher', 'group', 'instructor'
    )

    # ── Qidiruv ──────────────────────────────────────────────────────────────
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q)  |
            Q(student__phone__icontains=q)       |
            Q(course__title__icontains=q)
        )

    # ── Status filter ────────────────────────────────────────────────────────
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    # ── To'lov filter ────────────────────────────────────────────────────────
    pay_filter = request.GET.get('pay', 'all')
    if pay_filter != 'all':
        qs = qs.filter(payment_status=pay_filter)

    # ── Statistika ────────────────────────────────────────────────────────────
    all_qs       = Enrollment.objects.all()
    total_count  = all_qs.count()
    active_count = all_qs.filter(status='active').count()
    pending_count= all_qs.filter(status='pending').count()
    paid_count   = all_qs.filter(payment_status='paid').count()
    total_income = all_qs.aggregate(s=Sum('paid_amount'))['s'] or 0
    total_debt   = sum(
        max(e.net_fee - e.paid_amount, 0)
        for e in all_qs.only('course_fee', 'discount', 'paid_amount')
    )

    # ── Kurs va guruh tanlovi uchun querysetlar ───────────────────────────────
    try:
        from courses.models import Course, Group
        courses = list(Course.objects.filter(is_active=True))
        groups  = list(Group.objects.filter(is_active=True))
    except Exception:
        courses = []
        groups  = []

    try:
        from instructors.models import Instructor
        instructors = list(Instructor.objects.filter(is_active=True).select_related('user'))
    except Exception:
        instructors = []

    # ── Paginatsiya — har bir qator uchun modal renderlanadi, shuning uchun shart ──
    paginator = Paginator(qs, ENROLLMENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'enrollments':   page_obj,
        'page_obj':      page_obj,
        'search_query':  q,
        'status_filter': status_filter,
        'pay_filter':    pay_filter,
        'total_count':   total_count,
        'active_count':  active_count,
        'pending_count': pending_count,
        'paid_count':    paid_count,
        'total_income':  total_income,
        'total_debt':    total_debt,
        'courses':       courses,
        'groups':        groups,
        'instructors':   instructors,
        'status_choices': Enrollment.STATUS_CHOICES,
        'pay_choices':    Enrollment.PAYMENT_STATUS_CHOICES,
        'source_choices': Enrollment.SOURCE_CHOICES,
    }
    return render(request, 'enrollments_list.html', context)


# ─── Enrollment create ────────────────────────────────────────────────────────

def enrollment_create(request):
    if request.method != 'POST':
        return redirect('enrollments:enrollment_list')

    data = request.POST

    # 1. Talabani topish yoki yaratish
    try:
        student, created = _get_or_create_student(data)
    except Exception as exc:
        messages.error(request, f"Talaba yaratishda xatolik: {exc}")
        return redirect('enrollments:enrollment_list')

    # 2. Enrollment yaratish
    try:
        from courses.models import Course, Group
        course = Course.objects.filter(pk=data.get('course')).first()
        group  = Group.objects.filter(pk=data.get('group')).first()
    except Exception:
        course = group = None

    try:
        from instructors.models import Instructor
        instructor = Instructor.objects.filter(pk=data.get('instructor')).first()
    except Exception:
        instructor = None

    # Telegram lead orqali kelgan bo'lsa, manbani belgilaymiz
    lead_id = data.get('lead_id')
    source_val = data.get('source', 'walk_in')
    if lead_id:
        source_val = 'social'  # Telegram → ijtimoiy tarmoq

    enrollment = Enrollment.objects.create(
        student        = student,
        course         = course,
        group          = group,
        instructor     = instructor,
        status         = data.get('status', 'pending'),
        payment_status = data.get('payment_status', 'unpaid'),
        course_fee     = data.get('course_fee') or 0,
        discount       = data.get('discount') or 0,
        paid_amount    = data.get('paid_amount') or 0,
        start_date     = data.get('start_date') or None,
        end_date       = data.get('end_date') or None,
        source         = source_val,
        notes          = data.get('notes', ''),
        created_by     = request.user if request.user.is_authenticated else None,
    )

    # Telegram arizasini "ro'yxatga olingan" deb belgilaymiz
    if lead_id:
        try:
            from .models import TelegramLead
            lead = TelegramLead.objects.filter(pk=lead_id).first()
            if lead:
                lead.status       = 'processed'
                lead.enrollment   = enrollment
                lead.processed_by = request.user if request.user.is_authenticated else None
                lead.save(update_fields=['status', 'enrollment', 'processed_by', 'updated_at'])
        except Exception:
            pass

    if created:
        messages.success(
            request,
            f"✅ Talaba '{student.full_name}' ro'yxatga olindi va tizimga qo'shildi! "
            f"Login: {student.user.username if hasattr(student, 'user') and student.user else '—'}"
        )
    else:
        messages.success(
            request,
            f"✅ Mavjud talaba '{student.full_name}' kursga yozildi."
        )

    return redirect('enrollments:enrollment_list')


# ─── Enrollment update ────────────────────────────────────────────────────────

def enrollment_update(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)

    if request.method != 'POST':
        return redirect('enrollments:enrollment_list')

    data = request.POST

    try:
        from courses.models import Course, Group
        course = Course.objects.filter(pk=data.get('course')).first()
        group  = Group.objects.filter(pk=data.get('group')).first()
    except Exception:
        course = group = None

    try:
        from instructors.models import Instructor
        instructor = Instructor.objects.filter(pk=data.get('instructor')).first()
    except Exception:
        instructor = None

    enrollment.course         = course
    enrollment.group          = group
    enrollment.instructor     = instructor
    enrollment.status         = data.get('status', enrollment.status)
    enrollment.payment_status = data.get('payment_status', enrollment.payment_status)
    enrollment.course_fee     = data.get('course_fee') or enrollment.course_fee
    enrollment.discount       = data.get('discount') or enrollment.discount
    enrollment.paid_amount    = data.get('paid_amount') or enrollment.paid_amount
    enrollment.start_date     = data.get('start_date') or None
    enrollment.end_date       = data.get('end_date') or None
    enrollment.source         = data.get('source', enrollment.source)
    enrollment.notes          = data.get('notes', enrollment.notes)
    enrollment.save()

    messages.success(request, f"✅ Enrollment #{enrollment.pk} yangilandi.")
    return redirect('enrollments:enrollment_list')


# ─── Enrollment delete ────────────────────────────────────────────────────────

@require_POST
def enrollment_delete(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    name = str(enrollment)
    enrollment.delete()
    messages.success(request, f"🗑️ '{name}' o'chirildi.")
    return redirect('enrollments:enrollment_list')


# ─── Status toggle ────────────────────────────────────────────────────────────

@require_POST
def enrollment_toggle_status(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    cycle = {
        'pending':   'active',
        'active':    'frozen',
        'frozen':    'active',
        'completed': 'active',
        'cancelled': 'active',
    }
    enrollment.status = cycle.get(enrollment.status, 'active')
    enrollment.save(update_fields=['status'])
    messages.success(request, f"Holat yangilandi: {enrollment.get_status_display()}")
    return redirect('enrollments:enrollment_list')


# ─── Detail / note add ────────────────────────────────────────────────────────

@require_POST
def enrollment_add_note(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    text = request.POST.get('text', '').strip()
    if text:
        EnrollmentNote.objects.create(
            enrollment=enrollment,
            author=request.user if request.user.is_authenticated else None,
            text=text,
        )
        messages.success(request, "Izoh qo'shildi.")
    return redirect('enrollments:enrollment_list')


    enrollment = get_object_or_404(
        Enrollment.objects.select_related(
            'student', 'course', 'group', 'instructor', 'created_by'
        ).prefetch_related('history_notes__author'),
        pk=pk
    )

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            EnrollmentNote.objects.create(
                enrollment = enrollment,
                author     = request.user if request.user.is_authenticated else None,
                text       = text,
            )
            messages.success(request, "Izoh qo'shildi.")
        return redirect('enrollments:enrollment_detail', pk=pk)

    context = {'enrollment': enrollment}
    return render(request, 'enrollments/enrollment_detail.html', context)