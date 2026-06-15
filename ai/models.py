from django.conf import settings
from django.db import models


class AILog(models.Model):
    """
    Har bir Claude API chaqiruvi shu yerga yoziladi (texnik talab:
    "Har bir AI chaqiruv natijasini DB ga log qiling").
    """

    FEATURE_CHOICES = [
        ('churn',             'Talaba churn bashorati'),
        ('instructor_report', "O'qituvchi samaradorlik hisoboti"),
        ('course_recommend',  'Kurs tavsiyasi'),
    ]

    feature        = models.CharField(max_length=40, choices=FEATURE_CHOICES,
                                      verbose_name='Funksiya')
    # Qaysi obyekt uchun chaqirilgani: masalan "student:12", "instructor:3"
    related_object = models.CharField(max_length=120, blank=True, default='')
    model_name     = models.CharField(max_length=80, blank=True, default='',
                                      verbose_name='AI model')
    prompt         = models.TextField(blank=True, default='', verbose_name='Yuborilgan prompt')
    response       = models.TextField(blank=True, default='', verbose_name='AI javobi')
    success        = models.BooleanField(default=False, verbose_name='Muvaffaqiyatli')
    error          = models.TextField(blank=True, default='', verbose_name='Xatolik')
    input_tokens   = models.PositiveIntegerField(default=0)
    output_tokens  = models.PositiveIntegerField(default=0)
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_logs',
        verbose_name='Chaqirgan foydalanuvchi',
    )
    created_at     = models.DateTimeField(auto_now_add=True, verbose_name='Vaqt')

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'AI log'
        verbose_name_plural = 'AI loglar'
        indexes = [
            models.Index(fields=['feature', '-created_at']),
        ]

    def __str__(self):
        status = '✓' if self.success else '✗'
        return f"[{status}] {self.get_feature_display()} — {self.related_object}"
