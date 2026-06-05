from django.contrib import admin
from .models import CenterSettings


@admin.register(CenterSettings)
class CenterSettingsAdmin(admin.ModelAdmin):
    list_display = ('center_name', 'phone', 'email', 'currency')
