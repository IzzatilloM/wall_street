from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Student

User = get_user_model()

STUDENTS_PER_PAGE = 20


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def admin_required(request):
    return request.user.is_authenticated and request.user.role == 'admin'


def safe_ordering(sort_value: str) -> str:
    allowed = {
        'created_at', '-created_at',
        'first_name', '-first_name',
        'last_name',  '-last_name',
        'phone',      '-phone',
        'email',      '-email',
    }
    return sort_value if sort_value in allowed else '-created_at'


# ══════════════════════════════════════════════════════════════
#  AI CHURN PREDICTION  (Claude API)
# ══════════════════════════════════════════════════════════════

def _collect_churn_data(student):
    """Claude uchun talaba haqidagi statistikani yig'adi."""
    from attendance.models import Attendance

    today = timezone.now().date()
    last_30 = today - timedelta(days=30)

    # ── Oxirgi 30 kundagi davomat ─────────────────────────────
    att_qs = Attendance.objects.filter(date__gte=last_30)
    if student.user:
        att_qs = att_qs.filter(student__user=student.user)
    else:
        att_qs = att_qs.none()

    att_total   = att_qs.count()
    att_present = att_qs.filter(Q(status='present') | Q(status='late')).count()
    att_late    = att_qs.filter(status='late').count()
    att_percent = round(att_present / att_total * 100, 1) if att_total else None

    # ── To'lov kechikishi ─────────────────────────────────────
    from payments.models import Payment

    last_payment = (
        Payment.objects.filter(student=student)
        .exclude(status='cancelled')
        .order_by('-paid_at')
        .first()
    )
    days_since_payment = (
        (timezone.now() - last_payment.paid_at).days if last_payment else None
    )

    enrollments = list(
        student.enrollments.select_related('course').all()
    )
    overdue_count = sum(
        1 for e in enrollments
        if e.payment_status in ('overdue', 'unpaid') and e.remaining_amount > 0
    )
    total_debt = sum(
        float(e.remaining_amount) for e in enrollments
        if e.status in ('active', 'pending')
    )

    # ── Enrollment faolligi ───────────────────────────────────
    active_count    = sum(1 for e in enrollments if e.status == 'active')
    completed_count = sum(1 for e in enrollments if e.status == 'completed')
    cancelled_count = sum(1 for e in enrollments if e.status == 'cancelled')
    frozen_count    = sum(1 for e in enrollments if e.status == 'frozen')

    last_enrolled = max((e.enrolled_at for e in enrollments), default=None)
    days_since_enroll = (
        (timezone.now() - last_enrolled).days if last_enrolled else None
    )

    return {
        'davomat_30_kun': {
            'jami_darslar':   att_total,
            'kelgan':         att_present,
            'kechikkan':      att_late,
            'davomat_foizi':  att_percent,
        },
        'tolovlar': {
            'oxirgi_tolovdan_otgan_kunlar': days_since_payment,
            'muddati_otgan_enrollmentlar':  overdue_count,
            'umumiy_qarz_summa':            total_debt,
        },
        'enrollmentlar': {
            'faol':           active_count,
            'tugatilgan':     completed_count,
            'bekor_qilingan': cancelled_count,
            'muzlatilgan':    frozen_count,
            'oxirgi_yozilganidan_otgan_kunlar': days_since_enroll,
        },
        'talaba_faolmi': student.is_active,
    }


def _fallback_churn_score(data):
    """
    AI ishlamaganda (kredit/kalit yo'q) qoidaviy lokal churn bahosi.
    Xuddi shu statistikadan formula bilan 0-100 score hisoblaydi.
    """
    dav = data['davomat_30_kun']
    tol = data['tolovlar']
    enr = data['enrollmentlar']

    score = 0.0
    sabablar = []

    att = dav['davomat_foizi']
    if att is None:
        score += 25
        sabablar.append("oxirgi 30 kunda davomat ma'lumoti yo'q")
    else:
        score += (100 - att) * 0.4
        if att < 60:
            sabablar.append(f"davomat past ({att}%)")

    days = tol['oxirgi_tolovdan_otgan_kunlar']
    if days is None:
        score += 15
        sabablar.append("to'lov tarixi topilmadi")
    elif days > 60:
        score += 20
        sabablar.append(f"oxirgi to'lovdan {days} kun o'tgan")
    elif days > 30:
        score += 10

    if tol['muddati_otgan_enrollmentlar']:
        score += 15
        sabablar.append("muddati o'tgan to'lov bor")
    if tol['umumiy_qarz_summa'] > 0:
        score += 5

    if enr['faol'] == 0:
        score += 25
        sabablar.append("faol kurs yozilishi yo'q")
    if enr['bekor_qilingan'] > enr['tugatilgan']:
        score += 10
        sabablar.append("bekor qilingan kurslari ko'p")

    score = max(0.0, min(100.0, round(score, 1)))
    if not sabablar:
        sabablar.append("asosiy ko'rsatkichlar me'yorda")

    reason = "Lokal tahlil: " + ", ".join(sabablar) + "."
    return score, reason


