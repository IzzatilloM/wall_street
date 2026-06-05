from django.contrib import admin

from .models import Enrollment, EnrollmentNote, TelegramLead


@admin.register(TelegramLead)
class TelegramLeadAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'status', 'created_at', 'processed_by']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'telegram_username']
    readonly_fields = ['created_at', 'updated_at', 'telegram_chat_id', 'telegram_username']
    date_hierarchy = 'created_at'
