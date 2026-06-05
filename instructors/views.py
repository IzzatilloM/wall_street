from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Instructor

# Agar custom User model ishlatayotgan bo'lsangiz:
from django.contrib.auth import get_user_model
User = get_user_model()

MAX_ADMINS        = 2
TEACHERS_PER_PAGE = 15


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