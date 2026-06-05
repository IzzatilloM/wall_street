"""
Telegram arizalari (TelegramLead) bo'yicha dashboard notification uchun
global context. Faqat admin foydalanuvchilarga ko'rsatiladi.
"""
from .models import TelegramLead


def telegram_leads(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    # Faqat admin / staff foydalanuvchilar arizalarni ko'radi
    role = getattr(user, 'role', None)
    if role != 'admin' and not user.is_staff:
        return {}

    try:
        qs = TelegramLead.objects.filter(status='new').order_by('-created_at')
        leads = list(qs[:15])
        count = qs.count()
    except Exception:
        leads = []
        count = 0

    return {
        'tg_leads': leads,
        'tg_leads_count': count,
    }
