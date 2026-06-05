from datetime import date

from django.db import models
from django.conf import settings          # ← User o'rniga settings import qilindi
from django.utils import timezone
from django.db.models import Q


class Course(models.Model):
    """Course model"""

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,          # ← User → settings.AUTH_USER_MODEL
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses_taught'
    )

    total_sessions = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Courses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_total_sessions(self):
        return self.attendances.values('date').distinct().count()


class Student(models.Model):
    """Student model"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_student_profile'  # ← unique nom
    )

    student_id = models.CharField(max_length=50, unique=True)

    courses = models.ManyToManyField(
        Course,
        related_name='students'
    )

    enrollment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Students"
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.student_id})"

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def crm_student(self):
        """students.Student profili (coin balansi shu yerda saqlanadi)."""
        from students.models import Student as CRMStudent
        return CRMStudent.objects.filter(user=self.user).first()

    @property
    def coin_balance(self):
        crm = self.crm_student
        return crm.coins if crm else 0


class Attendance(models.Model):
    """Attendance model"""

    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    date = models.DateField(default=date.today)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present'
    )

    note = models.TextField(blank=True, null=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,          # ← User → settings.AUTH_USER_MODEL
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_marked'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Attendances"
        unique_together = ('student', 'course', 'date')
        ordering = ['-date', 'student__user__first_name']
        indexes = [
            models.Index(fields=['student', 'course']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return (
            f"{self.student.get_full_name()} - "
            f"{self.course.code} - "
            f"{self.date} - "
            f"{self.get_status_display()}"
        )

    @property
    def course_attendance_percent(self):
        total_classes = Attendance.objects.filter(
            student=self.student,
            course=self.course
        ).count()

        if total_classes == 0:
            return 0

        attended_classes = Attendance.objects.filter(
            student=self.student,
            course=self.course
        ).filter(
            Q(status='present') | Q(status='late')
        ).count()

        return round((attended_classes / total_classes) * 100, 1)

    @property
    def course_attendance_percent_rounded(self):
        return int(self.course_attendance_percent)

    @staticmethod
    def get_student_course_attendance(student, course):
        total_classes = Attendance.objects.filter(
            student=student, course=course
        ).count()

        if total_classes == 0:
            return 0

        attended_classes = Attendance.objects.filter(
            student=student, course=course
        ).filter(
            Q(status='present') | Q(status='late')
        ).count()

        return round((attended_classes / total_classes) * 100, 1)

    @staticmethod
    def get_course_attendance_stats(course, attendance_date=None):
        if attendance_date:
            records = Attendance.objects.filter(course=course, date=attendance_date)
        else:
            records = Attendance.objects.filter(course=course)

        total = records.count()

        if total == 0:
            return {
                'total_students': 0,
                'present': 0, 'absent': 0, 'late': 0,
                'present_percent': 0, 'absent_percent': 0, 'late_percent': 0,
            }

        present_count = records.filter(status='present').count()
        absent_count  = records.filter(status='absent').count()
        late_count    = records.filter(status='late').count()

        return {
            'total_students': total,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'present_percent': round((present_count / total) * 100, 1),
            'absent_percent':  round((absent_count  / total) * 100, 1),
            'late_percent':    round((late_count    / total) * 100, 1),
        }

    @staticmethod
    def get_student_overall_attendance(student):
        all_records = Attendance.objects.filter(student=student)
        total = all_records.count()

        if total == 0:
            return {
                'total_classes': 0, 'attended': 0,
                'absent': 0, 'late': 0, 'attendance_percent': 0,
            }

        attended = all_records.filter(Q(status='present') | Q(status='late')).count()
        absent   = all_records.filter(status='absent').count()
        late     = all_records.filter(status='late').count()

        return {
            'total_classes': total,
            'attended': attended,
            'absent': absent,
            'late': late,
            'attendance_percent': round((attended / total) * 100, 1),
        }


class CoinAward(models.Model):
    """
    Talabaga berilgan (yoki ayirilgan) coinlar tarixi.
    Har bir award students.Student.coins balansini yangilaydi.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='coin_awards',
    )
    amount = models.IntegerField(
        default=0,
        help_text="Musbat — qo'shish, manfiy — ayirish",
    )
    reason = models.CharField(max_length=255, blank=True)

    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='coin_awards_given',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coin award'
        verbose_name_plural = 'Coin awards'

    def __str__(self):
        return f"{self.student} : {self.amount:+d} coin"