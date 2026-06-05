# -*- coding: utf-8 -*-
"""
Talabalarni kurslarga yozish (Enrollment).

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_enrollments.py', encoding='utf-8').read())"

Har bir talaba 1-3 ta ingliz tili kursiga yoziladi. Idempotent.
"""
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import CustomUser
from students.models import Student
from courses.models import Course
from enrollments.models import Enrollment

admin = CustomUser.objects.filter(role='admin').first()
courses = list(Course.objects.filter(category='english', is_active=True).order_by('id'))
students = list(Student.objects.all().order_by('id'))

PAY_STATES = ['paid', 'partial', 'unpaid']
created = 0

for idx, st in enumerate(students):
    # har bir talabaga 1-3 ta kurs (idx asosida deterministik)
    n = (idx % 3) + 1
    chosen = [courses[(idx + j) % len(courses)] for j in range(n)]

    for k, course in enumerate(chosen):
        if Enrollment.objects.filter(student=st, course=course).exists():
            continue

        fee = Decimal(course.price)
        pstate = PAY_STATES[(idx + k) % len(PAY_STATES)]
        if pstate == 'paid':
            paid = fee
            status = 'active'
        elif pstate == 'partial':
            paid = (fee / 2).quantize(Decimal('1'))
            status = 'active'
        else:  # unpaid
            paid = Decimal('0')
            status = 'pending'

        start = date(2026, 1, 1) + timedelta(days=(idx % 60))
        months = course.duration_value if course.duration_unit == 'month' else 1
        end = start + timedelta(days=30 * months)

        Enrollment.objects.create(
            student=st,
            course=course,
            instructor=course.teacher,
            status=status,
            payment_status=pstate,
            course_fee=fee,
            discount=Decimal('0'),
            paid_amount=paid,
            start_date=start,
            end_date=end,
            source='walk_in',
            created_by=admin,
        )
        created += 1

print(f"Yangi enrollment: {created}")
print(f"Jami enrollment: {Enrollment.objects.count()}")
print(f"Yozilgan talabalar: {Enrollment.objects.values('student').distinct().count()} / {len(students)}")
# har kursdagi talabalar soni
print("Kurslar bo'yicha talabalar:")
for c in courses:
    cnt = Enrollment.objects.filter(course=c).count()
    print(f"  {c.title}: {cnt}")
