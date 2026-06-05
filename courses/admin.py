from django.contrib import admin
from .models import Course, Student


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'level',
        'teacher',
        'students_count',
        'duration_value',
        'duration_unit',
        'price',
        'is_active',
        'created_at',
    )
    list_filter = ('category', 'level', 'is_active', 'duration_unit', 'created_at')
    search_fields = ('title', 'teacher__full_name', 'description')
    list_select_related = ('teacher', 'teacher__user')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'status', 'course', 'created_at')
    list_filter = ('status', 'course', 'created_at')
    search_fields = ('full_name', 'phone', 'course__title')
    list_select_related = ('course',)