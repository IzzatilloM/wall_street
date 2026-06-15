"""
«Yordam markazi» — texnik murojaatlar (SupportTicket) bo'yicha global context.
Faqat admin / staff foydalanuvchilarga ochiq murojaatlar sonini beradi
(Settings tab dagi badge va sidebar belgisi uchun).
"""
from .models import SupportTicket


def support_tickets(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    role = getattr(user, 'role', None)
    if role != 'admin' and not user.is_staff:
        return {}

    try:
        count = SupportTicket.objects.filter(status__in=['new', 'in_progress']).count()
    except Exception:
        count = 0

    return {'support_open_count': count}
