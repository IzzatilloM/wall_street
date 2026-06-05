"""
Bot uchun Django ORM yordamchilari (async-safe).
Har bir DB operatsiyasi sync_to_async bilan o'raladi.
"""
import django_setup  # noqa: F401  (Django ni ishga tushiradi)

import secrets

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction

from students.models import Student
from courses.models import Course
from enrollments.models import TelegramLead

User = get_user_model()


# ══════════════════════════════════════════════════════
#  KURSLAR
# ══════════════════════════════════════════════════════
@sync_to_async
def get_active_courses(limit=50):
    qs = (
        Course.objects.filter(is_active=True)
        .select_related('teacher')
        .order_by('category', 'title')[:limit]
    )
    result = []
    for c in qs:
        result.append({
            'id': c.id,
            'title': c.title,
            'category': c.category_badge,
            'level': c.get_level_display(),
            'duration': c.duration_display,
            'price': float(c.price),
            'teacher': c.teacher.full_name if c.teacher else "—",
            'description': (c.description or '').strip(),
            'students': c.students_count,
        })
    return result


@sync_to_async
def get_course_detail(course_id):
    c = (
        Course.objects.filter(id=course_id, is_active=True)
        .select_related('teacher')
        .first()
    )
    if not c:
        return None
    return {
        'id': c.id,
        'title': c.title,
        'category': c.category_badge,
        'level': c.get_level_display(),
        'duration': c.duration_display,
        'price': float(c.price),
        'teacher': c.teacher.full_name if c.teacher else "—",
        'description': (c.description or '').strip() or "Tavsif kiritilmagan.",
        'students': c.students_count,
    }


# ══════════════════════════════════════════════════════
#  TALABA RO'YXATDAN O'TKAZISH
# ══════════════════════════════════════════════════════
@sync_to_async
def phone_exists(phone):
    return Student.objects.filter(phone=phone).exists()


@sync_to_async
def telegram_already_registered(chat_id):
    return User.objects.filter(telegram_chat_id=str(chat_id)).exists()


def _unique_username(base):
    username = base
    i = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{i}"
        i += 1
    return username


@sync_to_async
def register_lead(first_name, last_name, phone, chat_id, username=None, email=None):
    """
    Telegram orqali kelgan ariza — to'g'ridan-to'g'ri talaba YARATMAYDI.
    Admin dashboard'dagi notification'ga tushadi va admin "Ro'yxatga olish"
    tugmasi orqali Enrollment yaratadi.
    Qaytaradi: TelegramLead obyekti.
    """
    email = (email or '').strip().lower() or None

    # Bir xil telefon + chat_id bo'yicha hali ko'rib chiqilmagan ariza bo'lsa,
    # yangisini yaratmaymiz (takrorlanishning oldini olish).
    existing = TelegramLead.objects.filter(
        phone=phone, status='new'
    ).order_by('-created_at').first()
    if existing:
        existing.first_name = first_name
        existing.last_name = last_name
        existing.email = email
        existing.telegram_chat_id = str(chat_id)
        existing.telegram_username = username or ''
        existing.save()
        return existing

    lead = TelegramLead.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        telegram_chat_id=str(chat_id),
        telegram_username=username or '',
        status='new',
    )
    return lead


@sync_to_async
def register_student(first_name, last_name, phone, chat_id, username=None, email=None):
    """
    Telegram orqali kelgan talabani tizimga qo'shadi:
      - accounts.CustomUser (role='student', telegram bilan tasdiqlangan)
      - students.Student (admin panelda ko'rinadi)
    Qaytaradi: (student, login_username, password)
    """
    email = (email or '').strip().lower() or None

    with transaction.atomic():
        base = f"std_{phone}" if phone else f"tg_{chat_id}"
        login_username = _unique_username(base)
        raw_password = secrets.token_urlsafe(6)

        user = User.objects.create_user(
            username=login_username,
            password=raw_password,
            first_name=first_name,
            last_name=last_name,
            email=email or '',
        )
        user.role = 'student'
        user.phone = phone
        user.verification_method = 'telegram'
        user.is_verified = True
        user.telegram_chat_id = str(chat_id)
        if username:
            user.telegram_username = username
        user.save()

        student = Student.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            is_active=True,
        )

    return student, login_username, raw_password
