from django.conf import settings
from django.db import models
from django.utils import timezone


class CenterSettings(models.Model):
    """Markazning umumiy sozlamalari (singleton)."""
    center_name = models.CharField(max_length=200, default='Wall Street')
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=10, default="so'm")

    class Meta:
        verbose_name = 'Markaz sozlamasi'
        verbose_name_plural = 'Markaz sozlamalari'

    def __str__(self):
        return self.center_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SupportTicket(models.Model):
    """
    «Wall Street Technic Bot» orqali kelgan texnik yordam murojaati.

    Bot bu yerga yozadi → admin Settings sahifasidagi «Yordam markazi»
    bo'limida ko'radi → javob beradi / holatni o'zgartiradi.
    Admin javobi foydalanuvchining Telegramiga avtomatik yuboriladi.
    """

    CATEGORY_CHOICES = [
        ('password', 'Parolni tiklash'),
        ('login',    'Tizimga kira olmayapman'),
        ('payment',  "To'lov muammosi"),
        ('account',  'Hisob / profil muammosi'),
        ('course',   'Kurs / dars muammosi'),
        ('bug',      'Texnik xatolik (bug)'),
        ('other',    'Boshqa muammo'),
    ]

    # Har bir kategoriya uchun ikonka va rang (template/bot bezagi uchun)
    CATEGORY_META = {
        'password': ('fa-key',            '🔑'),
        'login':    ('fa-right-to-bracket', '🚪'),
        'payment':  ('fa-credit-card',    '💳'),
        'account':  ('fa-user-gear',      '👤'),
        'course':   ('fa-graduation-cap', '🎓'),
        'bug':      ('fa-bug',            '🐞'),
        'other':    ('fa-circle-question', '❓'),
    }

    PRIORITY_CHOICES = [
        ('low',    'Past'),
        ('normal', "O'rta"),
        ('high',   'Yuqori'),
        ('urgent', 'Shoshilinch'),
    ]

    STATUS_CHOICES = [
        ('new',         'Yangi'),
        ('in_progress', "Ko'rib chiqilmoqda"),
        ('resolved',    'Hal qilindi'),
        ('closed',      'Yopilgan'),
    ]

    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES,
                                   default='other', verbose_name='Kategoriya')
    subject     = models.CharField(max_length=200, blank=True, verbose_name='Mavzu')
    description = models.TextField(verbose_name='Muammo tavsifi')

    full_name   = models.CharField(max_length=150, blank=True, verbose_name='Murojaatchi')
    phone       = models.CharField(max_length=30, blank=True, verbose_name='Telefon')
    contact     = models.CharField(max_length=190, blank=True,
                                   verbose_name='Login / email')

    telegram_chat_id  = models.CharField(max_length=50, blank=True)
    telegram_username = models.CharField(max_length=150, blank=True)

    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES,
                                   default='normal', verbose_name='Muhimlik')
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES,
                                   default='new', verbose_name='Holat')

    admin_reply = models.TextField(blank=True, verbose_name='Admin javobi')
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_tickets',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(default=timezone.now, verbose_name='Kelgan vaqt')
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Texnik murojaat'
        verbose_name_plural = 'Texnik murojaatlar'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.code} · {self.get_category_display()}"

    # ── Computed helpers (template / bot uchun) ───────────────────────
    @property
    def code(self):
        """Murojaat raqami — WS-0001 ko'rinishida."""
        return f"WS-{self.pk:04d}" if self.pk else "WS-—"

    @property
    def category_icon(self):
        return self.CATEGORY_META.get(self.category, ('fa-circle-question', '❓'))[0]

    @property
    def category_emoji(self):
        return self.CATEGORY_META.get(self.category, ('fa-circle-question', '❓'))[1]

    @property
    def is_open(self):
        return self.status in ('new', 'in_progress')
