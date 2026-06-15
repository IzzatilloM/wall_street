"""
Telegram webhook'larni boshqarish — IKKI bot uchun (asosiy + technic).

Ishlatish:
    python manage.py tg_webhook set      # WEBSITE_URL bo'yicha webhook o'rnatadi
    python manage.py tg_webhook set --base https://wallstreet-crm.onrender.com
    python manage.py tg_webhook info     # joriy holatni ko'rsatadi (getWebhookInfo)
    python manage.py tg_webhook delete   # webhook'ni o'chiradi (polling'ga qaytish)

Eslatma: server (wsgi.py) ko'tarilganda webhook AVTOMATIK o'rnatiladi. Bu buyruq
qo'lda tekshirish/tuzatish uchun (masalan lokal kompyuterdan Render'ga qaratib).
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

WEBHOOK_PATH = "/tg/webhook/{token}/"
ALLOWED_UPDATES = ["message", "callback_query"]


def _bots():
    return [
        ("asosiy bot", (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()),
        ("technic bot", (getattr(settings, "TECHNIC_BOT_TOKEN", "") or "").strip()),
    ]


class Command(BaseCommand):
    help = "Telegram webhook'larni boshqaradi (set/info/delete) — 2 bot uchun"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["set", "info", "delete"])
        parser.add_argument(
            "--base",
            default=None,
            help="Sayt manzili (default: settings.WEBSITE_URL). Masalan: "
                 "https://wallstreet-crm.onrender.com",
        )

    def handle(self, *args, **opts):
        action = opts["action"]
        base = (opts["base"] or getattr(settings, "WEBSITE_URL", "") or "").rstrip("/")

        for label, token in _bots():
            if not token:
                self.stdout.write(self.style.WARNING(f"⏭  {label}: token yo'q — o'tkazildi"))
                continue
            self.stdout.write(f"\n=== {label} (…{token[-6:]}) ===")
            try:
                if action == "set":
                    self._set(token, base)
                elif action == "delete":
                    self._delete(token)
                else:
                    self._info(token)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"❌ Xato: {e}"))

    def _api(self, token, method, **payload):
        url = f"https://api.telegram.org/bot{token}/{method}"
        r = requests.post(url, json=payload, timeout=20)
        return r.json()

    def _set(self, token, base):
        if not base.startswith("https://"):
            self.stdout.write(self.style.ERROR(
                f"❌ Manzil https:// bo'lishi shart (hozir: {base!r}). "
                "--base bilan bering yoki WEBSITE_URL ni to'g'rilang."
            ))
            return
        hook = base + WEBHOOK_PATH.format(token=token)
        res = self._api(token, "setWebhook", url=hook,
                        drop_pending_updates=True, allowed_updates=ALLOWED_UPDATES)
        if res.get("ok"):
            self.stdout.write(self.style.SUCCESS(f"✅ O'rnatildi: {hook}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {res}"))

    def _delete(self, token):
        res = self._api(token, "deleteWebhook", drop_pending_updates=True)
        if res.get("ok"):
            self.stdout.write(self.style.SUCCESS("🗑  Webhook o'chirildi (polling'ga tayyor)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {res}"))

    def _info(self, token):
        res = self._api(token, "getWebhookInfo")
        info = res.get("result", {}) if res.get("ok") else {}
        url = info.get("url") or "(o'rnatilmagan)"
        self.stdout.write(f"   URL:                 {url}")
        self.stdout.write(f"   Kutilayotgan update: {info.get('pending_update_count', 0)}")
        if info.get("last_error_message"):
            self.stdout.write(self.style.WARNING(
                f"   Oxirgi xato:         {info['last_error_message']}"
            ))
