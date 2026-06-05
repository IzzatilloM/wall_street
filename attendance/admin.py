from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Attendance, Student, Course, CoinAward


@admin.register(CoinAward)
class CoinAwardAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'reason', 'awarded_by', 'created_at']
    list_filter = ['created_at', 'awarded_by']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'reason']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'instructor', 'student_count', 'total_sessions']
    list_filter = ['created_at', 'instructor']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_total_sessions']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'instructor')
        }),
        ('Statistics', {
            'fields': ('total_sessions', 'get_total_sessions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_count(self, obj):
        count = obj.students.count()
        return format_html(
            '<span style="background-color: #0A4548; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            count
        )
    student_count.short_description = 'Students'

    def get_total_sessions(self, obj):
        return obj.get_total_sessions()
    get_total_sessions.short_description = 'Total Sessions'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'get_full_name', 'enrollment_date', 'course_count']
    list_filter = ['enrollment_date', 'courses']
    search_fields = ['student_id', 'user__first_name', 'user__last_name', 'user__email']
    filter_horizontal = ['courses']
    readonly_fields = ['enrollment_date', 'get_full_name']

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

    def course_count(self, obj):
        count = obj.courses.count()
        return format_html(
            '<span style="background-color: #0E5C60; color: white; padding: 4px 8px; border-radius: 4px;">{}</span>',
            count
        )
    course_count.short_description = 'Enrolled Courses'

    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'student_id', 'get_full_name')
        }),
        ('Enrollment', {
            'fields': ('courses', 'enrollment_date')
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_name', 'date', 'status_badge', 'marked_by', 'updated_at']
    list_filter = ['status', 'date', 'course', 'student']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'get_course_attendance_percent', 'get_attendance_stats']
    date_hierarchy = 'date'

    fieldsets = (
        ('Attendance Record', {
            'fields': ('student', 'course', 'date', 'status')
        }),
        ('Additional Information', {
            'fields': ('note', 'marked_by')
        }),
        ('Statistics', {
            'fields': ('get_course_attendance_percent', 'get_attendance_stats'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'

    def course_name(self, obj):
        return f"{obj.course.code} - {obj.course.name}"
    course_name.short_description = 'Course'

    def status_badge(self, obj):
        colors = {
            'present': '#10b981',
            'absent': '#ef4444',
            'late': '#f59e0b',
        }
        color = colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 6px 12px; border-radius: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def get_course_attendance_percent(self, obj):
        percent = obj.course_attendance_percent
        return format_html(
            '<strong>{:.1f}%</strong>',
            percent
        )
    get_course_attendance_percent.short_description = 'Course Attendance %'

    def get_attendance_stats(self, obj):
        stats = Attendance.get_course_attendance_stats(obj.course)
        return format_html(
            '<strong>Present:</strong> {} | <strong>Absent:</strong> {} | <strong>Late:</strong> {}',
            stats['present'],
            stats['absent'],
            stats['late']
        )
    get_attendance_stats.short_description = 'Course Stats'

    actions = ['mark_as_present', 'mark_as_absent', 'mark_as_late']

    def mark_as_present(self, request, queryset):
        updated = queryset.update(status='present')
        self.message_user(request, f'{updated} attendance record(s) marked as Present.')
    mark_as_present.short_description = "Mark as Present"

    def mark_as_absent(self, request, queryset):
        updated = queryset.update(status='absent')
        self.message_user(request, f'{updated} attendance record(s) marked as Absent.')
    mark_as_absent.short_description = "Mark as Absent"

    def mark_as_late(self, request, queryset):
        updated = queryset.update(status='late')
        self.message_user(request, f'{updated} attendance record(s) marked as Late.')
    mark_as_late.short_description = "Mark as Late"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('student', 'student__user', 'course', 'marked_by')

    class Media:
        css = {
            'all': ('admin/css/attendance_admin.css',)
        }