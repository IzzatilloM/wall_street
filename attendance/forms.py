from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Attendance, Student, Course


class AttendanceForm(forms.ModelForm):
    """Form for marking attendance"""

    class Meta:
        model = Attendance
        fields = ['student', 'course', 'date', 'status', 'note']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes...',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        date = cleaned_data.get('date')

        # Check if date is not in the future
        if date and date > timezone.now().date():
            raise ValidationError("Attendance date cannot be in the future.")

        # Check if student is enrolled in the course
        if student and course:
            if not student.courses.filter(id=course.id).exists():
                raise ValidationError(
                    f"{student.user.get_full_name()} is not enrolled in {course.name}."
                )

        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """Form for bulk marking attendance"""

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        })
    )

    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True,
        })
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError("Attendance date cannot be in the future.")
        return date


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""

    STATUS_CHOICES = [
        ('', 'All Status'),
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or ID...',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError("From date must be before To date.")

        return cleaned_data


class StudentAttendanceReportForm(forms.Form):
    """Form for generating student attendance reports"""

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )


class CourseAttendanceReportForm(forms.Form):
    """Form for generating course attendance reports"""

    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )

    export_format = forms.ChoiceField(
        choices=[
            ('html', 'HTML Report'),
            ('csv', 'CSV File'),
            ('pdf', 'PDF File'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )