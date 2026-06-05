from django.db import models
import uuid
from instructors.models import Instructor

MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


class SalaryPayment(models.Model):
    MONTH_CHOICES = [(i, name) for i, name in enumerate(MONTH_NAMES, start=1)]
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE, related_name='salary_payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
    paid_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-year', '-month', '-paid_at']
        verbose_name = "Oylik to'lov"
        verbose_name_plural = "Oylik to'lovlar"

    def __str__(self):
        return f"{self.instructor.full_name} - {self.get_month_display()} {self.year}"
