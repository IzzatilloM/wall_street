from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, StudentMoveForm
from .models import Course, Student
from instructors.models import Instructor


def _apply_schedule(request, course):
    """POST'dan dars jadvalini (kunlar + vaqt) o'qib, kursga saqlaydi."""
    valid = {d for d, _ in Course.WEEKDAY_CHOICES}
    days = [d for d in request.POST.getlist('weekdays') if d in valid]
    course.weekdays = ','.join(days)
    course.start_time = request.POST.get('start_time') or None
    course.end_time = request.POST.get('end_time') or None
    course.save(update_fields=['weekdays', 'start_time', 'end_time'])


@login_required
def course_list(request):
    courses = (
        Course.objects.select_related('teacher')
        .prefetch_related('students')
        .annotate(student_count=Count('students'))
        .order_by('category', 'title')
    )

    # Search va filter
    q = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()

    if q:
        courses = courses.filter(title__icontains=q)
    if level:
        courses = courses.filter(level=level)

    total_courses = courses.count()
    english_courses = courses.filter(category='english').count()
    it_courses = courses.filter(category='it').count()
    total_students = Student.objects.count()
    teachers = Instructor.objects.filter(is_active=True)
    total_teachers = teachers.count()
    active_courses_count = courses.filter(is_active=True).count()

    form = CourseForm()

    context = {
        'courses': courses,
        'form': form,
        'teachers': teachers,           # ✅
        'total_courses': total_courses,
        'english_courses': english_courses,
        'it_courses': it_courses,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'active_courses_count': active_courses_count,
    }
    return render(request, 'course_list.html', context)


@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            _apply_schedule(request, course)
            messages.success(request, "Yangi kurs muvaffaqiyatli qo'shildi.")
        else:
            messages.error(request, "Kurs qo'shishda xatolik bor. Formani tekshiring.")
    return redirect('courses:course_list')  # ✅ namespace bilan


@login_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            _apply_schedule(request, course)
            messages.success(request, "Kurs muvaffaqiyatli tahrirlandi.")
        else:
            messages.error(request, "Kursni tahrirlashda xatolik bor.")
    return redirect('courses:course_list')  # ✅


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        course.delete()
        messages.success(request, "Kurs o'chirildi.")
    return redirect('courses:course_list')  # ✅


@login_required
def move_student_to_other_course(request, student_id):
    student = get_object_or_404(Student.objects.select_related('course'), pk=student_id)
    current_course = student.course

    if request.method == 'POST':
        form = StudentMoveForm(request.POST, current_course=current_course)
        if form.is_valid():
            new_course = form.cleaned_data['new_course']
            student.course = new_course
            student.save()
            messages.success(
                request,
                f"{student.full_name} muvaffaqiyatli '{new_course.title}' kursiga ko'chirildi."
            )
        else:
            messages.error(request, "Studentni ko'chirishda xatolik yuz berdi.")
    return redirect('courses:course_list')  # ✅