def _send_churn_alert(student, score, reason):
    """
    Risk yuqori bo'lganda avtomatik ogohlantirish yuboradi.
    Kanallar: email (talaba va admin) + Telegram (agar chat_id mavjud bo'lsa).
    """
    from accounts.telegram_utils import send_telegram_message

    sent_channels = []

    subject = f"⚠️ Wall Street CRM — {student.full_name} uchun yuqori churn riski ({score:.0f}/100)"
    body = (
        f"Talaba: {student.full_name}\n"
        f"Telefon: {student.phone}\n"
        f"AI churn risk: {score:.0f}/100\n\n"
        f"Sabab (AI tahlili):\n{reason}\n\n"
        f"Iltimos, talaba bilan bog'lanib holatni aniqlashtiring.\n"
        f"— Wall Street CRM (AI monitoring)"
    )

    # Email — talabaning o'ziga va adminga
    recipients = []
    if student.email:
        recipients.append(student.email)
    admin_email = getattr(settings, 'DEVELOPER_EMAIL', '')
    if admin_email:
        recipients.append(admin_email)

    if recipients:
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )
            sent_channels.append('email')
        except Exception:
            pass

    # Telegram — talabaning bog'langan chat_id siga
    chat_id = getattr(student.user, 'telegram_chat_id', '') if student.user else ''
    if chat_id:
        tg_text = (
            "⚠️ Wall Street CRM\n\n"
            f"Hurmatli {student.full_name}, so'nggi davomat va to'lov "
            "ko'rsatkichlaringiz pasaygani aniqlandi.\n\n"
            "O'qishni davom ettirishda muammo bo'lsa, administratsiya "
            "bilan bog'laning — yordam beramiz! 📞"
        )
        success, _ = send_telegram_message(chat_id, tg_text)
        if success:
            sent_channels.append('telegram')

    return sent_channels


def calculate_churn_risk(student_id, user=None):
    """
    Talabaning churn (o'qishni tashlab ketish) riskini Claude API orqali
    hisoblaydi va natijani Student modeliga saqlaydi.

    Returns:
        dict: {'success': bool, 'score': float, 'reason': str,
               'alert_sent': list, 'error': str}
    """
    from ai.services import ask_claude, extract_json

    student = get_object_or_404(Student, pk=student_id)
    data = _collect_churn_data(student)

    system_prompt = (
        "Siz ta'lim markazi CRM tizimining tahlilchi yordamchisisiz. "
        "Sizga talabaning davomati, to'lovlari va kurs yozilishlari "
        "haqida statistika beriladi. Talabaning o'qishni tashlab ketish "
        "(churn) ehtimolini 0 dan 100 gacha baholang: 0 — hech qanday "
        "xavf yo'q, 100 — deyarli aniq tashlab ketadi.\n\n"
        "Qoidalar:\n"
        "- Davomat past yoki darslar umuman yo'q bo'lsa — risk oshadi\n"
        "- To'lov uzoq vaqt qilinmagan yoki qarz katta bo'lsa — risk oshadi\n"
        "- Faol enrollment yo'q yoki bekor qilinganlar ko'p bo'lsa — risk oshadi\n"
        "- Ma'lumot yetarli bo'lmasa, buni sababda ayting va o'rtacha baho bering\n\n"
        "Javobni FAQAT quyidagi JSON formatda qaytaring, boshqa matn yozmang:\n"
        '{"score": <0-100 oraliqdagi son>, "sabab": "<o\'zbek tilida 2-3 jumlali qisqa izoh>"}'
    )

    import json as _json
    user_prompt = (
        f"Talaba: {student.full_name}\n"
        f"Statistika (JSON):\n{_json.dumps(data, ensure_ascii=False, indent=2)}"
    )

    success, text = ask_claude(
        feature='churn',
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        related_object=f"student:{student.pk}",
        max_tokens=512,
        user=user,
    )

    # AI javobini o'qishga harakat qilamiz; bo'lmasa lokal formula ishlaydi
    offline = False
    score = None
    reason = ''

    if success:
        parsed = extract_json(text)
        if parsed and 'score' in parsed:
            try:
                score = max(0.0, min(100.0, float(parsed['score'])))
                reason = str(parsed.get('sabab', '')).strip()
            except (TypeError, ValueError):
                score = None

    if score is None:
        # AI ishlamadi (kredit/kalit yo'q yoki javob buzilgan) — lokal tahlil
        offline = True
        score, reason = _fallback_churn_score(data)

    student.churn_risk_score      = score
    student.churn_risk_reason     = reason
    student.churn_risk_updated_at = timezone.now()
    student.save(update_fields=[
        'churn_risk_score', 'churn_risk_reason', 'churn_risk_updated_at',
    ])

    # Risk chegaradan oshsa — avtomatik ogohlantirish
    alert_sent = []
    threshold = getattr(settings, 'AI_CHURN_ALERT_THRESHOLD', 70)
    if score > threshold:
        alert_sent = _send_churn_alert(student, score, reason)

    return {
        'success':    True,
        'score':      score,
        'reason':     reason,
        'level':      student.churn_risk_level,
        'alert_sent': alert_sent,
        'offline':    offline,
    }


