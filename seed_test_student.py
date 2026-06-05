# -*- coding: utf-8 -*-
"""Mobil ilovani sinash uchun bitta yangi TEST student yaratadi.

Ishga tushirish (loyiha ildizidan):
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_test_student.py', encoding='utf-8').read())"

Kirish ma'lumotlari:
    username : test.student
    parol    : Test@2026

Skript idempotent — qayta ishga tushirsa, dublikat yaratmaydi.
"""
from datetime import date, timedelta

from django.utils import timezone

from accounts.models import CustomUser
from students.models import Student
from courses.models import Course
from instructors.models import Instructor
from enrollments.models import Enrollment
from payments.models import Payment

USERNAME = "test.student"
PASSWORD = "Test@2026"

# 1) Login foydalanuvchisi (CustomUser) ─ ilovaga shu bilan kiriladi
user, _ = CustomUser.objects.get_or_create(
    username=USERNAME,
    defaults={"role": "student", "is_verified": True,
              "first_name": "Test", "last_name": "Student"},
)
user.role = "student"
user.is_verified = True
user.first_name = "Test"
user.last_name = "Student"
user.set_password(PASSWORD)
user.save()

# 2) Student profili (telefon va email unique)
student = Student.objects.filter(user=user).first()
if not student:
    student, _ = Student.objects.get_or_create(
        phone="+998900000099",
        defaults={"first_name": "Test", "last_name": "Student",
                  "email": "test.student@wallstreet.uz", "coins": 100},
    )
    student.user = user
student.first_name = "Test"
student.last_name = "Student"
student.coins = 100
student.is_active = True
student.save()

# 3) Mavjud kursga yozamiz (ilovada "Mening kurslarim" ko'rinishi uchun)
course = Course.objects.first()
if course:
    instructor = getattr(course, "teacher", None) or Instructor.objects.first()
    Enrollment.objects.get_or_create(
        student=student, course=course,
        defaults={
            "instructor": instructor,
            "status": "active",
            "payment_status": "partial",
            "course_fee": 1200000,
            "discount": 200000,
            "paid_amount": 600000,
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=90),
        },
    )

# 4) To'lovlar (ilovada "To'lovlar" ko'rinishi uchun)
if course and not Payment.objects.filter(student=student).exists():
    Payment.objects.create(
        student=student, course=course, amount=500000,
        payment_month=timezone.now().month, payment_year=timezone.now().year,
        status="paid", payment_method="card", paid_at=timezone.now(),
        note="Test to'lov (ilova sinovi)",
    )
    Payment.objects.create(
        student=student, course=course, amount=500000,
        payment_month=timezone.now().month, payment_year=timezone.now().year,
        status="pending", payment_method="cash", paid_at=timezone.now(),
    )

print("=" * 52)
print("TEST STUDENT TAYYOR — ilovaga shu bilan kiring:")
print("  username :", USERNAME)
print("  parol    :", PASSWORD)
print("  ism      :", student.full_name, "| student id:", student.id)
print("  kurs     :", course.title if course else "(kurs topilmadi)")
print("  to'lovlar:", Payment.objects.filter(student=student).count())
print("=" * 52)
