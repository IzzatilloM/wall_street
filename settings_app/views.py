from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import CenterSettings
from .forms import (
    ProfileForm,
    CenterSettingsForm,
    StyledSetPasswordForm,
)

User = get_user_model()


def _is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


def _managed_users():
    """O'qituvchi va talaba foydalanuvchilari (username + ochiq parol bilan)."""
    teachers = User.objects.filter(role='teacher').order_by('first_name', 'username')
    students = User.objects.filter(role='student').order_by('first_name', 'username')
    return teachers, students


@login_required
def settings_view(request):
    user = request.user
    center = CenterSettings.load()

    profile_form = ProfileForm(instance=user)
    center_form = CenterSettingsForm(instance=center)
    password_form = StyledSetPasswordForm(user)
    active_tab = request.GET.get('tab', 'profile')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            active_tab = 'profile'
            profile_form = ProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile information saved.')
                return redirect('settings')

        elif form_type == 'remove_avatar':
            active_tab = 'profile'
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                messages.success(request, 'Profile photo removed.')
            return redirect('settings')

        elif form_type == 'center' and _is_admin(user):
            active_tab = 'center'
            center_form = CenterSettingsForm(request.POST, instance=center)
            if center_form.is_valid():
                center_form.save()
                messages.success(request, 'Center settings saved.')
                return redirect('settings')

        elif form_type == 'password':
            active_tab = 'security'
            password_form = StyledSetPasswordForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                # Ochiq nusxani ham saqlaymiz (sozlamalarda ko'rinishi uchun)
                user.plain_password = password_form.cleaned_data.get('new_password1', '')
                user.save(update_fields=['plain_password'])
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                return redirect('settings')

    teacher_users, student_users = _managed_users()

    context = {
        'profile_form': profile_form,
        'center_form': center_form,
        'password_form': password_form,
        'active_tab': active_tab,
        'teacher_users': teacher_users,
        'student_users': student_users,
        'can_manage_users': _is_admin(user),
    }
    return render(request, 'settings/settings.html', context)


# ══════════════════════════════════════════════════════════════
#  FOYDALANUVCHILARNI BOSHQARISH (o'qituvchi / talaba)
# ══════════════════════════════════════════════════════════════

@login_required
@require_POST
def user_update(request, pk):
    """Username / parol / faollikni yangilaydi (faqat admin)."""
    if not _is_admin(request.user):
        messages.error(request, 'You do not have permission for this action.')
        return redirect('settings')

    target = get_object_or_404(User, pk=pk, role__in=['teacher', 'student'])

    new_username = (request.POST.get('username') or '').strip()
    new_password = (request.POST.get('password') or '').strip()
    is_active = request.POST.get('is_active') in ['on', 'true', '1', 'yes']

    if not new_username:
        messages.error(request, 'Username cannot be empty.')
        return redirect('/settings/?tab=users')

    if User.objects.filter(username=new_username).exclude(pk=target.pk).exists():
        messages.error(request, f'Username «{new_username}» is already taken.')
        return redirect('/settings/?tab=users')

    target.username = new_username
    target.is_active = is_active

    if new_password:
        target.set_password(new_password)
        target.plain_password = new_password

    target.save()

    messages.success(request, f'«{new_username}» login details updated.')
    return redirect('/settings/?tab=users')


@login_required
@require_POST
def user_delete(request, pk):
    """Foydalanuvchini (va bog'liq profilini) o'chiradi (faqat admin)."""
    if not _is_admin(request.user):
        messages.error(request, 'You do not have permission for this action.')
        return redirect('settings')

    target = get_object_or_404(User, pk=pk, role__in=['teacher', 'student'])
    label = target.get_full_name() or target.username
    # OneToOne profillar (Instructor / Student) cascade orqali o'chadi
    target.delete()

    messages.success(request, f'«{label}» has been deleted.')
    return redirect('/settings/?tab=users')
