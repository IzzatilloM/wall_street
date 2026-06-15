"""O'qituvchi mobil ilovasi uchun modellar (teacher_api).

Bu modul o'qituvchining shaxsiy jurnali: o'zi yaratgan guruhlar,
ulardagi o'quvchilar, dars davomatlari va oylik hisob-kitobi.
Autentifikatsiya mavjud `accounts.CustomUser` (role='teacher') + JWT orqali.
"""
from django.conf import settings
from django.db import models


class TeacherProfile(models.Model):
    """O'qituvchining oylik/dars haqi sozlamalari (CustomUser ustiga)."""

    SALARY_CHOICES = [
        ('monthly', 'Oylik'),
        ('per_lesson', 'Har bir dars uchun'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    salary_type = models.CharField(max_length=12, choices=SALARY_CHOICES, default='per_lesson')
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_per_lesson = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_per_hour = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil: {self.user.username}"


class TGroup(models.Model):
    """O'qituvchi yaratgan guruh."""

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='t_groups',
    )
    name = models.CharField(max_length=120)
    subject = models.CharField(max_length=120, blank=True, null=True)
    lesson_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    schedule = models.JSONField(blank=True, null=True)   # {"days":["Mon"],"time":"18:00"}
    color = models.CharField(max_length=9, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class TStudent(models.Model):
    """Guruhdagi o'quvchi."""

    STATUS_CHOICES = [('active', 'Faol'), ('inactive', 'Nofaol')]

    group = models.ForeignKey(TGroup, on_delete=models.CASCADE, related_name='students')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='teacher_api/students/', blank=True, null=True)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class TAttendance(models.Model):
    """Bitta dars sessiyasi (davomat sarlavhasi)."""

    group = models.ForeignKey(TGroup, on_delete=models.CASCADE, related_name='attendances')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='t_attendances'
    )
    lesson_date = models.DateField()
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_min = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-lesson_date', '-id']

    def __str__(self):
        return f"{self.group.name} — {self.lesson_date}"


class TAttendanceItem(models.Model):
    """Sessiyadagi har bir o'quvchining holati."""

    STATUS_CHOICES = [('present', 'Keldi'), ('absent', 'Kelmadi'), ('late', 'Kechikdi')]

    attendance = models.ForeignKey(TAttendance, on_delete=models.CASCADE, related_name='items')
    student = models.ForeignKey(TStudent, on_delete=models.CASCADE, related_name='attendance_items')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('attendance', 'student')
