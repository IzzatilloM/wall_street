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

# ── Telegram botlar (webhook rejimi) ────────────────────────────────────────
# MUHIM: og'ir importni (aiogram) shu yerda — server BOOT paytida, bitta thread'da,
# ketma-ket bajaramiz. Aks holda u birinchi webhook so'rovi ichida bajarilib,
# Render bepul tarifda (cold-start + parallel import) worker'ni timeout/deadlock
# qilardi va 502 berardi. Boot paytida bajarilsa, keyingi so'rovlar yengil bo'ladi.
import logging as _logging
_tg_log = _logging.getLogger("telegram_setup")

# 1) Botlarni oldindan yuklaymiz (token -> dispatcher registratsiyasi).
try:
    from enrollments.telegram_webhook import _ensure_loaded
    _ensure_loaded()
except Exception:  # bot import hech qachon saytni yiqitmasin
    _tg_log.exception("Telegram botlarni oldindan yuklashda xato")

# 2) Webhook'larni Telegram'ga o'rnatamiz (SINXRON, thread'siz — eng xavfsiz).
#    Faqat WEBSITE_URL https:// bo'lsa ishlaydi; lokalda o'tkazib yuboriladi.
try:
    from wallstreet.telegram_setup import set_webhooks_sync
    set_webhooks_sync()
except Exception:  # webhook sozlash hech qachon saytni yiqitmasin
    _tg_log.exception("Telegram webhook o'rnatishda xato")
