# admin.py - Django Admin configurations

from django.contrib import admin
from .models import CustomEvent, EventReminder, EventAttendee, CalendarNotification


@admin.register(CustomEvent)
class CustomEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event_date', 'event_type', 'is_important', 'created_at')
    list_filter = ('event_type', 'event_date', 'is_important', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'event_date'

    fieldsets = (
        ('Asosiy Ma\'lumotlar', {
            'fields': ('user', 'title', 'description', 'event_type', 'color')
        }),
        ('Vaqt', {
            'fields': ('event_date', 'start_time', 'end_time', 'is_all_day')
        }),
        ('Statusi', {
            'fields': ('is_important',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'reminder_type', 'minutes_before', 'is_sent', 'created_at')
    list_filter = ('reminder_type', 'is_sent', 'created_at')
    search_fields = ('event__title',)

    fieldsets = (
        ('Event', {
            'fields': ('event',)
        }),
        ('Reminder Settings', {
            'fields': ('reminder_type', 'minutes_before', 'is_sent')
        }),
    )


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'responded_at')
    list_filter = ('status', 'responded_at')
    search_fields = ('user__username', 'event__title')

    fieldsets = (
        ('Event Info', {
            'fields': ('event', 'user')
        }),
        ('Status', {
            'fields': ('status', 'responded_at')
        }),
    )


@admin.register(CalendarNotification)
class CalendarNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification', {
            'fields': ('title', 'message', 'notification_type', 'event')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
    )

    readonly_fields = ('created_at',)