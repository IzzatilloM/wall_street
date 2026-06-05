from django import forms
from django.contrib.auth.forms import SetPasswordForm
from accounts.models import CustomUser
from .models import CenterSettings


class StyledSetPasswordForm(SetPasswordForm):
    """Set a brand new password – no current password required."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'new_password1': 'New password',
            'new_password2': 'Confirm new password',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'ws-input'})
            if name in labels:
                field.label = labels[name]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'ws-input'}),
            'last_name': forms.TextInput(attrs={'class': 'ws-input'}),
            'email': forms.EmailInput(attrs={'class': 'ws-input'}),
            'phone': forms.TextInput(attrs={'class': 'ws-input'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'ws-file', 'accept': 'image/*'}),
        }
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email',
            'phone': 'Phone',
            'avatar': 'Profile photo',
        }


class CenterSettingsForm(forms.ModelForm):
    class Meta:
        model = CenterSettings
        fields = ['center_name', 'address', 'phone', 'email', 'currency']
        widgets = {
            'center_name': forms.TextInput(attrs={'class': 'ws-input'}),
            'address': forms.TextInput(attrs={'class': 'ws-input'}),
            'phone': forms.TextInput(attrs={'class': 'ws-input'}),
            'email': forms.EmailInput(attrs={'class': 'ws-input'}),
            'currency': forms.TextInput(attrs={'class': 'ws-input'}),
        }
        labels = {
            'center_name': 'Center name',
            'address': 'Address',
            'phone': 'Phone',
            'email': 'Email',
            'currency': 'Currency',
        }
