from django import forms
from .models import SalaryPayment


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['instructor', 'amount', 'month', 'year', 'status', 'note']
        widgets = {
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'month': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2026'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Note (optional)'}),
        }
        labels = {
            'instructor': 'Teacher',
            'amount': 'Amount (UZS)',
            'month': 'Month',
            'year': 'Year',
            'status': 'Status',
            'note': 'Note',
        }
