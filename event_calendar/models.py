# models.py - Optional database models uchun

from django.db import models
from django.conf import settings
from datetime import date


class CustomEvent(models.Model):
    """
    User tomonidan qo'shilgan maxsus eventlar
    """

    EVENT_TYPES = [
        ('task', 'Task - Vazifa'),
        ('exam', 'Exam - Imtihon'),
        ('meeting', 'Meeting - Uchrashuv'),
        ('study', 'Study Session - O\'qish sessiyasi'),
        ('break', 'Break - Dam'),
        ('other', 'Other - Boshqa'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    event_date = models.DateField()

    start_time = models.TimeField(
        null=True,
        blank=True
    )

    end_time = models.TimeField(
        null=True,
        blank=True
    )

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default='other'
    )

    color = models.CharField(
        max_length=20,
        default='blue'
    )

    is_important = models.BooleanField(default=False)

    is_all_day = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_date', 'start_time']

        indexes = [
            models.Index(fields=['user', 'event_date']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.event_date}"


class EventReminder(models.Model):
    """
    Event uchun xabar va reminder lar
    """

    REMINDER_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    event = models.ForeignKey(
        CustomEvent,
        on_delete=models.CASCADE,
        related_name='reminders'
    )

    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPES
    )

    minutes_before = models.IntegerField(default=15)

    is_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder: {self.event.title} ({self.reminder_type})"


class EventAttendee(models.Model):
    """
    Event ga ishtirok etayotgan odamlar
    """

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qildi'),
        ('declined', 'Rad qildi'),
    ]

    event = models.ForeignKey(
        CustomEvent,
        on_delete=models.CASCADE,
        related_name='attendees'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"


class CalendarNotification(models.Model):
    """
    User uchun notification lar
    """

    NOTIFICATION_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_notifications'
    )

    event = models.ForeignKey(
        CustomEvent,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"