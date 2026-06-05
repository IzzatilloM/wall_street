from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    VERIFICATION_CHOICES = [
        ('gmail', 'Gmail'),
        ('telegram', 'Telegram'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='teacher'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    verification_method = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='gmail'
    )

    is_verified = models.BooleanField(default=False)

    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    telegram_username = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Admin sozlamalar bo'limida ko'rinadigan ochiq parol nusxasi.
    # Django asosiy parolni hash qiladi (qaytarib bo'lmaydi), shu sababli
    # o'qituvchi/talabaga berilgan parolni admin ko'ra olishi uchun shu
    # yerda ochiq holda ham saqlanadi. Faqat ilova orqali o'rnatilgan
    # parollar bu yerga yoziladi.
    plain_password = models.CharField(
        max_length=128,
        blank=True,
        default='',
    )

    def save(self, *args, **kwargs):
        # Admin panel yoki superuser orqali yaratilgan userlar
        # avtomatik verified bo'ladi
        if self.is_staff or self.is_superuser:
            self.is_verified = True

        # Role='admin' bo'lsa ham verified qilish
        if self.role == 'admin':
            self.is_verified = True

        # Admin limit tekshiruvi - faqat yangi user uchun
        if self.role == 'admin' and not self.pk:
            max_admin_count = getattr(settings, 'MAX_ADMIN_COUNT', 2)
            current_admin_count = CustomUser.objects.filter(role='admin').count()
            if current_admin_count >= max_admin_count:
                raise ValueError(
                    f"Faqat {max_admin_count} ta admin bo'lishi mumkin!"
                )

        super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.get_full_name() or self.username
        return f"{full_name} ({self.role})"