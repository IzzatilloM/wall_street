"""
Texnik bot uchun Django ORM yordamchilari (async-safe).
"""
import django_setup  # noqa: F401  (Django ni ishga tushiradi)

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from settings_app.models import SupportTicket

User = get_user_model()


# ══════════════════════════════════════════════════════
#  MUROJAAT YARATISH
# ══════════════════════════════════════════════════════
@sync_to_async
def create_ticket(*, category, description, full_name='', phone='', contact='',
                  chat_id='', username='', priority='normal', subject=''):
    """SupportTicket yaratadi va dict qaytaradi (code, id)."""
    ticket = SupportTicket.objects.create(
        category=category,
        description=description.strip(),
        full_name=full_name.strip(),
        phone=phone.strip(),
        contact=contact.strip(),
        telegram_chat_id=str(chat_id),
        telegram_username=username or '',
        priority=priority,
        subject=subject.strip(),
        status='new',
    )
    return {'id': ticket.id, 'code': ticket.code}


@sync_to_async
def get_my_tickets(chat_id, limit=10):
    """Foydalanuvchining oxirgi murojaatlari (dict ro'yxati)."""
    qs = SupportTicket.objects.filter(
        telegram_chat_id=str(chat_id)
    ).order_by('-created_at')[:limit]
    result = []
    for t in qs:
        result.append({
            'code': t.code,
            'emoji': t.category_emoji,
            'category': t.get_category_display(),
            'status': t.get_status_display(),
            'status_key': t.status,
            'priority': t.get_priority_display(),
            'description': t.description,
            'admin_reply': t.admin_reply,
            'created': t.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    return result


@sync_to_async
def get_admin_chat_ids():
    """DB dagi admin foydalanuvchilarning Telegram chat ID lari."""
    ids = (
        User.objects.filter(role='admin')
        .exclude(telegram_chat_id='')
        .exclude(telegram_chat_id__isnull=True)
        .values_list('telegram_chat_id', flat=True)
    )
    return [str(i) for i in ids if i]


@sync_to_async
def get_known_name(chat_id):
    """Agar bu chat ID tizimda ro'yxatdan o'tgan bo'lsa — to'liq ismni qaytaradi."""
    u = User.objects.filter(telegram_chat_id=str(chat_id)).first()
    if u:
        return (u.get_full_name() or u.username or '').strip()
    return ''
