"""
Bot konfiguratsiyasi — barcha qiymatlar .env orqali sozlanadi.
Lokalda WEBSITE_URL = http://127.0.0.1:8000 (default).
Hostga qo'yganda .env da WEBSITE_URL ni real domeningizga o'zgartiring.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')


def _clean(value: str) -> str:
    return (value or '').strip().strip('"').strip("'")


# ── Bot ──────────────────────────────────────────────
BOT_TOKEN = _clean(os.getenv('TELEGRAM_BOT_TOKEN', ''))
BOT_NAME = _clean(os.getenv('BOT_NAME', 'Wall Street CRM'))
BOT_VERSION = _clean(os.getenv('BOT_VERSION', '3.0'))
ADMIN_USERNAME = _clean(os.getenv('ADMIN_USERNAME', '@vvall_street_admin'))

# ── Platforma havolalari ─────────────────────────────
WEBSITE_URL = _clean(os.getenv('WEBSITE_URL', 'http://127.0.0.1:8000')).rstrip('/')
LOGIN_URL = f"{WEBSITE_URL}/accounts/login/"
REGISTER_URL = f"{WEBSITE_URL}/accounts/register/"
RESET_URL = f"{WEBSITE_URL}/accounts/forgot-password/"
COURSES_URL = f"{WEBSITE_URL}/courses/"

# ── Ijtimoiy tarmoqlar ───────────────────────────────
SUPPORT_URL = _clean(os.getenv('SUPPORT_URL', 'https://t.me/vvall_street_admin'))
TELEGRAM_CHANNEL = _clean(os.getenv('TELEGRAM_CHANNEL', 'https://t.me/wallstreet_lc'))
INSTAGRAM_URL = _clean(os.getenv('INSTAGRAM_URL', 'https://instagram.com/wallstreetcrm'))
YOUTUBE_URL = _clean(os.getenv('YOUTUBE_URL', 'https://youtube.com/@wallstreetcrm'))
LINKEDIN_URL = _clean(os.getenv('LINKEDIN_URL', 'https://linkedin.com/company/wallstreetcrm'))
