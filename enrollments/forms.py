from django import forms
from django.apps import apps

from .models import Enrollment, EnrollmentNote


# ForeignKey fieldlarni lazy queryset bilan qo'lda yaratish uchun helper
def _lazy_fk_field(app_label, model_name, required=True, empty_label="---------"):
    """ModelChoiceField — queryset import vaqtida emas, ishlatganda yuklanadi."""
    class _LazyField(forms.ModelChoiceField):
        def __init__(self, *args, **kwargs):
            # queryset hali bo'sh, __init__ da to'ldiriladi
            super().__init__(queryset=None, *args, **kwargs)

        def get_queryset(self):
            return apps.get_model(app_label, model_name).objects.all()

    field = _LazyField(
        required=required,
        empty_label=empty_label,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    # queryset property ni override qilamiz
    field.__class__.queryset = property(lambda self: self.get_queryset())
    return field


class EnrollmentForm(forms.ModelForm):

    # ForeignKey fieldlar qo'lda — import vaqtida model yuklanmaydi
    student    = _lazy_fk_field('student',     'Student',    required=True)
    course     = _lazy_fk_field('courses',     'Course',     required=False)
    group      = _lazy_fk_field('courses',     'Group',      required=False)
    instructor = _lazy_fk_field('instructors', 'Instructor', required=False)

    class Meta:
        model  = Enrollment
        fields = [
            'student', 'course', 'group', 'instructor',
            'status', 'payment_status',
            'course_fee', 'discount', 'paid_amount',
            'start_date', 'end_date', 'source', 'notes',
        ]
        widgets = {
            'status':         forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'source':         forms.Select(attrs={'class': 'form-select'}),
            'course_fee':  forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'discount':    forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'start_date':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        course_fee  = cleaned_data.get('course_fee')  or 0
        discount    = cleaned_data.get('discount')    or 0
        paid_amount = cleaned_data.get('paid_amount') or 0
        start_date  = cleaned_data.get('start_date')
        end_date    = cleaned_data.get('end_date')

        if discount > course_fee:
            self.add_error('discount', "Chegirma kurs narxidan katta bo'lishi mumkin emas.")
        if paid_amount > (course_fee - discount):
            self.add_error('paid_amount', "To'langan summa sof narxdan katta bo'lishi mumkin emas.")
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas.")
        return cleaned_data


class EnrollmentUpdateForm(forms.ModelForm):

    group      = _lazy_fk_field('courses',     'Group',      required=False)
    instructor = _lazy_fk_field('instructors', 'Instructor', required=False)

    class Meta:
        model  = Enrollment
        fields = [
            'group', 'instructor',
            'status', 'payment_status',
            'course_fee', 'discount', 'paid_amount',
            'start_date', 'end_date', 'source', 'notes',
        ]
        widgets = {
            'status':         forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'source':         forms.Select(attrs={'class': 'form-select'}),
            'course_fee':  forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'discount':    forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'start_date':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        course_fee  = cleaned_data.get('course_fee')  or 0
        discount    = cleaned_data.get('discount')    or 0
        paid_amount = cleaned_data.get('paid_amount') or 0
        start_date  = cleaned_data.get('start_date')
        end_date    = cleaned_data.get('end_date')

        if discount > course_fee:
            self.add_error('discount', "Chegirma kurs narxidan katta bo'lishi mumkin emas.")
        if paid_amount > (course_fee - discount):
            self.add_error('paid_amount', "To'langan summa sof narxdan katta bo'lishi mumkin emas.")
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas.")
        return cleaned_data


class EnrollmentNoteForm(forms.ModelForm):

    class Meta:
        model  = EnrollmentNote
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Izohingizni kiriting...',
            }),
        }
        labels = {'text': 'Izoh'}