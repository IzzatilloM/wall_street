from django import forms
from .models import Instructor

class InstructorUpdateForm(forms.ModelForm):

    class Meta:
        model  = Instructor
        fields = [
            'full_name',
            'specialty',
            'experience_years',
            'salary',
            'address',
            'bio',
            'is_active',
        ]
        error_messages = {
            'full_name': {'required': "To'liq ism majburiy."},
        }

    def clean_experience_years(self):
        val = self.cleaned_data.get('experience_years')
        return val if val is not None else 0

    def clean_salary(self):
        val = self.cleaned_data.get('salary')
        return val if val is not None else 0