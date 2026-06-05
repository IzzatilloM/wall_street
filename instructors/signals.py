"""
Foydalanuvchi (CustomUser) saqlanganda Instructor profilini
avtomatik sinxronlash.

- role == 'teacher' yoki 'admin'  → Instructor yaratiladi / saqlanadi
- role 'student' ga o'zgarsa      → Instructor profili o'chiriladi

Shu signal tufayli ro'yxatdan o'tgan har bir teacher/admin
darhol instructorlar sahifasida ko'rinadi.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Instructor

User = get_user_model()


@receiver(post_save, sender=User)
def sync_instructor_profile(sender, instance, created, **kwargs):
    role = getattr(instance, 'role', None)

    if role in ('teacher', 'admin'):
        full_name = f"{instance.first_name} {instance.last_name}".strip()
        if not full_name:
            full_name = instance.username

        Instructor.objects.get_or_create(
            user=instance,
            defaults={'full_name': full_name},
        )
    else:
        # student yoki boshqa rolga o'tsa — instructor profilini olib tashlaymiz
        Instructor.objects.filter(user=instance).delete()