@login_required
@require_POST
def student_churn_risk(request, pk):
    """AJAX: bitta talaba uchun churn riskini hisoblash."""
    if not admin_required(request):
        return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q!'}, status=403)

    # Xatolik ham 200 qaytadi (success flag JSON ichida) — aks holda har bir
    # sozlanmagan kalit developer'ga error-email yuborib tashlaydi.
    result = calculate_churn_risk(pk, user=request.user)
    return JsonResponse(result)


# ══════════════════════════════════════════════════════════════
#  STUDENT PANEL (student o'zi kiradi)
# ══════════════════════════════════════════════════════════════

@login_required
def student_panel(request):
    if request.user.role != 'student':
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)

    # Talabaning barcha enrollmentlari
    enrollments = student.enrollments.select_related(
        'course', 'group', 'instructor'
    ).order_by('-enrolled_at')

    return render(request, 'student_list.html', {
        'student':     student,
        'enrollments': enrollments,
    })


# ══════════════════════════════════════════════════════════════
#  LIST
# ══════════════════════════════════════════════════════════════

@login_required
def student_list(request):
    if not admin_required(request):
        return redirect('dashboard')

    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all').strip()
    sort   = safe_ordering(request.GET.get('sort', '-created_at'))

    # enrolled_courses_count → enrollment modeli orqali hisoblanadi
    # select_related('user') — har bir qatordagi N+1 so'rovlarni kamaytiradi
    students_qs = Student.objects.select_related('user').annotate(
        enrolled_courses_count=Count('enrollments', distinct=True)
    )

    if q:
        students_qs = students_qs.filter(
            Q(first_name__icontains=q)   |
            Q(last_name__icontains=q)    |
            Q(phone__icontains=q)        |
            Q(parent_phone__icontains=q) |
            Q(email__icontains=q)
        )

    if status == 'active':
        students_qs = students_qs.filter(is_active=True)
    elif status == 'inactive':
        students_qs = students_qs.filter(is_active=False)

    students_qs = students_qs.order_by(sort)

    # ── Paginatsiya ──
    paginator = Paginator(students_qs, STUDENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'students':       page_obj,   # template {% for student in students %} — page obyekti iteratsiyalanadi
        'page_obj':       page_obj,
        'paginator':      paginator,
        'search_query':   q,
        'status_filter':  status,
        'sort':           sort,
        'total_count':    Student.objects.count(),
        'active_count':   Student.objects.filter(is_active=True).count(),
        'inactive_count': Student.objects.filter(is_active=False).count(),
    }

    return render(request, 'student_list.html', context)



@login_required
def student_create(request):

    messages.info(
        request,
        "ℹ️ Yangi talaba qo'shish uchun Enrollments sahifasidan foydalaning."
    )
    return redirect('enrollments:enrollment_list')


# ══════════════════════════════════════════════════════════════
#  UPDATE
# ══════════════════════════════════════════════════════════════

