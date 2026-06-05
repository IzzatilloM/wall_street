from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import csv
from django.http import HttpResponse

from .models import Attendance, Student, Course, CoinAward


@login_required(login_url='login')
def attendance_list(request):
    if hasattr(request.user, 'role') and request.user.role == 'teacher':
        courses = Course.objects.filter(instructor=request.user).select_related('instructor')
    else:
        courses = Course.objects.select_related('instructor').all()

    attendances = Attendance.objects.select_related('student', 'course', 'student__user').all()

    course_filter = request.GET.get('course')
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    if course_filter:
        attendances = attendances.filter(course_id=course_filter)

    if date_filter:
        try:
            attendances = attendances.filter(date=datetime.strptime(date_filter, '%Y-%m-%d').date())
        except ValueError:
            pass

    if status_filter:
        attendances = attendances.filter(status=status_filter)

    if search_query:
        attendances = attendances.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query)
        )

    # ── Statistika (filtrlangan to'plam bo'yicha, paginatsiyadan oldin) ──
    total_records = attendances.count()
    present_count = attendances.filter(status='present').count()
    absent_count  = attendances.filter(status='absent').count()
    late_count    = attendances.filter(status='late').count()
    attended      = present_count + late_count
    present_rate  = round((attended / total_records) * 100) if total_records else 0
    today_count   = attendances.filter(date=timezone.now().date()).count()

    paginator = Paginator(attendances, 10)
    page = request.GET.get('page')
    try:
        attendances = paginator.page(page)
    except PageNotAnInteger:
        attendances = paginator.page(1)
    except EmptyPage:
        attendances = paginator.page(paginator.num_pages)

    students = Student.objects.select_related('user').prefetch_related('courses').all()

    context = {
        'attendances': attendances,
        'courses': courses,
        'students': students,
        'selected_course': course_filter,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        # statistika
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'present_rate': present_rate,
        'today_count': today_count,
        'courses_count': courses.count(),
    }

    return render(request, 'attendance_list.html', context)  # ✅


@login_required(login_url='login')
def mark_attendance(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            course_id = request.POST.get('course')
            date = request.POST.get('date')
            status = request.POST.get('status')
            note = request.POST.get('note', '')

            if not all([student_id, course_id, date, status]):
                messages.error(request, 'All fields are required.')
                return redirect('attendance:attendance_list')

            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id)

            attendance, created = Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=date,
                defaults={
                    'status': status,
                    'note': note,
                    'marked_by': request.user
                }
            )

            if created:
                messages.success(request, f'Attendance marked for {student.user.get_full_name()} in {course.name}')
            else:
                messages.success(request, f'Attendance updated for {student.user.get_full_name()} in {course.name}')

        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')

    return redirect('attendance:attendance_list')


@login_required(login_url='login')
def update_attendance(request, attendance_id):
    if request.method == 'POST':
        try:
            attendance = get_object_or_404(Attendance, id=attendance_id)
            status = request.POST.get('status')
            note = request.POST.get('note', '')

            attendance.status = status
            attendance.note = note
            attendance.marked_by = request.user
            attendance.save()

            messages.success(request, 'Attendance updated successfully.')

        except Exception as e:
            messages.error(request, f'Error updating attendance: {str(e)}')

    return redirect('attendance:attendance_list')


@login_required(login_url='login')
def delete_attendance(request, attendance_id):
    try:
        attendance = get_object_or_404(Attendance, id=attendance_id)
        student_name = attendance.student.user.get_full_name()
        course_name = attendance.course.name

        attendance.delete()
        messages.success(request, f'Attendance record deleted for {student_name} in {course_name}')
    except Exception as e:
        messages.error(request, f'Error deleting attendance: {str(e)}')

    return redirect('attendance:attendance_list')


@login_required(login_url='login')
def student_attendance_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    courses = student.courses.all()

    course_attendance = {}
    for course in courses:
        records = Attendance.objects.filter(student=student, course=course)
        percentage = Attendance.get_student_course_attendance(student, course)

        course_attendance[course] = {
            'records': records,
            'percentage': percentage,
            'total': records.count(),
            'present': records.filter(status='present').count(),
            'absent': records.filter(status='absent').count(),
            'late': records.filter(status='late').count(),
        }

    overall_stats = Attendance.get_student_overall_attendance(student)

    context = {
        'student': student,
        'course_attendance': course_attendance,
        'overall_stats': overall_stats,
    }
    return render(request, 'attendance_list.html', context)  # ✅


@login_required(login_url='login')
def award_coins(request, student_id):
    """
    Talabaga coin qo'shadi / ayiradi.
    students.Student.coins balansini yangilaydi va CoinAward tarixini saqlaydi.
    """
    if request.method != 'POST':
        return redirect('attendance:attendance_list')

    student = get_object_or_404(Student, id=student_id)

    try:
        amount = int(request.POST.get('amount', 0))
    except (TypeError, ValueError):
        amount = 0

    reason = (request.POST.get('reason') or '').strip()

    if amount == 0:
        messages.error(request, "Coin miqdori 0 bo'lishi mumkin emas.")
        return redirect('attendance:attendance_list')

    # CRM Student profili (coin balansi shu yerda)
    crm = student.crm_student
    if crm is None:
        messages.error(
            request,
            f"{student.get_full_name()} uchun talaba profili topilmadi — coin qo'shib bo'lmadi."
        )
        return redirect('attendance:attendance_list')

    new_balance = (crm.coins or 0) + amount
    if new_balance < 0:
        new_balance = 0
    crm.coins = new_balance
    crm.save(update_fields=['coins'])

    CoinAward.objects.create(
        student=student,
        amount=amount,
        reason=reason,
        awarded_by=request.user,
    )

    verb = "qo'shildi" if amount > 0 else "ayirildi"
    messages.success(
        request,
        f"🪙 {student.get_full_name()} ga {abs(amount)} coin {verb}. "
        f"Yangi balans: {new_balance} coin."
    )
    return redirect('attendance:attendance_list')


@login_required(login_url='login')
def export_attendance(request):
    try:
        course_id = request.GET.get('course')
        date = request.GET.get('date')

        attendances = Attendance.objects.select_related('student', 'course', 'marked_by')

        if course_id:
            attendances = attendances.filter(course_id=course_id)
            course = Course.objects.get(id=course_id)
            filename = f'attendance_{course.code}_{timezone.now().date()}.csv'
        else:
            filename = f'attendance_report_{timezone.now().date()}.csv'

        if date:
            try:
                attendances = attendances.filter(date=datetime.strptime(date, '%Y-%m-%d').date())
            except ValueError:
                pass

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Student Name', 'Student ID', 'Course', 'Date', 'Status', 'Note', 'Marked By'])

        for attendance in attendances:
            writer.writerow([
                attendance.student.user.get_full_name(),
                attendance.student.student_id,
                attendance.course.name,
                attendance.date.strftime('%Y-%m-%d'),
                attendance.get_status_display(),
                attendance.note or '-',
                attendance.marked_by.get_full_name() if attendance.marked_by else 'N/A'
            ])

        return response

    except Exception as e:
        messages.error(request, f'Error exporting attendance: {str(e)}')
        return redirect('attendance:attendance_list')