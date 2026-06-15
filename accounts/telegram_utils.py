

import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    """Ixtiyoriy matnli xabarni Telegram orqali yuboradi (kod, ogohlantirish...)."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')

    if not token:
        return False, "TELEGRAM_BOT_TOKEN settings.py yoki .env ichida topilmadi!"

    if not chat_id:
        return False, "Telegram Chat ID topilmadi!"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    # PythonAnywhere bepul tarifda tashqi internet faqat proxy orqali chiqadi.
    _proxy = getattr(settings, 'PROXY_URL', '') or ''
    proxies = {'http': _proxy, 'https': _proxy} if _proxy else None

    try:
        response = requests.post(url, json=payload, timeout=10, proxies=proxies)
        data = response.json()

        if response.status_code == 200 and data.get("ok"):
            return True, "Xabar Telegram orqali yuborildi!"

        return False, data.get("description", "Telegramga yuborishda xatolik yuz berdi!")
    except Exception as e:
        return False, str(e)


def send_telegram_code(chat_id, code):
    """Ro'yxatdan o'tish / parol tiklash tasdiqlash kodini yuboradi."""
    text = (
        "🏢 Wall Street CRM\n\n"
        f"🔐 Tasdiqlash kodi: {code}\n\n"
        "Ushbu kodni ro'yxatdan o'tish oynasiga kiriting.\n"
        "Kod 5 daqiqa davomida amal qiladi."
    )
    success, msg = send_telegram_message(chat_id, text)
    if success:
        return True, "Kod Telegram orqali yuborildi!"
    return False, msg