@login_required
def student_update(request, pk):
    if not admin_required(request):
        return redirect('dashboard')

    student = get_object_or_404(Student, pk=pk)

    if request.method != 'POST':
        return redirect('student:student_list')

    first_name   = request.POST.get('first_name',   '').strip()
    last_name    = request.POST.get('last_name',    '').strip()
    phone        = request.POST.get('phone',         '').strip()
    parent_phone = request.POST.get('parent_phone', '').strip()
    email        = request.POST.get('email',         '').strip().lower()
    gender       = request.POST.get('gender',        '').strip() or None
    birth_date   = request.POST.get('birth_date')    or None
    address      = request.POST.get('address',       '').strip()
    image        = request.FILES.get('image')
    is_active    = request.POST.get('is_active') in ['on', 'true', '1', 'yes']

    # ── Validatsiya ──────────────────────────────────────────
    errors = []

    if not first_name:
        errors.append("Ism kiritilmadi.")
    if not last_name:
        errors.append("Familiya kiritilmadi.")
    if not phone:
        errors.append("Telefon kiritilmadi.")

    if phone and Student.objects.filter(phone=phone).exclude(pk=student.pk).exists():
        errors.append("Bu telefon boshqa studentda mavjud.")
    if email and Student.objects.filter(email=email).exclude(pk=student.pk).exists():
        errors.append("Bu email boshqa studentda mavjud.")

    if errors:
        for e in errors:
            messages.error(request, e)
        return redirect('student:student_list')

    # ── Student yangilash ─────────────────────────────────────
    student.first_name   = first_name
    student.last_name    = last_name
    student.phone        = phone
    student.parent_phone = parent_phone or None
    student.email        = email        or None
    student.gender       = gender
    student.birth_date   = birth_date
    student.address      = address      or None
    student.is_active    = is_active

    if image:
        student.image = image

    student.save()

    # ── User ma'lumotlarini ham sinxronlashtirish ─────────────
    if student.user:
        student.user.first_name = first_name
        student.user.last_name  = last_name
        student.user.email      = email or ''
        # phone maydoni User modelida bo'lsa
        if hasattr(student.user, 'phone'):
            student.user.phone = phone
        student.user.is_active = is_active
        student.user.save()

    messages.success(request, f"✅ {student.full_name} ma'lumotlari yangilandi.")
    return redirect('student:student_list')


# ══════════════════════════════════════════════════════════════
#  DELETE
# ══════════════════════════════════════════════════════════════

@login_required
@require_POST
def student_delete(request, pk):
    if not admin_required(request):
        return redirect('dashboard')

    student = get_object_or_404(Student, pk=pk)
    name = student.full_name

    # User o'chirilsa cascade bilan Student ham o'chadi (OneToOne)
    if student.user:
        student.user.delete()
    else:
        student.delete()

    messages.success(request, f"🗑️ {name} tizimdan o'chirildi.")
    return redirect('student:student_list')


# ══════════════════════════════════════════════════════════════
#  TOGGLE STATUS
# ══════════════════════════════════════════════════════════════

@login_required
@require_POST
def student_toggle_status(request, pk):
    if not admin_required(request):
        return redirect('dashboard')

    student = get_object_or_404(Student, pk=pk)
    student.is_active = not student.is_active
    student.save(update_fields=['is_active'])

    # User bilan sinxronlashtirish
    if student.user:
        student.user.is_active = student.is_active
        student.user.save(update_fields=['is_active'])

    status_text = "faollashtirildi ✅" if student.is_active else "nofaol qilindi ⛔"
    messages.success(request, f"{student.full_name} {status_text}.")
    return redirect('student:student_list')


# ══════════════════════════════════════════════════════════════
#  AJAX SEARCH  (enrollment formida talaba qidirish uchun)
# ══════════════════════════════════════════════════════════════

@login_required
def student_search_ajax(request):
    """
    Enrollment formi ichida mavjud talabalarni qidirish.
    ?q=... → JSON qaytaradi
    """
    if not admin_required(request):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})

    students = Student.objects.annotate(
        enrolled_courses_count=Count('enrollments', distinct=True)
    ).filter(
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q)  |
        Q(phone__icontains=q)      |
        Q(email__icontains=q)
    ).select_related('user')[:10]

    data = [
        {
            'id':                     s.pk,
            'full_name':              s.full_name,
            'phone':                  s.phone,
            'email':                  s.email or '',
            'is_active':              s.is_active,
            'enrolled_courses_count': s.enrolled_courses_count,
            'username':               s.user.username if s.user else '',
        }
        for s in students
    ]

    return JsonResponse({'results': data})


# ══════════════════════════════════════════════════════════════
#  STUDENT DETAIL  (redirect — detail modal list da ochiladi)
# ══════════════════════════════════════════════════════════════

@login_required
def student_detail(request, pk):
    if not admin_required(request):
        return redirect('dashboard')
    return redirect('student:student_list')