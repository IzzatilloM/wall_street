from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number', 'student', 'course', 'instructor',
        'amount', 'discount', 'payment_month', 'payment_year',
        'payment_method', 'status', 'paid_at',
    )
    list_filter  = ('status', 'payment_method', 'payment_year', 'payment_month')
    search_fields= ('receipt_number', 'student__first_name', 'student__last_name',
                    'course__name')
    readonly_fields = ('receipt_number', 'created_at', 'updated_at')
    date_hierarchy   = 'paid_at'
    ordering         = ('-paid_at',)
