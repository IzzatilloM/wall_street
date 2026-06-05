from django.conf import settings
from django.db import models


# ════════════════════════════════════════════════════════
#  Instructor Profile
#
#  ⚠️ MUHIM: Bu app ENDI o'zining alohida CustomUser
#  modeliga ega EMAS. Instructor to'g'ridan-to'g'ri
#  loyiha bo'ylab yagona foydalanuvchi modeliga
#  (settings.AUTH_USER_MODEL = 'accounts.CustomUser')
#  bog'lanadi. Shu sababli ro'yxatdan o'tgan barcha
#  teacher/admin lar avtomatik bu yerda ko'rinadi.
# ════════════════════════════════════════════════════════


class Instructor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_profile',
    )
    full_name = models.CharField(max_length=150, default='', blank=True, verbose_name="To'liq ism")
    specialty        = models.CharField(max_length=200, blank=True, default='',
                                        verbose_name="Mutaxassislik")
    experience_years = models.PositiveSmallIntegerField(default=0,
                                                        verbose_name="Tajriba (yil)")
    salary           = models.DecimalField(max_digits=10, decimal_places=2,
                                           default=0, verbose_name="Maosh ($)")
    address          = models.CharField(max_length=255, blank=True, default='',
                                        verbose_name="Manzil")
    bio              = models.TextField(blank=True, default='', verbose_name="Bio")
    is_active        = models.BooleanField(default=True, verbose_name="Faol")
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Instructor'
        verbose_name_plural = 'Instructorlar'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.full_name}  ({self.user.get_role_display()})"

    @property
    def role(self):
        return self.user.role

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email or ''

    @property
    def phone(self):
        return self.user.phone or ''

    def to_json_dict(self):
        return {
            'id':               self.pk,
            'full_name':        self.full_name,
            'specialty':        self.specialty,
            'experience_years': self.experience_years,
            'salary':           float(self.salary),
            'address':          self.address,
            'bio':              self.bio,
            'is_active':        self.is_active,
            'role':             self.user.role,
            'username':         self.user.username,
            'email':            self.user.email or '',
            'phone':            self.user.phone or '',
            'created_at':       self.created_at.strftime('%d.%m.%Y') if self.created_at else '',
        }
