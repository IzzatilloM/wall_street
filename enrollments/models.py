from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Enrollment(models.Model):
    """
    Talabaning kursga yozilishi (ro'yxatdan o'tish).
    Enrollment yaratilganda Student ham avtomatik yaratiladi yoki mavjudi topiladi.
    """

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('frozen',    'Frozen'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid',         'Unpaid'),
        ('partial',        'Partially paid'),
        ('paid',           'Fully paid'),
        ('overdue',        'Overdue'),
        ('refunded',       'Refunded'),
    ]

    SOURCE_CHOICES = [
        ('walk_in',    'Walk-in'),
        ('referral',   'Referral'),
        ('social',     'Social media'),
        ('website',    'Website'),
        ('phone',      'Phone'),
        ('other',      'Other'),
    ]

    # ── Asosiy bog'lanishlar ──────────────────────────────────────────────────
    student  = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Talaba',
    )
    course   = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='enrollments',
        verbose_name='Kurs',
    )
    group    = models.ForeignKey(
        'courses.Group',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='enrollments',
        verbose_name='Guruh',
    )
    instructor = models.ForeignKey(
        'instructors.Instructor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='enrollments',
        verbose_name="O'qituvchi",
    )

    # ── Holat ────────────────────────────────────────────────────────────────
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                      default='pending', verbose_name='Holat')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES,
                                      default='unpaid', verbose_name="To'lov holati")

    # ── Moliyaviy ma'lumotlar ─────────────────────────────────────────────────
    course_fee     = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0, verbose_name='Kurs narxi')
    discount       = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0, verbose_name='Chegirma')
    paid_amount    = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0, verbose_name="To'langan summa")

    # ── Sanalar ───────────────────────────────────────────────────────────────
    start_date     = models.DateField(null=True, blank=True,
                                      verbose_name='Boshlanish sanasi')
    end_date       = models.DateField(null=True, blank=True,
                                      verbose_name='Tugash sanasi')
    enrolled_at    = models.DateTimeField(default=timezone.now,
                                          verbose_name='Yozilgan vaqt')

    # ── Qo'shimcha ────────────────────────────────────────────────────────────
    source         = models.CharField(max_length=20, choices=SOURCE_CHOICES,
                                      default='walk_in', verbose_name='Manba')
    notes          = models.TextField(blank=True, verbose_name='Izoh')
    created_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_enrollments',
        verbose_name='Yaratuvchi',
    )
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Ro'yxatga olish"
        verbose_name_plural = "Ro'yxatga olishlar"
        ordering            = ['-enrolled_at']

    def __str__(self):
        return f"{self.student} → {self.course} ({self.get_status_display()})"

    # ── Computed properties ───────────────────────────────────────────────────
    @property
    def net_fee(self):
        return self.course_fee - self.discount

    @property
    def remaining_amount(self):
        return max(self.net_fee - self.paid_amount, 0)

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.net_fee

    @property
    def payment_percent(self):
        if self.net_fee <= 0:
            return 100
        return min(int(self.paid_amount / self.net_fee * 100), 100)


class TelegramLead(models.Model):
    """
    Telegram bot orqali ro'yxatdan o'tmoqchi bo'lgan talaba arizasi.
    Bot bu yerga yozadi → admin dashboard notification'da ko'radi →
    "Ro'yxatga olish" tugmasi orqali Enrollment yaratadi.
    """
    STATUS_CHOICES = [
        ('new',       'Yangi'),
        ('processed', "Ro'yxatga olingan"),
        ('rejected',  'Rad etilgan'),
    ]

    first_name        = models.CharField(max_length=100, verbose_name='Ism')
    last_name         = models.CharField(max_length=100, blank=True, verbose_name='Familiya')
    phone             = models.CharField(max_length=30, verbose_name='Telefon')
    email             = models.EmailField(blank=True, null=True, verbose_name='Email')
    telegram_chat_id  = models.CharField(max_length=50, blank=True)
    telegram_username = models.CharField(max_length=150, blank=True)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                  default='new', verbose_name='Holat')
    note       = models.TextField(blank=True, verbose_name='Izoh')
    enrollment = models.ForeignKey(
        'Enrollment', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_lead', verbose_name='Yaratilgan enrollment',
    )
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='processed_leads',
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Kelgan vaqt')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Telegram ariza'
        verbose_name_plural = 'Telegram arizalar'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class BotFSMState(models.Model):
    """
    Telegram bot uchun aiogram FSM holatini bazada saqlaydi.
    Webhook rejimida sayt bir nechta worker/jarayonda ishlasa ham
    ro'yxatdan o'tish bosqichlari (ism→familiya→telefon...) yo'qolmaydi.
    """
    key        = models.CharField(max_length=190, unique=True, db_index=True)
    state      = models.CharField(max_length=255, blank=True, default='')
    data       = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Bot FSM holati'
        verbose_name_plural = 'Bot FSM holatlari'

    def __str__(self):
        return f"{self.key} → {self.state or '∅'}"


class EnrollmentNote(models.Model):
    """Enrollment bo'yicha qo'shimcha izohlar tarixi."""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE,
                                   related_name='history_notes')
    author     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True)
    text       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note #{self.pk} — {self.enrollment}"