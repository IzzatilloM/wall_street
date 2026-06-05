from django.db import models
from django.utils import timezone


class News(models.Model):
    """Mobil ilova uchun yangiliklar / e'lonlar."""

    title = models.CharField(max_length=200, verbose_name='Sarlavha')
    short_text = models.CharField(
        max_length=300, blank=True,
        verbose_name='Qisqa matn',
    )
    body = models.TextField(verbose_name='Matn')
    image = models.ImageField(
        upload_to='news/', blank=True, null=True,
        verbose_name='Rasm',
    )
    telegram_url = models.URLField(
        blank=True, null=True,
        verbose_name='Telegram havola',
    )
    is_published = models.BooleanField(default=True, verbose_name='Chop etilgan')
    is_pinned = models.BooleanField(default=False, verbose_name='Tepaga qadalgan')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Sana')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Yangilik'
        verbose_name_plural = 'Yangiliklar'

    def __str__(self):
        return self.title
