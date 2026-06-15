"""
Wall Street Technic Bot konfiguratsiyasi — barcha qiymatlar .env orqali.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')


def _clean(value: str) -> str:
    return (value or '').strip().strip('"').strip("'")


# ── Bot ──────────────────────────────────────────────
BOT_TOKEN = _clean(os.getenv('TECHNIC_BOT_TOKEN', ''))
BOT_NAME = _clean(os.getenv('TECHNIC_BOT_NAME', 'Wall Street Technic'))
BOT_VERSION = _clean(os.getenv('TECHNIC_BOT_VERSION', '1.0'))
ADMIN_USERNAME = _clean(os.getenv('ADMIN_USERNAME', '@vvall_street_admin'))

# Yangi murojaat haqida ogohlantirish boradigan admin chat ID lari
_raw_admins = _clean(os.getenv('TECHNIC_ADMIN_CHAT_IDS', ''))
ADMIN_CHAT_IDS = [x.strip() for x in _raw_admins.split(',') if x.strip()]

# ── Proxy (PythonAnywhere bepul tarif uchun) ─────────
_auto_proxy = 'http://proxy.server:3128' if (
    os.getenv('PYTHONANYWHERE_DOMAIN') or os.getenv('PYTHONANYWHERE_SITE')
) else ''
PROXY_URL = _clean(os.getenv('PROXY_URL', _auto_proxy))

# ── Platforma havolalari ─────────────────────────────
WEBSITE_URL = _clean(os.getenv('WEBSITE_URL', 'http://127.0.0.1:8000')).rstrip('/')
LOGIN_URL = f"{WEBSITE_URL}/accounts/login/"
RESET_URL = f"{WEBSITE_URL}/accounts/forgot-password/"

SUPPORT_URL = _clean(os.getenv('SUPPORT_URL', 'https://t.me/vvall_street_admin'))
