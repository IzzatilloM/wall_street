from django.db import models
from django.conf import settings


class Student(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        blank=True,
        null=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20, unique=True)
    parent_phone = models.CharField(max_length=20, blank=True, null=True)

    email = models.EmailField(blank=True, null=True, unique=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    birth_date = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='students/', blank=True, null=True)

    coins = models.PositiveIntegerField(default=0)

    # ─── AI churn bashorati (Claude API) ───
    # 0-100: talabaning o'qishni tashlab ketish ehtimoli.
    # None — hali hisoblanmagan.
    churn_risk_score = models.FloatField(
        blank=True, null=True,
        verbose_name='Churn risk (0-100)',
    )
    churn_risk_reason = models.TextField(
        blank=True, default='',
        verbose_name='Churn risk sababi (AI)',
    )
    churn_risk_updated_at = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Churn risk yangilangan vaqt',
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def churn_risk_level(self):
        """Badge rangi uchun: low / medium / high (None — hisoblanmagan)."""
        if self.churn_risk_score is None:
            return ''
        if self.churn_risk_score >= 70:
            return 'high'
        if self.churn_risk_score >= 40:
            return 'medium'
        return 'low'