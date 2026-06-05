

import requests
from django.conf import settings


def send_telegram_code(chat_id, code):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')

    if not token:
        return False, "TELEGRAM_BOT_TOKEN settings.py yoki .env ichida topilmadi!"

    if not chat_id:
        return False, "Telegram Chat ID topilmadi!"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    text = (
        "🏢 Wall Street CRM\n\n"
        f"🔐 Tasdiqlash kodi: {code}\n\n"
        "Ushbu kodni ro'yxatdan o'tish oynasiga kiriting.\n"
        "Kod 5 daqiqa davomida amal qiladi."
    )

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get("ok"):
            return True, "Kod Telegram orqali yuborildi!"

        return False, data.get("description", "Telegramga yuborishda xatolik yuz berdi!")
    except Exception as e:
        return False, str(e)