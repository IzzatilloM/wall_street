import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Instructor

# Agar custom User model ishlatayotgan bo'lsangiz:
from django.contrib.auth import get_user_model
User = get_user_model()

MAX_ADMINS        = 2
TEACHERS_PER_PAGE = 15


# ─────────────────────────────────────────────
#  AI INSTRUCTOR PERFORMANCE ANALYTICS (Claude)
# ─────────────────────────────────────────────

def _collect_instructor_stats(instructor):
    """O'qituvchi kurslari bo'yicha retention va davomat statistikasi."""
    from enrollments.models import Enrollment
    from attendance.models import Attendance

    # ── Retention (enrollmentlar bo'yicha) ──
    enr_qs = Enrollment.objects.filter(
        Q(instructor=instructor) |
        Q(course__teacher=instructor) |
        Q(group__teacher=instructor)
    ).distinct()

    total     = enr_qs.count()
    active    = enr_qs.filter(status='active').count()
    completed = enr_qs.filter(status='completed').count()
    cancelled = enr_qs.filter(status='cancelled').count()
    frozen    = enr_qs.filter(status='frozen').count()

    retention_rate = (
        round((active + completed) / total * 100, 1) if total else None
    )

    # ── Davomat (attendance kurslari instructor useriga bog'langan) ──
    att_qs = Attendance.objects.filter(course__instructor=instructor.user)
    att_total   = att_qs.count()
    att_present = att_qs.filter(Q(status='present') | Q(status='late')).count()
    att_late    = att_qs.filter(status='late').count()
    att_percent = round(att_present / att_total * 100, 1) if att_total else None

    # ── Kurslar ──
    courses = list(
        instructor.courses.values_list('title', flat=True)[:10]
    )

    return {
        'oqituvchi': {
            'ism':           instructor.full_name,
            'mutaxassislik': instructor.specialty or "ko'rsatilmagan",
            'tajriba_yil':   instructor.experience_years,
            'kurslari':      courses,
        },
        'retention': {
            'jami_enrollment':  total,
            'faol':             active,
            'tugatgan':         completed,
            'bekor_qilgan':     cancelled,
            'muzlatilgan':      frozen,
            'retention_foizi':  retention_rate,
        },
        'davomat': {
            'jami_yozuvlar':  att_total,
            'kelganlar':      att_present,
            'kechikkanlar':   att_late,
            'davomat_foizi':  att_percent,
        },
    }


def _fallback_instructor_report(stats):
    """AI ishlamaganda statistikadan tayyor o'zbekcha hisobot tuzadi."""
    o = stats['oqituvchi']
    r = stats['retention']
    d = stats['davomat']

    jumlalar = [
        f"{o['ism']} ({o['mutaxassislik']}, {o['tajriba_yil']} yil tajriba) "
        f"bo'yicha statistik hisobot."
    ]

    if r['jami_enrollment']:
        jumlalar.append(
            f"Jami {r['jami_enrollment']} ta yozilishdan {r['faol']} tasi faol, "
            f"{r['tugatgan']} tasi kursni tugatgan — retention {r['retention_foizi']}%."
        )
        if r['retention_foizi'] >= 80:
            jumlalar.append("Talabalarni ushlab qolish darajasi juda yaxshi.")
        elif r['retention_foizi'] >= 60:
            jumlalar.append(
                "Retention o'rtacha — bekor qilishlar sababini o'rganish foydali bo'ladi."
            )
        else:
            jumlalar.append(
                "Retention past — talabalar bilan individual ishlash tavsiya etiladi."
            )
    else:
        jumlalar.append("Hozircha enrollment ma'lumotlari mavjud emas.")

    if d['jami_yozuvlar']:
        jumlalar.append(
            f"Davomat ko'rsatkichi {d['davomat_foizi']}% "
            f"({d['jami_yozuvlar']} ta yozuv asosida)."
        )
    else:
        jumlalar.append("Davomat yozuvlari hali kiritilmagan.")

    return " ".join(jumlalar)


