"""
WSGI config for wallstreet project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wallstreet.settings')

application = get_wsgi_application()

# Web server ko'tarilganda Telegram webhook'larini avtomatik o'rnatadi
# (Render bepul tarifda Shell yo'q). Faqat WEBSITE_URL https:// bo'lsa ishlaydi;
# lokalda (http://) o'tkazib yuboriladi. Fon thread'ida — bootni bloklamaydi.
try:
    from wallstreet.telegram_setup import auto_set_webhooks
    auto_set_webhooks()
except Exception:  # webhook sozlash hech qachon server ishini buzmasin
    import logging
    logging.getLogger("telegram_setup").exception("auto_set_webhooks ishga tushmadi")
