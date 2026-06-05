from django import forms
from .models import Course, Student


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title',
            'category',
            'level',
            'teacher',
            'duration_value',
            'duration_unit',
            'price',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: IELTS Intensive'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duration_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Davomiylik soni'
            }),
            'duration_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0,
                'placeholder': 'Narxi'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-textarea',
                'rows': 4,
                'placeholder': 'Kurs haqida batafsil ma’lumot...'
            }),
        }


class StudentMoveForm(forms.Form):
    new_course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Yangi kurs"
    )

    def __init__(self, *args, **kwargs):
        current_course = kwargs.pop('current_course', None)
        super().__init__(*args, **kwargs)
        qs = Course.objects.all().order_by('title')
        if current_course:
            qs = qs.exclude(id=current_course.id)
        self.fields['new_course'].queryset = qs


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'phone', 'status', 'course']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }