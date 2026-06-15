"""
Telegram botlar — WEBHOOK kirish nuqtasi (IKKI bot uchun).

Botlar endi alohida always-on jarayon emas: Telegram update'larni shu Django
view'iga POST qiladi, biz ularni mos botning aiogram dispatcher'iga uzatamiz.
Shu sabab botlar sayt bilan BITTA jarayonda, BITTA bazada ishlaydi va Render
bepul tarifida (background worker'siz, Shell'siz) ham ishlaydi.

URL:  https://<domeningiz>/tg/webhook/<BOT_TOKEN>/

Har bir bot o'z tokeni bilan kelgani uchun URL'dagi token bo'yicha qaysi botga
tegishli ekanini aniqlaymiz:
  * TELEGRAM_BOT_TOKEN  → wallstreet/telegram_bot  (asosiy bot)
  * TECHNIC_BOT_TOKEN   → wallstreet/technic_bot   (texnik yordam boti)

Ikkala bot papkasi bir xil nomli modullarni (bot, config, db, ...) ishlatadi.
Bitta Django jarayonida ularni to'qnashtirmaslik uchun har bir botni izolyatsiya
qilingan holda import qilamiz (sys.modules'ni saqlab/tiklab).
"""
import asyncio
import importlib
import json
import logging
import sys
import threading
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("telegram_webhook")

# Ikkala bot papkasi ham aynan shu nomli modullarni o'z ichida saqlaydi. Ikkinchi
# botni import qilishdan oldin birinchisining shu nomli modullarini sys.modules'dan
# vaqtincha olib turamiz — aks holda `import db`, `from config import ...` noto'g'ri
# (birinchi botning) modullariga ulanib qoladi.
_SHARED_NAMES = ("bot", "config", "db", "states", "keyboards", "storage", "django_setup")

# (papka, inson o'qiydigan nom) — import qilinadigan botlar.
_BOTS = (
    ("telegram_bot", "asosiy bot"),
    ("technic_bot", "technic bot"),
)

# token -> {"dp": Dispatcher, "proxy": str | None, "modules": {...}}
_REGISTRY = {}
_LOAD_LOCK = threading.Lock()
_LOADED = False


def _import_bot(folder: str):
    """Bitta bot papkasini izolyatsiyada import qiladi.

    Returns: (dp, token, proxy, modules)
    """
    bot_dir = Path(settings.BASE_DIR) / "wallstreet" / folder

    # Boshqa botdan qolgan, bir xil nomli modullarni vaqtincha chetga olamiz.
    stash = {n: sys.modules.pop(n) for n in _SHARED_NAMES if n in sys.modules}
    sys.path.insert(0, str(bot_dir))
    try:
        bot_module = importlib.import_module("bot")        # handlerlar shu importda ro'yxatga olinadi
        config_module = importlib.import_module("config")

        dp = bot_module.dp
        token = (getattr(config_module, "BOT_TOKEN", "") or "").strip()
        proxy = (getattr(config_module, "PROXY_URL", "") or "").strip() or None

        # Yangi yuklangan modullarga havolani saqlab qolamiz: handlerlar o'z
        # __globals__ (modul lug'ati) orqali shu modullarga bog'langan, ular
        # sys.modules'dan olib tashlansa ham tirik qolishi kerak.
        modules = {n: sys.modules[n] for n in _SHARED_NAMES if n in sys.modules}
        return dp, token, proxy, modules
    finally:
        try:
            sys.path.remove(str(bot_dir))
        except ValueError:
            pass
        # Yangi yuklangan shared modullarni olib tashlab, chetga olinganini tiklaymiz.
        for n in _SHARED_NAMES:
            sys.modules.pop(n, None)
        sys.modules.update(stash)


def _ensure_loaded():
    """Birinchi so'rovda ikkala botni bir marta yuklaydi (token -> dp registratsiyasi)."""
    global _LOADED
    if _LOADED:
        return
    with _LOAD_LOCK:
        if _LOADED:
            return
        for folder, label in _BOTS:
            try:
                dp, token, proxy, modules = _import_bot(folder)
            except Exception:
                logger.exception("Webhook: %s yuklab bo'lmadi", label)
                continue
            if not token:
                logger.warning("Webhook: %s tokeni topilmadi — o'tkazib yuborildi", label)
                continue
            _REGISTRY[token] = {"dp": dp, "proxy": proxy, "modules": modules}
            logger.info("Webhook: %s yuklandi (token ...%s)", label, token[-6:])
        _LOADED = True


async def _feed(dp, token, proxy, data):
    # Har bir so'rovda yangi Bot (yangi event loop bilan mos kelishi uchun),
    # so'ng sessiyani yopamiz.
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.enums import ParseMode

    session = AiohttpSession(proxy=proxy) if proxy else None
    bot = Bot(token=token, session=session,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.feed_raw_update(bot, data)
    finally:
        await bot.session.close()


@csrf_exempt
def telegram_webhook(request, token):
    _ensure_loaded()

    entry = _REGISTRY.get(token)
    # URL'dagi token hech bir botga mos kelmasa — rad etamiz (oddiy himoya).
    if entry is None:
        return HttpResponseForbidden("forbidden")

    # Brauzerda ochilsa — tirik ekanini ko'rsatadi.
    if request.method != "POST":
        return HttpResponse("Wall Street bot webhook ✅")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)

    asyncio.run(_feed(entry["dp"], token, entry["proxy"], data))
    return JsonResponse({"ok": True})
