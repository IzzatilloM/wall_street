"""Mobil ilovani sinash uchun namuna ma'lumotlar.

Ishga tushirish:
    python manage.py shell < seed_mobile.py
"""
from django.utils import timezone

from accounts.models import CustomUser
from students.models import Student
from courses.models import Course
from instructors.models import Instructor
from payments.models import Payment
from news.models import News

# 1) Student foydalanuvchi (username/parol bilan kiradi)
user, created = CustomUser.objects.get_or_create(
    username='student1',
    defaults={'role': 'student', 'is_verified': True, 'first_name': 'Ali', 'last_name': 'Valiyev'},
)
user.set_password('student123')
user.role = 'student'
user.is_verified = True
user.save()

# 2) Student profili
student, _ = Student.objects.get_or_create(
    user=user,
    defaults={
        'first_name': 'Ali', 'last_name': 'Valiyev',
        'phone': '+998901112233', 'email': 'ali@example.com',
        'coins': 150,
    },
)

# 3) Kurs uchun o'qituvchi (teacher rolidagi foydalanuvchi → Instructor)
teacher_user, _ = CustomUser.objects.get_or_create(
    username='teacher1',
    defaults={'role': 'teacher', 'is_verified': True,
              'first_name': 'John', 'last_name': 'Smith'},
)
teacher_user.set_password('teacher123')
teacher_user.role = 'teacher'
teacher_user.save()
# Instructor profili signal orqali avtomatik yaratiladi
teacher = Instructor.objects.filter(user=teacher_user).first()

course, _ = Course.objects.get_or_create(
    title='General English',
    defaults={'category': 'english', 'level': 'intermediate', 'price': 500000, 'teacher': teacher},
)

# 4) To'lovlar
if not Payment.objects.filter(student=student).exists():
    Payment.objects.create(
        student=student, course=course, amount=500000,
        payment_month=5, payment_year=2026, status='paid',
        payment_method='card', paid_at=timezone.now(),
    )
    Payment.objects.create(
        student=student, course=course, amount=500000,
        payment_month=6, payment_year=2026, status='pending',
        payment_method='cash', paid_at=timezone.now(),
    )

# 5) Yangiliklar
if not News.objects.exists():
    News.objects.create(
        title="Yangi IELTS kursi ochildi!",
        short_text="Iyun oyidan yangi IELTS guruhi boshlanadi.",
        body="Wall Street o'quv markazida yangi IELTS intensiv kursi ochildi. "
             "Tajribali o'qituvchilar bilan 3 oyda 6.5+ ball oling!",
        telegram_url="https://t.me/wallstreet",
        is_pinned=True,
    )
    News.objects.create(
        title="Bayram tabrigi",
        short_text="Hammani kelayotgan bayram bilan tabriklaymiz!",
        body="Aziz o'quvchilar, sizlarni chin qalbdan tabriklaymiz.",
    )

print("SEED TAYYOR: login=student1 / parol=student123")
print("Studentlar:", Student.objects.count(), "| To'lovlar:", Payment.objects.count(), "| Yangiliklar:", News.objects.count())
