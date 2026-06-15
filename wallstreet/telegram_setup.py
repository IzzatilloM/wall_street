"""
Telegram webhook'larni server (gunicorn) ishga tushganda AVTOMATIK o'rnatadi.

Render bepul tarifda Shell (terminal) berilmaydi — shu sabab webhook'ni qo'lda
ro'yxatdan o'tkazib bo'lmaydi. Bu modul web server ko'tarilganda Telegram'ga
`setWebhook` so'rovini o'zi yuboradi.

Faqat WEBSITE_URL `https://...` bo'lsa ishlaydi (lokalda http:// — o'tkazib
yuboriladi, lokalda polling ishlayveradi). Tarmoq so'rovi alohida thread'da
bajariladi — server ishga tushishini sekinlashtirmaydi.

Faqat `wallstreet/wsgi.py` (web server) tomonidan chaqiriladi; `manage.py
migrate` / `collectstatic` (build bosqichi) buni ishga tushirmaydi.
"""
import logging
import threading

logger = logging.getLogger("telegram_setup")

_WEBHOOK_PATH = "/tg/webhook/{token}/"
# Bot handlerlari faqat shu turdagi update'larni ishlatadi.
_ALLOWED_UPDATES = ["message", "callback_query"]


def _set_one(token: str, base_url: str, label: str):
    import requests  # lokal import — modul yuklanishini yengillashtiradi

    hook = base_url.rstrip("/") + _WEBHOOK_PATH.format(token=token)
    api = f"https://api.telegram.org/bot{token}/setWebhook"
    try:
        resp = requests.post(
            api,
            json={
                "url": hook,
                "drop_pending_updates": True,
                "allowed_updates": _ALLOWED_UPDATES,
            },
            timeout=15,
        )
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.ok and body.get("ok"):
            logger.info("✅ Telegram webhook o'rnatildi (%s): %s", label, hook)
        else:
            logger.error("❌ Webhook o'rnatishda xato (%s): %s", label, resp.text[:300])
    except Exception:
        logger.exception("❌ Webhook so'rovida xato (%s)", label)


def set_webhooks_sync():
    """Webhook'larni SINXRON o'rnatadi (boot paytida, thread'siz — eng xavfsiz)."""
    from django.conf import settings

    base = (getattr(settings, "WEBSITE_URL", "") or "").strip()
    if not base.startswith("https://"):
        logger.info(
            "WEBSITE_URL https emas (%r) — webhook o'rnatilmadi (lokal/polling rejim).",
            base,
        )
        return

    bots = [
        ((getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip(), "asosiy bot"),
        ((getattr(settings, "TECHNIC_BOT_TOKEN", "") or "").strip(), "technic bot"),
    ]
    for token, label in bots:
        if token:
            _set_one(token, base, label)
        else:
            logger.info("Webhook: %s tokeni yo'q — o'tkazib yuborildi", label)


def auto_set_webhooks():
    """Webhook'larni fon thread'ida o'rnatadi (boshqaruv buyrug'i/eski chaqiruvlar uchun)."""
    threading.Thread(target=set_webhooks_sync, name="tg-webhook-setup", daemon=True).start()