def get_instructor_ai_report(instructor_id, user=None):
    """
    O'qituvchining samaradorlik hisobotini Claude API orqali oladi
    (o'zbek tilida 3-5 jumla).

    Returns:
        dict: {'success': bool, 'report': str, 'stats': dict, 'error': str}
    """
    from ai.services import ask_claude

    instructor = get_object_or_404(Instructor, pk=instructor_id)
    stats = _collect_instructor_stats(instructor)

    system_prompt = (
        "Siz ta'lim markazi CRM tizimining tahlilchi yordamchisisiz. "
        "Sizga o'qituvchining kurslari, talabalar retention darajasi va "
        "davomat statistikasi beriladi. Shu ma'lumotlar asosida o'qituvchi "
        "samaradorligi haqida O'ZBEK TILIDA aniq 3-5 jumlali hisobot yozing.\n\n"
        "Qoidalar:\n"
        "- Faqat berilgan raqamlarga tayaning, o'ylab topmang\n"
        "- Kuchli tomonini va yaxshilash kerak bo'lgan jihatni ayting\n"
        "- Ma'lumot kam bo'lsa, buni ochiq ayting\n"
        "- Hisobot rasmiy lekin tushunarli tilda bo'lsin\n"
        "- Faqat hisobot matnini qaytaring, sarlavha yoki JSON kerak emas"
    )

    user_prompt = (
        f"O'qituvchi statistikasi (JSON):\n"
        f"{json.dumps(stats, ensure_ascii=False, indent=2)}"
    )

    success, text = ask_claude(
        feature='instructor_report',
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        related_object=f"instructor:{instructor.pk}",
        max_tokens=600,
        user=user,
    )

    offline = False
    if not success:
        # AI ishlamadi (kredit/kalit yo'q) — statistikadan lokal hisobot
        offline = True
        text = _fallback_instructor_report(stats)

    return {
        'success': True,
        'report':  text,
        'instructor_name': instructor.full_name,
        'stats':   stats,
        'offline': offline,
    }


@login_required
@require_POST
def instructor_ai_report(request, pk):
    """AJAX: o'qituvchi uchun AI samaradorlik hisoboti."""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': "Ruxsat yo'q!"}, status=403)

    result = get_instructor_ai_report(pk, user=request.user)
    return JsonResponse(result)


# ─────────────────────────────────────────────
#  LIST
# ─────────────────────────────────────────────
@login_required
def instructor_list(request):
    admin_list = (
        Instructor.objects
        .filter(user__role='admin')
        .select_related('user')
        .order_by('-created_at')
    )

    teacher_qs = (
        Instructor.objects
        .filter(user__role='teacher')
        .select_related('user')
        .order_by('-created_at')
    )
    paginator    = Paginator(teacher_qs, TEACHERS_PER_PAGE)
    page_number  = request.GET.get('page', 1)
    teacher_page = paginator.get_page(page_number)

    admin_count   = admin_list.count()
    teacher_count = teacher_qs.count()
    active_count  = Instructor.objects.filter(is_active=True).count()
    total_count   = admin_count + teacher_count

    context = {
        'admin_list':    admin_list,
        'teacher_page':  teacher_page,

        'admin_count':   admin_count,
        'teacher_count': teacher_count,
        'active_count':  active_count,
        'total_count':   total_count,

        'max_admins':    MAX_ADMINS,
        'can_add_admin': admin_count < MAX_ADMINS,   # ← template uchun kerak
    }
    return render(request, 'instructors_list.html', context)


