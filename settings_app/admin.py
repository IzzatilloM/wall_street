from django.contrib import admin
from .models import CenterSettings, SupportTicket


@admin.register(CenterSettings)
class CenterSettingsAdmin(admin.ModelAdmin):
    list_display = ('center_name', 'phone', 'email', 'currency')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'category', 'full_name', 'phone',
                    'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('full_name', 'phone', 'contact', 'description',
                     'telegram_username', 'telegram_chat_id')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    date_hierarchy = 'created_at'
