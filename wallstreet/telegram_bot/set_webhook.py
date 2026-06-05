"""
Telegram webhook'ni boshqarish (bir martalik buyruqlar).

telegram_bot papkasi ichida turib ishga tushiring:

    python set_webhook.py set https://foydalanuvchi.pythonanywhere.com
    python set_webhook.py info
    python set_webhook.py delete      # webhook'ni o'chiradi (polling'ga qaytish uchun)

«set» — Telegram'ga update'larni saytingizdagi /tg/webhook/<token>/ manziliga
yuborishni buyuradi. Buni domen tayyor bo'lgach BIR MARTA ishga tushirsangiz kifoya.
"""
import asyncio
import sys

from aiogram import Bot

from config import BOT_TOKEN

WEBHOOK_PATH = f"/tg/webhook/{BOT_TOKEN}/"


async def _run():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    bot = Bot(token=BOT_TOKEN)
    try:
        if cmd == "set":
            if len(sys.argv) < 3:
                print("❌ BASE_URL kiriting. Masalan: python set_webhook.py set https://user.pythonanywhere.com")
                return
            base = sys.argv[2].rstrip("/")
            url = f"{base}{WEBHOOK_PATH}"
            await bot.set_webhook(url, drop_pending_updates=True)
            print("✅ Webhook o'rnatildi:")
            print("   ", url)
        elif cmd == "delete":
            await bot.delete_webhook(drop_pending_updates=True)
            print("🗑  Webhook o'chirildi. Endi lokalda 'python bot.py' (polling) ishlaydi.")
        else:  # info
            info = await bot.get_webhook_info()
            print("ℹ️  Webhook holati:")
            print("    URL:", info.url or "(o'rnatilmagan)")
            print("    Kutilayotgan update:", info.pending_update_count)
            if info.last_error_message:
                print("    Oxirgi xato:", info.last_error_message)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(_run())
