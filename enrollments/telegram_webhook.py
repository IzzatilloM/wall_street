"""
Telegram bot — WEBHOOK kirish nuqtasi.

Bot endi alohida always-on jarayon emas: Telegram update'larni shu Django
view'iga POST qiladi, biz ularni aiogram dispatcher'iga uzatamiz. Shu sabab
bot sayt bilan BITTA jarayonda, BITTA bazada ishlaydi va PythonAnywhere
bepul tarifida ham (always-on task'siz) ishlaydi.

URL:  https://<domeningiz>/tg/webhook/<BOT_TOKEN>/
"""
import asyncio
import json
import sys
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# telegram_bot papkasini import yo'liga qo'shamiz, shunda u yerdagi
# db / config / states / keyboards / bot modullari import bo'la oladi.
_BOT_DIR = Path(settings.BASE_DIR) / "wallstreet" / "telegram_bot"
if str(_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(_BOT_DIR))

_dp = None
_token = None


def _load():
    """bot.py ni bir marta import qiladi — barcha handlerlar dp ga ulanadi."""
    global _dp, _token
    if _dp is None:
        import bot as _bot_module  # noqa: F401  (handlerlar shu importda ro'yxatga olinadi)
        from config import BOT_TOKEN
        _dp = _bot_module.dp
        _token = BOT_TOKEN
    return _dp, _token


async def _feed(dp, token, data):
    # Har bir so'rovda yangi Bot (yangi event loop bilan mos kelishi uchun),
    # so'ng sessiyani yopamiz.
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.feed_raw_update(bot, data)
    finally:
        await bot.session.close()


@csrf_exempt
def telegram_webhook(request, token):
    dp, secret = _load()

    # URL'dagi token bot tokeniga mos kelmasa — rad etamiz (oddiy himoya).
    if token != secret:
        return HttpResponseForbidden("forbidden")

    # Brauzerda ochilsa — tirik ekanini ko'rsatadi.
    if request.method != "POST":
        return HttpResponse("Wall Street bot webhook ✅")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    asyncio.run(_feed(dp, secret, data))
    return JsonResponse({"ok": True})
