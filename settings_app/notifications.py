"""
Web (Settings) tomondan «Wall Street Technic Bot» orqali foydalanuvchiga
xabar yuborish. Bot alohida jarayon (polling/webhook) bo'lgani uchun,
admin javobini bevosita Telegram Bot API ga sinxron `requests` so'rovi
bilan yuboramiz — bu eng barqaror yo'l.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/sendMessage"


def _token():
    # Texnik bot uchun alohida token; bo'lmasa asosiy botga tushadi.
    return (
        getattr(settings, 'TECHNIC_BOT_TOKEN', '')
        or getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    )


def send_telegram_message(chat_id, text):
    """Berilgan chat_id ga HTML xabar yuboradi. (success: bool)"""
    token = _token()
    if not token or not chat_id:
        return False

    proxy = getattr(settings, 'PROXY_URL', '') or None
    proxies = {'http': proxy, 'https': proxy} if proxy else None

    try:
        resp = requests.post(
            _API.format(token=token),
            json={
                'chat_id': str(chat_id),
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            },
            proxies=proxies,
            timeout=15,
        )
        ok = resp.ok and resp.json().get('ok', False)
        if not ok:
            logger.warning("Telegram sendMessage muvaffaqiyatsiz: %s", resp.text[:300])
        return ok
    except Exception:
        logger.exception("Telegram xabar yuborishda xato")
        return False


def notify_ticket_reply(ticket):
    """Admin javobini murojaat egasiga (Telegramga) yetkazadi."""
    if not ticket.telegram_chat_id or not ticket.admin_reply:
        return False

    status_label = ticket.get_status_display()
    text = (
        "📬 <b>Murojaatingizga javob keldi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>{ticket.code}</b> · {ticket.category_emoji} {ticket.get_category_display()}\n"
        f"📊 Holat: <b>{status_label}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👨‍💻 <b>Texnik xizmat javobi:</b>\n"
        f"<blockquote>{ticket.admin_reply}</blockquote>\n\n"
        "<i>Savol qolsa — botda «🆘 Muammoni bildirish» orqali yana yozing.</i>"
    )
    return send_telegram_message(ticket.telegram_chat_id, text)
