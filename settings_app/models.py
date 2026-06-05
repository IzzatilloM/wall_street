from django.db import models


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
