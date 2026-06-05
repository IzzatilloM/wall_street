from django.contrib import admin
from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'is_pinned', 'created_at')
    list_filter = ('is_published', 'is_pinned')
    search_fields = ('title', 'short_text', 'body')
    list_editable = ('is_published', 'is_pinned')
    date_hierarchy = 'created_at'
