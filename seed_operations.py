# -*- coding: utf-8 -*-
"""
Attendance / Payments / Salary sahifalari uchun ma'lumotlarni to'ldiradi.
Bu sahifalar ALOHIDA modellardan foydalanadi — shularni real ma'lumotdan
(courses.Course, students.Student, enrollments.Enrollment, instructors.Instructor)
sinxronlaydi.

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_operations.py', encoding='utf-8').read())"
Idempotent.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from courses.models import Course as RealCourse
from students.models import Student as RealStudent
from instructors.models import Instructor
from enrollments.models import Enrollment

from attendance.models import Course as AttCourse, Student as AttStudent, Attendance
from payments.models import Payment
from staff_salary.models import SalaryPayment

now = timezone.now()

# ══════════════════════════════════════════════════════
# 1) ATTENDANCE — alohida Course/Student modellarini sinxronlash
# ══════════════════════════════════════════════════════
real_to_att_course = {}
for rc in RealCourse.objects.select_related('teacher__user').all():
    instr_user = rc.teacher.user if (rc.teacher and rc.teacher.user) else None
    ac, _ = AttCourse.objects.get_or_create(
        code=f"WS-C{rc.id}",
        defaults={'name': rc.title, 'instructor': instr_user},
    )
    # nom/instruktorni yangilab turamiz
    if ac.name != rc.title or ac.instructor_id != (instr_user.id if instr_user else None):
        ac.name = rc.title
        ac.instructor = instr_user
        ac.save()
    real_to_att_course[rc.id] = ac

real_to_att_student = {}
for rs in RealStudent.objects.select_related('user').all():
    if not rs.user:
        continue
    ast, _ = AttStudent.objects.get_or_create(
        user=rs.user,
        defaults={'student_id': f"WS-S{rs.id}"},
    )
    real_to_att_student[rs.id] = ast

# M2M: enrollment asosida talabani kursga bog'lash
links = 0
for e in Enrollment.objects.select_related('student', 'course').all():
    if not e.course:
        continue
    ac = real_to_att_course.get(e.course_id)
    ast = real_to_att_student.get(e.student_id)
    if ac and ast and not ast.courses.filter(pk=ac.pk).exists():
        ast.courses.add(ac)
        links += 1

print(f"[1] attendance.Course: {AttCourse.objects.count()} | "
      f"attendance.Student: {AttStudent.objects.count()} | yangi M2M: {links}")

# ══════════════════════════════════════════════════════
# 2) PAYMENTS — enrollmentlardan to'lov yozuvlari
# ══════════════════════════════════════════════════════
_PSTATUS = {'paid': 'paid', 'partial': 'partial', 'unpaid': 'pending',
            'overdue': 'overdue', 'refunded': 'cancelled'}
pay_created = 0
for e in Enrollment.objects.select_related('student', 'course', 'instructor').all():
    if not e.course:
        continue
    month = (e.start_date.month if e.start_date else now.month)
    year = (e.start_date.year if e.start_date else now.year)
    if Payment.objects.filter(student=e.student, course=e.course,
                              payment_month=month, payment_year=year).exists():
        continue
    amount = e.paid_amount if e.paid_amount and e.paid_amount > 0 else e.net_fee
    Payment.objects.create(
        student=e.student,
        course=e.course,
        instructor=e.instructor,
        amount=amount or Decimal('0'),
        discount=e.discount or Decimal('0'),
        payment_month=month,
        payment_year=year,
        payment_method='cash',
        status=_PSTATUS.get(e.payment_status, 'paid'),
        paid_at=now,
    )
    pay_created += 1

print(f"[2] Yangi to'lov: {pay_created} | jami Payment: {Payment.objects.count()}")

# ══════════════════════════════════════════════════════
# 3) SALARY — o'qituvchilar uchun oylik to'lovlar
# ══════════════════════════════════════════════════════
sal_created = 0
for i, inst in enumerate(Instructor.objects.filter(user__role='teacher')):
    status = 'paid' if i % 3 != 0 else 'pending'
    if SalaryPayment.objects.filter(instructor=inst, month=now.month, year=now.year).exists():
        continue
    SalaryPayment.objects.create(
        instructor=inst,
        amount=inst.salary or Decimal('500'),
        month=now.month,
        year=now.year,
        status=status,
        note="Joriy oy uchun oylik",
    )
    sal_created += 1

print(f"[3] Yangi oylik: {sal_created} | jami SalaryPayment: {SalaryPayment.objects.count()}")
print("TAYYOR.")
