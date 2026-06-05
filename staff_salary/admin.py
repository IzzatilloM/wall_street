from django.contrib import admin
from .models import SalaryPayment


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'amount', 'month', 'year', 'status', 'paid_at')
    list_filter = ('status', 'year', 'month')
    search_fields = ('instructor__full_name',)
