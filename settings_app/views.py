from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CenterSettings, SupportTicket
from .notifications import notify_ticket_reply
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

    # ── Texnik murojaatlar (faqat admin) ──────────────────────────────
    support_tickets = []
    support_counts = {}
    if _is_admin(user):
        support_tickets = list(SupportTicket.objects.all()[:200])
        support_counts = {
            'all':         len(support_tickets),
            'new':         sum(1 for t in support_tickets if t.status == 'new'),
            'in_progress': sum(1 for t in support_tickets if t.status == 'in_progress'),
            'resolved':    sum(1 for t in support_tickets if t.status in ('resolved', 'closed')),
        }

    context = {
        'profile_form': profile_form,
        'center_form': center_form,
        'password_form': password_form,
        'active_tab': active_tab,
        'teacher_users': teacher_users,
        'student_users': student_users,
        'can_manage_users': _is_admin(user),
        'support_tickets': support_tickets,
        'support_counts': support_counts,
        'ticket_status_choices': SupportTicket.STATUS_CHOICES,
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


# ══════════════════════════════════════════════════════════════
#  YORDAM MARKAZI — texnik murojaatlar (Wall Street Technic Bot)
# ══════════════════════════════════════════════════════════════

@login_required
@require_POST
def ticket_update(request, pk):
    """Murojaatga javob yozadi va/yoki holatini o'zgartiradi (faqat admin).

    Javob yozilsa — foydalanuvchining Telegramiga avtomatik yetkaziladi.
    """
    if not _is_admin(request.user):
        messages.error(request, 'You do not have permission for this action.')
        return redirect('settings')

    ticket = get_object_or_404(SupportTicket, pk=pk)

    reply = (request.POST.get('reply') or '').strip()
    new_status = (request.POST.get('status') or ticket.status).strip()
    valid_statuses = dict(SupportTicket.STATUS_CHOICES)
    if new_status not in valid_statuses:
        new_status = ticket.status

    ticket.status = new_status
    if reply:
        ticket.admin_reply = reply

    if new_status in ('resolved', 'closed') and not ticket.resolved_at:
        ticket.resolved_by = request.user
        ticket.resolved_at = timezone.now()
    elif new_status in ('new', 'in_progress'):
        ticket.resolved_at = None
        ticket.resolved_by = None

    ticket.save()

    # Javobni foydalanuvchiga Telegram orqali yuborish
    if reply:
        delivered = notify_ticket_reply(ticket)
        if delivered:
            messages.success(request, f'«{ticket.code}» — javob foydalanuvchiga yuborildi.')
        else:
            messages.warning(
                request,
                f'«{ticket.code}» saqlandi, ammo Telegramga yuborib bo\'lmadi '
                '(token yoki chat ID tekshiring).'
            )
    else:
        messages.success(request, f'«{ticket.code}» holati yangilandi.')

    return redirect('/settings/?tab=support')


@login_required
@require_POST
def ticket_delete(request, pk):
    """Murojaatni o'chiradi (faqat admin)."""
    if not _is_admin(request.user):
        messages.error(request, 'You do not have permission for this action.')
        return redirect('settings')

    ticket = get_object_or_404(SupportTicket, pk=pk)
    code = ticket.code
    ticket.delete()
    messages.success(request, f'«{code}» murojaat o\'chirildi.')
    return redirect('/settings/?tab=support')
