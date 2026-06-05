from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
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
    return redirect('enrollments:enrollments_list')


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