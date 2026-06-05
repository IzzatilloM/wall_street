import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST

ENROLLMENTS_PER_PAGE = 25

from .models import Enrollment, EnrollmentNote
from .forms import EnrollmentForm, EnrollmentUpdateForm, EnrollmentNoteForm

User = get_user_model()


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