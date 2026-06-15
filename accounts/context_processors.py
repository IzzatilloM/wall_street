"""Template context processor'lar."""

from django.conf import settings


def google_oauth(request):
    """
    "Google bilan kirish" tugmasini faqat Google Client ID sozlangan bo'lsa
    ko'rsatamiz. Lokalda (kalitsiz) tugma chiqmaydi — ishlamaydigan tugma bo'lmaydi.
    """
    return {
        'google_oauth_enabled': bool(getattr(settings, 'GOOGLE_CLIENT_ID', '')),
        'telegram_bot_username': getattr(settings, 'TELEGRAM_BOT_USERNAME', ''),
    }
