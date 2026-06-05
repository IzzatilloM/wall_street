from django.db import models
from django.core.validators import MinValueValidator


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('english', 'English'),
        ('it', 'IT'),
    ]
    LEVEL_CHOICES = [
        ('beginner',            'Beginner'),
        ('elementary',          'Elementary'),
        ('pre_intermediate',    'Pre-Intermediate'),
        ('intermediate',        'Intermediate'),
        ('upper_intermediate',  'Upper-Intermediate'),
        ('advanced',            'Advanced'),
        ('ielts',               'IELTS'),
        ('foundation',          'Foundation'),
        ('standard',            'Standard'),
        ('bootcamp',            'Bootcamp'),
        ('pro',                 'Pro'),
    ]
    DURATION_UNIT_CHOICES = [
        ('month', 'Month'),
        ('week',  'Week'),
    ]
    WEEKDAY_CHOICES = [
        ('mon', 'Dushanba'),
        ('tue', 'Seshanba'),
        ('wed', 'Chorshanba'),
        ('thu', 'Payshanba'),
        ('fri', 'Juma'),
        ('sat', 'Shanba'),
        ('sun', 'Yakshanba'),
    ]
    WEEKDAY_SHORT = {
        'mon': 'Dush', 'tue': 'Sesh', 'wed': 'Chor', 'thu': 'Pay',
        'fri': 'Jum', 'sat': 'Shan', 'sun': 'Yak',
    }

    title          = models.CharField(max_length=200)
    category       = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    level          = models.CharField(max_length=30, choices=LEVEL_CHOICES, default='standard')
    teacher        = models.ForeignKey(
        'instructors.Instructor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses',
    )
    duration_value = models.PositiveIntegerField(
        default=6, validators=[MinValueValidator(1)]
    )
    duration_unit  = models.CharField(
        max_length=10, choices=DURATION_UNIT_CHOICES, default='month'
    )
    price          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description    = models.TextField(blank=True)

    # ─── Dars jadvali (hafta kunlari + vaqt oralig'i) ───
    weekdays       = models.CharField(
        max_length=40, blank=True, default='',
        help_text="Vergul bilan ajratilgan kunlar, masalan: mon,wed,fri",
    )
    start_time     = models.TimeField(null=True, blank=True, verbose_name='Boshlanish vaqti')
    end_time       = models.TimeField(null=True, blank=True, verbose_name='Tugash vaqti')

    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"

    @property
    def duration_display(self):
        unit = "oy" if self.duration_unit == "month" else "hafta"
        return f"{self.duration_value} {unit}"

    @property
    def category_badge(self):
        return "English" if self.category == "english" else "IT"

    @property
    def students_count(self):
        return self.students.count()

    # ─── Jadval yordamchilari ───
    @property
    def weekday_list(self):
        """Tanlangan kun kodlari ro'yxati: ['mon', 'wed', 'fri']."""
        return [d for d in (self.weekdays or '').split(',') if d]

    @property
    def weekdays_display(self):
        """Qisqa kun nomlari: 'Dush, Chor, Jum'."""
        return ', '.join(self.WEEKDAY_SHORT.get(d, d) for d in self.weekday_list)

    @property
    def time_display(self):
        """Vaqt oralig'i: '08:00–10:00'."""
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')}"
        return ''

    @property
    def schedule_display(self):
        """To'liq jadval: 'Dush, Chor, Jum · 08:00–10:00'."""
        days = self.weekdays_display
        time = self.time_display
        if days and time:
            return f"{days} · {time}"
        return days or time or ''


class Group(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('frozen',    'Frozen'),
    ]

    name       = models.CharField(max_length=100, verbose_name='Guruh nomi')
    course     = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Kurs',
    )
    teacher    = models.ForeignKey(
        'instructors.Instructor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='groups',
        verbose_name="O'qituvchi",
    )
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='active', verbose_name='Holat',
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Boshlanish')
    end_date   = models.DateField(null=True, blank=True, verbose_name='Tugash')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering    = ['-created_at']
        verbose_name        = 'Guruh'
        verbose_name_plural = 'Guruhlar'

    def __str__(self):
        return f"{self.name} — {self.course}"


# ─── eski Student modeli (courses ichida) ────────────────────────────────────
# Bu model enrollments.Enrollment bilan to'qnashmaydi,
# chunki u 'students.Student' ga emas, Course ga bog'liq.
class Student(models.Model):
    STATUS_CHOICES = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
        ('frozen',   'Frozen'),
    ]

    full_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=30, blank=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    course     = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='students',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

# ─── Enrollment o'chirildi ───────────────────────────────────────────────────
# courses.Enrollment o'chirildi — u enrollments appiga ko'chirilgan.
# related_name to'qnashuvi shu yerda edi.