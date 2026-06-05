from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'first_name',
        'last_name',
        'phone',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'gender', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email')