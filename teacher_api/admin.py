from django.contrib import admin

from .models import TeacherProfile, TGroup, TStudent, TAttendance, TAttendanceItem


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'salary_type', 'base_salary', 'rate_per_lesson', 'rate_per_hour')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(TGroup)
class TGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'subject', 'lesson_price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'subject', 'teacher__username')


@admin.register(TStudent)
class TStudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'phone', 'monthly_fee', 'status')
    list_filter = ('status',)
    search_fields = ('full_name', 'phone')


class TAttendanceItemInline(admin.TabularInline):
    model = TAttendanceItem
    extra = 0


@admin.register(TAttendance)
class TAttendanceAdmin(admin.ModelAdmin):
    list_display = ('group', 'teacher', 'lesson_date', 'duration_min', 'created_at')
    list_filter = ('lesson_date',)
    inlines = [TAttendanceItemInline]