# ─────────────────────────────────────────────
#  CREATE  (yangi qo'shildi)
# ─────────────────────────────────────────────
@login_required
def instructor_create(request):
    if request.method != 'POST':
        return redirect('instructors:instructor_list')

    # --- form ma'lumotlari ---
    username         = request.POST.get('username', '').strip()
    password         = request.POST.get('password', '').strip()
    email            = request.POST.get('email', '').strip()
    phone            = request.POST.get('phone', '').strip()
    role             = request.POST.get('role', 'teacher')   # 'teacher' | 'admin'
    full_name        = request.POST.get('full_name', '').strip()
    specialty        = request.POST.get('specialty', '').strip()
    experience_years = request.POST.get('experience_years') or 0
    salary           = request.POST.get('salary') or 0
    address          = request.POST.get('address', '').strip()
    bio              = request.POST.get('bio', '').strip()
    is_active        = request.POST.get('is_active') == 'on'

    # --- validatsiya ---
    if not username or not password or not full_name:
        messages.error(request, "Username, parol va to'liq ism majburiy maydonlar.")
        return redirect('instructors:instructor_list')

    if User.objects.filter(username=username).exists():
        messages.error(request, f"«{username}» username allaqachon mavjud.")
        return redirect('instructors:instructor_list')

    # Admin limit tekshiruvi
    if role == 'admin':
        current_admin_count = Instructor.objects.filter(user__role='admin').count()
        if current_admin_count >= MAX_ADMINS:
            messages.error(
                request,
                f"Admin limiti to'ldi ({MAX_ADMINS}/{MAX_ADMINS}). "
                "Yangi admin qo'shish uchun avval bitta adminni o'chiring."
            )
            return redirect('instructors:instructor_list')

    try:
        # User yaratish
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        # role / phone / verified — barchasi CustomUser da saqlanadi
        user.role = role
        user.phone = phone
        if hasattr(user, 'is_verified'):
            user.is_verified = True
        # Ochiq parol nusxasi (sozlamalarda ko'rinishi uchun)
        if hasattr(user, 'plain_password'):
            user.plain_password = password
        user.save()  # ← post_save signali Instructor profilini avtomatik yaratadi

        # Signal yaratgan profilni topib, qo'shimcha maydonlarni to'ldiramiz
        instructor, _ = Instructor.objects.get_or_create(
            user=user,
            defaults={'full_name': full_name},
        )
        instructor.full_name        = full_name
        instructor.specialty        = specialty
        instructor.experience_years = int(experience_years)
        instructor.salary           = float(salary)
        instructor.address          = address
        instructor.bio              = bio
        instructor.is_active        = is_active
        instructor.save()

        role_label = "Admin" if role == 'admin' else "Teacher"
        messages.success(request, f"{role_label} «{full_name}» muvaffaqiyatli qo'shildi.")

    except Exception as e:
        messages.error(request, f"Xatolik yuz berdi: {e}")

    return redirect('instructors:instructor_list')


# ─────────────────────────────────────────────
#  UPDATE
# ─────────────────────────────────────────────
@login_required
def instructor_update(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)

    if request.method != 'POST':
        return redirect('instructors:instructor_list')

    full_name        = request.POST.get('full_name', '').strip()
    specialty        = request.POST.get('specialty', '').strip()
    experience_years = request.POST.get('experience_years') or 0
    salary           = request.POST.get('salary') or 0
    address          = request.POST.get('address', '').strip()
    bio              = request.POST.get('bio', '').strip()
    is_active        = request.POST.get('is_active') == 'on'

    if not full_name:
        messages.error(request, "To'liq ism bo'sh bo'lishi mumkin emas.")
        return redirect('instructors:instructor_list')

    try:
        instructor.full_name        = full_name
        instructor.specialty        = specialty
        instructor.experience_years = int(experience_years)
        instructor.salary           = float(salary)
        instructor.address          = address
        instructor.bio              = bio
        instructor.is_active        = is_active
        instructor.save()

        messages.success(request, f"«{full_name}» ma'lumotlari yangilandi.")

    except Exception as e:
        messages.error(request, f"Yangilashda xatolik: {e}")

    return redirect('instructors:instructor_list')


# ─────────────────────────────────────────────
#  DELETE
# ─────────────────────────────────────────────
@login_required
def instructor_delete(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)

    if request.method != 'POST':
        return redirect('instructors:instructor_list')

    try:
        name = instructor.full_name
        user = instructor.user
        instructor.delete()
        user.delete()

        messages.success(request, f"«{name}» tizimdan o'chirildi.")

    except Exception as e:
        messages.error(request, f"O'chirishda xatolik: {e}")

    return redirect('instructors:instructor_list')