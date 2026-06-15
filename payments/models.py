from django.db import models
from django.utils import timezone
from django.conf import settings
from students.models import Student


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank transfer'),
        ('online', 'Online payment'),
    ]

    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partially paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'), (5, 'May'), (6, 'June'),
        (7, 'July'), (8, 'August'), (9, 'September'),
        (10, 'October'), (11, 'November'), (12, 'December'),
    ]

    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Kurs'
    )
    instructor = models.ForeignKey(
        'instructors.Instructor', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='payments', verbose_name="O'qituvchi"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="To'lov summasi"
    )
    discount = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, verbose_name='Chegirma'
    )

    # ✅ Tuzatildi: DateField → PositiveSmallIntegerField, ices → choices
    payment_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        default=timezone.now().month,
        verbose_name="To'lov oyi"
    )
    payment_year = models.PositiveSmallIntegerField(
        default=timezone.now().year,
        verbose_name="To'lov yili"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES,
        default='cash', verbose_name="To'lov usuli"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='paid', verbose_name='Holat'
    )
    note = models.TextField(blank=True, null=True, verbose_name='Izoh')
    paid_at = models.DateTimeField(
        default=timezone.now, verbose_name="To'lov sanasi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-paid_at']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = Payment.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.receipt_number = f"WS-{timezone.now().year}-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def net_amount(self):
        return self.amount - self.discount

    def __str__(self):
        return f"{self.receipt_number} | {self.student} — {self.course}"


class PaymentTransaction(models.Model):
    """Mobil ilova orqali onlayn to'lov (Payme / Click) tranzaksiyasi.

    Har bir tranzaksiya bitta `Payment` (status='pending') bilan bog'lanadi.
    To'lov muvaffaqiyatli yakunlanganda (perform/complete) Payment.status='paid'
    bo'ladi va tegishli Enrollment.paid_amount yangilanadi → CRM'da ko'rinadi.
    """

    PROVIDER_CHOICES = [
        ('payme', 'Payme'),
        ('click', 'Click'),
    ]

    # Payme holatlari: 1 — yaratildi, 2 — to'landi, -1/-2 — bekor qilindi
    STATE_CREATED = 1
    STATE_COMPLETED = 2
    STATE_CANCELLED = -1
    STATE_CANCELLED_AFTER = -2

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='transactions'
    )
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES)
    provider_tx_id = models.CharField(
        max_length=64, blank=True, default='', db_index=True,
        verbose_name="Provayder tranzaksiya ID"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    state = models.IntegerField(default=STATE_CREATED)
    reason = models.IntegerField(null=True, blank=True)

    # Payme vaqtlari (millisekund)
    create_time = models.BigIntegerField(default=0)
    perform_time = models.BigIntegerField(default=0)
    cancel_time = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Onlayn to'lov tranzaksiyasi"
        verbose_name_plural = "Onlayn to'lov tranzaksiyalari"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'provider_tx_id']),
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_tx_id} → {self.payment.receipt_number}"