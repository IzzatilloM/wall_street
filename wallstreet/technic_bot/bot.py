"""
🛠 Wall Street Technic Bot — texnik yordam boti.

Texnik nosozliklar, parolni tiklash va boshqa murojaatlarni qabul qiladi,
ularni bazaga (settings_app.SupportTicket) yozadi va adminlarga xabar beradi.
Murojaatlar Settings → «Yordam markazi» bo'limida ko'rinadi; admin javobi
foydalanuvchining shu botiga avtomatik qaytadi.
"""
import asyncio
import logging
import re

import db  # ← Django ni bootstrap qiladi + ORM helperlar
from db import create_ticket, get_my_tickets, get_admin_chat_ids, get_known_name

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext

from storage import DjangoFSMStorage
from config import BOT_TOKEN, BOT_NAME, BOT_VERSION, ADMIN_USERNAME, ADMIN_CHAT_IDS, PROXY_URL
from states import NewTicket, PasswordReset
from keyboards import (
    main_menu, cancel_kb, contact_request_kb,
    category_inline, priority_inline, attachment_inline,
    confirm_inline, success_inline, pwd_confirm_inline,
    faq_inline, admin_inline, about_inline, back_to_main_inline,
    CATEGORY_BUTTONS,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("technic_bot")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if not BOT_TOKEN:
    raise RuntimeError(
        "TECHNIC_BOT_TOKEN topilmadi! .env faylga TECHNIC_BOT_TOKEN=... qo'shing."
    )

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
bot = Bot(token=BOT_TOKEN, session=_session,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=DjangoFSMStorage())

DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Yorliqlar ─────────────────────────────────────────
CATEGORY_LABELS = dict(CATEGORY_BUTTONS)  # "login" → "🚪 Tizimga kira olmayapman"
PRIORITY_LABELS = {
    'low': "🟢 Past", 'normal': "🟡 O'rta",
    'high': "🟠 Yuqori", 'urgent': "🔴 Shoshilinch",
}

# Telegram standart xabar effektlari (faqat shaxsiy chatda ishlaydi)
FX_PARTY = "5046509860389126442"   # 🎉
FX_FIRE = "5104841245755180586"    # 🔥
FX_LIKE = "5107584321108051014"    # 👍


# ════════════════════════════════════════════════════
#          ANIMATSIYA / EFFEKT YORDAMCHILARI
# ════════════════════════════════════════════════════
async def typing(chat_id, secs: float = 0.5):
    """«yozmoqda...» animatsiyasi."""
    try:
        await bot.send_chat_action(chat_id, "typing")
        await asyncio.sleep(secs)
    except Exception:
        pass


async def answer_fx(message: Message, text: str, reply_markup=None, effect: str | None = None):
    """Xabarni effekt bilan yuboradi; effekt qo'llab-quvvatlanmasa — oddiy yuboradi."""
    if effect:
        try:
            return await message.answer(text, reply_markup=reply_markup, message_effect_id=effect)
        except Exception:
            pass
    return await message.answer(text, reply_markup=reply_markup)


async def progress_bar(message: Message, label: str = "Yuborilmoqda"):
    """To'lib boradigan progress animatsiyasi (xabarni tahrirlash orqali)."""
    frames = ["▱▱▱▱▱", "▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]
    msg = await message.answer(f"⏳ <b>{label}…</b>\n<code>{frames[0]}</code>  0%")
    pct = [0, 20, 40, 60, 80, 100]
    for i, fr in enumerate(frames[1:], 1):
        await asyncio.sleep(0.22)
        try:
            await msg.edit_text(f"⏳ <b>{label}…</b>\n<code>{fr}</code>  {pct[i]}%")
        except Exception:
            pass
    return msg


def normalize_phone(raw: str):
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("998") and len(digits) == 12:
        digits = digits[3:]
    if len(digits) == 9 and digits.isdigit():
        return digits
    return None


# ════════════════════════════════════════════════════
#                  /start
# ════════════════════════════════════════════════════
@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    full_name = message.from_user.full_name

    loading = await message.answer("⏳")
    await asyncio.sleep(0.5)
    await loading.delete()

    text = (
        f"🛠 <b>{BOT_NAME.upper()} — TEXNIK YORDAM</b>\n"
        f"{DIV}\n"
        f"👋 Assalomu alaykum, <b>{full_name}</b>!\n\n"
        "Men — <b>Wall Street</b> platformasining\n"
        "rasmiy <b>texnik yordam</b> botiman. 🤖\n\n"
        "╔══════════════════════════╗\n"
        "║   🆘  <b>NIMADA YORDAM KERAK?</b>  ║\n"
        "╚══════════════════════════╝\n\n"
        "  🔑  Parolni unutdingizmi?\n"
        "  🚪  Tizimga kira olmayapsizmi?\n"
        "  💳  To'lov bilan muammomi?\n"
        "  🐞  Saytda xatolik chiqdimi?\n\n"
        f"{DIV}\n"
        "📨 Murojaatingiz to'g'ridan-to'g'ri\n"
        "<b>administratorga</b> yetkaziladi va\n"
        "javob shu botga qaytariladi.\n\n"
        "⬇️ <b>Quyidagi bo'limni tanlang:</b>"
    )
    await message.answer(text, reply_markup=main_menu)


# ════════════════════════════════════════════════════
#          BEKOR QILISH (har qanday holatda)
# ════════════════════════════════════════════════════
@dp.message(F.text == "❌ Bekor qilish")
async def cancel_any(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.clear()
    await message.answer(
        "❌ Murojaat bekor qilindi.\n\n🏠 Asosiy menyu:",
        reply_markup=main_menu,
    )


@dp.callback_query(F.data == "t_cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer("❌ Bekor qilindi")
    await state.clear()
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu)


# ════════════════════════════════════════════════════
#          🆘 YANGI MUROJAAT (FSM)
# ════════════════════════════════════════════════════
async def _begin_ticket(target: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewTicket.category)
    await typing(target.chat.id, 0.4)
    await target.answer(
        "🆘 <b>YANGI MUROJAAT</b>\n"
        f"{DIV}\n"
        "1️⃣ Muammo qaysi bo'limga tegishli?\n\n"
        "<i>Quyidagidan birini tanlang:</i>",
        reply_markup=category_inline(),
    )


@dp.message(F.text == "🆘  Muammoni bildirish")
async def btn_new_ticket(message: Message, state: FSMContext):
    await _begin_ticket(message, state)


@dp.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    await _begin_ticket(message, state)


@dp.callback_query(F.data == "new_ticket")
async def cb_new_ticket(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🆘 Yangi murojaat")
    await _begin_ticket(callback.message, state)


# ── 1) Kategoriya tanlandi ──
@dp.callback_query(F.data.startswith("cat_"), NewTicket.category)
async def cb_category(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_", 1)[1]
    if key not in CATEGORY_LABELS:
        await callback.answer("Noma'lum kategoriya", show_alert=True)
        return
    await callback.answer(CATEGORY_LABELS[key])
    await state.update_data(category=key)
    await state.set_state(NewTicket.description)
    await typing(callback.message.chat.id, 0.3)
    await callback.message.answer(
        f"✅ Bo'lim: <b>{CATEGORY_LABELS[key]}</b>\n"
        f"{DIV}\n"
        "2️⃣ Endi muammoni <b>batafsil</b> yozing.\n\n"
        "<i>Qachon, qayerda va nima bo'lganini yozsangiz —\n"
        "tezroq hal qilamiz.</i>",
        reply_markup=cancel_kb,
    )


# ── 2) Tavsif ──
@dp.message(NewTicket.description, F.text)
async def reg_description(message: Message, state: FSMContext):
    desc = message.text.strip()
    if len(desc) < 5:
        await message.answer("⚠️ Biroz batafsilroq yozing (kamida 5 ta belgi):")
        return
    await state.update_data(description=desc)
    await state.set_state(NewTicket.attachment)
    await typing(message.chat.id, 0.3)
    await message.answer(
        "📷 <b>Skrinshot</b> bormi?\n"
        f"{DIV}\n"
        "Xatolik ko'rinishini suratga olib yuboring —\n"
        "bu muammoni tezroq aniqlashga yordam beradi.\n\n"
        "<i>Skrinshot bo'lmasa — pastdagi tugmani bosing.</i>",
        reply_markup=attachment_inline,
    )


# ── 3) Skrinshot (ixtiyoriy) ──
@dp.message(NewTicket.attachment, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await _ask_contact(message, state)


@dp.callback_query(F.data == "skip_photo", NewTicket.attachment)
async def cb_skip_photo(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏭ O'tkazildi")
    await state.update_data(photo=None)
    await _ask_contact(callback.message, state)


@dp.message(NewTicket.attachment, F.text)
async def attachment_hint(message: Message, state: FSMContext):
    await message.answer(
        "📷 Iltimos, skrinshotni <b>rasm</b> sifatida yuboring\n"
        "yoki «⏭ Skrinshotsiz davom etish» tugmasini bosing.",
        reply_markup=attachment_inline,
    )


async def _ask_contact(target: Message, state: FSMContext):
    await state.set_state(NewTicket.contact)
    await typing(target.chat.id, 0.3)
    await target.answer(
        "📞 <b>Bog'lanish uchun</b>\n"
        f"{DIV}\n"
        "Telefon raqamingizni yuboring yoki\n"
        "tizimdagi <b>login / email</b>ingizni yozing.\n\n"
        "<i>Bu admin sizni tezroq topishi uchun kerak.</i>",
        reply_markup=contact_request_kb,
    )


# ── 4) Kontakt ──
@dp.message(NewTicket.contact, F.contact)
async def reg_contact_phone(message: Message, state: FSMContext):
    phone = normalize_phone(message.contact.phone_number) or message.contact.phone_number
    await state.update_data(phone=str(phone), contact='')
    await _ask_priority(message, state)


@dp.message(NewTicket.contact, F.text)
async def reg_contact_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if text in ("⏭ O'tkazib yuborish", "⏭"):
        await state.update_data(phone='', contact='')
    else:
        phone = normalize_phone(text)
        if phone:
            await state.update_data(phone=phone, contact='')
        else:
            await state.update_data(phone='', contact=text)
    await _ask_priority(message, state)


async def _ask_priority(target: Message, state: FSMContext):
    await state.set_state(NewTicket.priority)
    await typing(target.chat.id, 0.3)
    await target.answer(
        "⚡ <b>Muammo qanchalik shoshilinch?</b>\n"
        f"{DIV}\n"
        "<i>Muhimlik darajasini tanlang:</i>",
        reply_markup=priority_inline(),
    )


# ── 5) Muhimlik → tasdiq ──
@dp.callback_query(F.data.startswith("prio_"), NewTicket.priority)
async def cb_priority(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_", 1)[1]
    if key not in PRIORITY_LABELS:
        await callback.answer("Noma'lum daraja", show_alert=True)
        return
    await callback.answer(PRIORITY_LABELS[key])
    await state.update_data(priority=key)
    await _show_summary(callback.message, state)


async def _show_summary(target: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(NewTicket.confirm)

    cat = CATEGORY_LABELS.get(data.get('category'), '—')
    prio = PRIORITY_LABELS.get(data.get('priority', 'normal'), '—')
    phone = data.get('phone') or ''
    contact = data.get('contact') or ''
    contact_line = (f"+998 {phone}" if phone else (contact or '—'))
    photo_line = "✅ bor" if data.get('photo') else "—"

    await typing(target.chat.id, 0.3)
    await target.answer(
        "🔎 <b>MUROJAATNI TASDIQLANG</b>\n"
        f"{DIV}\n"
        f"  📂 Bo'lim:    <b>{cat}</b>\n"
        f"  ⚡ Muhimlik: <b>{prio}</b>\n"
        f"  📞 Aloqa:    <b>{contact_line}</b>\n"
        f"  📷 Skrinshot: <b>{photo_line}</b>\n\n"
        "  📝 <b>Tavsif:</b>\n"
        f"  <i>{data.get('description', '')}</i>\n"
        f"{DIV}\n"
        "Hammasi to'g'rimi?",
        reply_markup=confirm_inline,
    )


@dp.callback_query(F.data == "t_restart")
async def cb_restart(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🔄 Qaytadan")
    await _begin_ticket(callback.message, state)


# ── 6) Tasdiqlash → murojaatni yaratish ──
@dp.callback_query(F.data == "t_confirm", NewTicket.confirm)
async def cb_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Yuborilmoqda...")
    data = await state.get_data()

    bar = await progress_bar(callback.message, "Murojaat yuborilmoqda")

    full_name = await get_known_name(callback.message.chat.id) or callback.from_user.full_name
    try:
        result = await create_ticket(
            category=data.get('category', 'other'),
            description=data.get('description', ''),
            full_name=full_name,
            phone=data.get('phone', ''),
            contact=data.get('contact', ''),
            chat_id=callback.message.chat.id,
            username=callback.from_user.username,
            priority=data.get('priority', 'normal'),
        )
    except Exception:
        logger.exception("Murojaat yaratishda xato")
        await state.clear()
        try:
            await bar.delete()
        except Exception:
            pass
        await callback.message.answer(
            "⚠️ <b>Xatolik yuz berdi.</b>\n"
            "Iltimos keyinroq qayta urinib ko'ring.",
            reply_markup=main_menu,
        )
        return

    photo_id = data.get('photo')
    await _notify_admins(result['code'], data, full_name,
                         callback.from_user, photo_id)

    await state.clear()
    try:
        await bar.delete()
    except Exception:
        pass

    await answer_fx(
        callback.message,
        "🎉 <b>MUROJAATINGIZ QABUL QILINDI!</b>\n"
        f"{DIV}\n"
        f"  🆔 Raqam:  <b>{result['code']}</b>\n"
        f"  📂 Bo'lim: <b>{CATEGORY_LABELS.get(data.get('category'), '—')}</b>\n\n"
        "✅ Murojaatingiz administratorga yuborildi.\n"
        "👨‍💻 Mutaxassis tez orada ko'rib chiqadi va\n"
        "javobni <b>shu botga</b> yuboradi.\n\n"
        "📋 Holatini «Murojaatlarim» dan kuzating.\n"
        f"{DIV}\n"
        "<i>Sabringiz uchun rahmat! 🙏</i>",
        reply_markup=success_inline(),
        effect=FX_PARTY,
    )


# ════════════════════════════════════════════════════
#          🔑 PAROLNI UNUTDIM (FSM)
# ════════════════════════════════════════════════════
async def _begin_pwd(target: Message, state: FSMContext):
    await state.clear()
    await state.set_state(PasswordReset.identifier)
    await typing(target.chat.id, 0.4)
    await target.answer(
        "🔑 <b>PAROLNI TIKLASH</b>\n"
        f"{DIV}\n"
        "Xavfsizlik uchun parolni <b>administrator</b>\n"
        "tiklab beradi.\n\n"
        "✍️ Tizimdagi <b>login</b>ingizni yoki\n"
        "<b>telefon / email</b>ingizni yozing:\n\n"
        "<i>Masalan: std_901234567  yoki  +998901234567</i>",
        reply_markup=cancel_kb,
    )


@dp.message(F.text == "🔑  Parolni unutdim")
async def btn_pwd(message: Message, state: FSMContext):
    await _begin_pwd(message, state)


@dp.message(PasswordReset.identifier, F.text)
async def pwd_identifier(message: Message, state: FSMContext):
    ident = message.text.strip()
    if len(ident) < 3:
        await message.answer("⚠️ Login/telefon juda qisqa. Qaytadan kiriting:")
        return
    phone = normalize_phone(ident)
    await state.update_data(
        identifier=ident,
        phone=phone or '',
        contact='' if phone else ident,
    )
    await state.set_state(PasswordReset.confirm)
    await typing(message.chat.id, 0.3)
    await message.answer(
        "🔎 <b>TASDIQLANG</b>\n"
        f"{DIV}\n"
        f"  🔑 Murojaat:  <b>Parolni tiklash</b>\n"
        f"  👤 Hisob:     <b>{ident}</b>\n"
        f"{DIV}\n"
        "Administratorga yuboraylikmi?",
        reply_markup=pwd_confirm_inline,
    )


@dp.callback_query(F.data == "pwd_restart")
async def cb_pwd_restart(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🔄 Qaytadan")
    await _begin_pwd(callback.message, state)


@dp.callback_query(F.data == "pwd_confirm", PasswordReset.confirm)
async def cb_pwd_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Yuborilmoqda...")
    data = await state.get_data()
    bar = await progress_bar(callback.message, "So'rov yuborilmoqda")

    full_name = await get_known_name(callback.message.chat.id) or callback.from_user.full_name
    ident = data.get('identifier', '')
    try:
        result = await create_ticket(
            category='password',
            description=f"Parolni tiklash so'rovi. Hisob: {ident}",
            full_name=full_name,
            phone=data.get('phone', ''),
            contact=data.get('contact', ''),
            chat_id=callback.message.chat.id,
            username=callback.from_user.username,
            priority='high',
            subject='Parolni tiklash',
        )
    except Exception:
        logger.exception("Parol murojaatida xato")
        await state.clear()
        try:
            await bar.delete()
        except Exception:
            pass
        await callback.message.answer("⚠️ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
                                      reply_markup=main_menu)
        return

    await _notify_admins(result['code'],
                         {'category': 'password', 'priority': 'high',
                          'description': f"Parolni tiklash — {ident}", 'phone': data.get('phone', ''),
                          'contact': data.get('contact', '')},
                         full_name, callback.from_user, None)

    await state.clear()
    try:
        await bar.delete()
    except Exception:
        pass

    await answer_fx(
        callback.message,
        "🔐 <b>SO'ROV QABUL QILINDI!</b>\n"
        f"{DIV}\n"
        f"  🆔 Raqam: <b>{result['code']}</b>\n\n"
        "✅ Administrator hisobingizni tekshirib,\n"
        "<b>yangi parolni shu botga</b> yuboradi.\n\n"
        "⏰ Odatda ish vaqtida 30 daqiqada javob beriladi.\n"
        f"{DIV}\n"
        "<i>Xavfsizligingiz biz uchun muhim. 🛡</i>",
        reply_markup=success_inline(),
        effect=FX_FIRE,
    )


# ════════════════════════════════════════════════════
#          📋 MENING MUROJAATLARIM
# ════════════════════════════════════════════════════
async def _show_my_tickets(target: Message):
    await typing(target.chat.id, 0.4)
    tickets = await get_my_tickets(target.chat.id)
    if not tickets:
        await target.answer(
            "📭 <b>Sizda hali murojaatlar yo'q.</b>\n\n"
            "Muammo bo'lsa «🆘 Muammoni bildirish» ni bosing.",
            reply_markup=main_menu,
        )
        return

    status_icon = {'new': '🆕', 'in_progress': '⏳', 'resolved': '✅', 'closed': '🔒'}
    lines = ["📋 <b>MENING MUROJAATLARIM</b>", DIV]
    for t in tickets:
        si = status_icon.get(t['status_key'], '•')
        lines.append(
            f"\n{t['emoji']} <b>{t['code']}</b> · {t['category']}\n"
            f"   {si} Holat: <b>{t['status']}</b>\n"
            f"   🗓 {t['created']}"
        )
        if t['admin_reply']:
            lines.append(f"   💬 <i>Javob: {t['admin_reply']}</i>")
    lines.append(f"\n{DIV}")
    await target.answer("\n".join(lines), reply_markup=back_to_main_inline)


@dp.message(F.text == "📋  Murojaatlarim")
async def btn_my_tickets(message: Message):
    await _show_my_tickets(message)


@dp.callback_query(F.data == "my_tickets")
async def cb_my_tickets(callback: CallbackQuery):
    await callback.answer("📋 Murojaatlarim")
    await _show_my_tickets(callback.message)


# ════════════════════════════════════════════════════
#          ❓ SAVOL-JAVOB / 👨‍💻 ADMIN / ℹ️ HAQIDA
# ════════════════════════════════════════════════════
@dp.message(F.text == "❓  Savol-javob")
async def btn_faq(message: Message):
    await typing(message.chat.id, 0.3)
    await message.answer(
        "❓ <b>KO'P SO'RALADIGAN SAVOLLAR</b>\n"
        f"{DIV}\n"
        "❔ <b>Parolni unutib qo'ydim.</b>\n"
        "┗ «🔑 Parolni unutdim» tugmasini bosing —\n"
        "  admin yangi parolni shu yerga yuboradi.\n\n"
        "❔ <b>Tizimga kira olmayapman.</b>\n"
        "┗ Login/parol to'g'riligini tekshiring.\n"
        "  Foyda bermasa — «🆘 Muammoni bildirish».\n\n"
        "❔ <b>To'lov o'tmadi / ko'rinmayapti.</b>\n"
        "┗ «🆘 Muammoni bildirish» → «💳 To'lov».\n\n"
        "❔ <b>Javob qancha vaqtda keladi?</b>\n"
        "┗ Ish vaqtida odatda 30 daqiqada.\n"
        f"{DIV}",
        reply_markup=faq_inline,
    )


@dp.message(F.text == "👨‍💻  Admin")
async def btn_admin(message: Message):
    await typing(message.chat.id, 0.3)
    await message.answer(
        "👨‍💻 <b>ADMIN BILAN BOG'LANISH</b>\n"
        f"{DIV}\n"
        f"  💬 Telegram:  <b>{ADMIN_USERNAME}</b>\n"
        "  ⏰ Ish vaqti: <b>9:00 — 22:00</b>\n"
        "  📅 Kunlar:    <b>Dush — Shan</b>\n\n"
        "💡 <i>Eng tez yo'l — «🆘 Muammoni bildirish».\n"
        "Murojaat raqami bilan kuzatiladi va\n"
        "javob shu botga keladi.</i>\n"
        f"{DIV}",
        reply_markup=admin_inline,
    )


@dp.message(F.text == "ℹ️  Bot haqida")
async def btn_about(message: Message):
    await typing(message.chat.id, 0.3)
    await message.answer(
        "┌─────────────────────────┐\n"
        f"│  🛠  <b>TECHNIC BOT — v{BOT_VERSION}</b>   │\n"
        "└─────────────────────────┘\n\n"
        f"🏦 <b>{BOT_NAME}</b>\n\n"
        "Wall Street platformasining rasmiy\n"
        "texnik yordam yordamchisi.\n\n"
        f"{DIV}\n"
        "🛠 <b>Imkoniyatlar:</b>\n\n"
        "  🆘  Texnik nosozliklar bo'yicha murojaat\n"
        "  🔑  Parolni tiklash so'rovi\n"
        "  📋  Murojaat holatini kuzatish\n"
        "  💬  Admindan to'g'ridan-to'g'ri javob\n\n"
        f"{DIV}\n"
        "⚡ <b>Texnik:</b> aiogram 3.x · Django ORM\n"
        "💼 <b>Wall Street Team</b>",
        reply_markup=about_inline,
    )


# ── /help ──
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Buyruqlar:</b>\n\n"
        "  /start  — Botni qayta ishga tushirish\n"
        "  /report — Yangi texnik murojaat\n"
        "  /help   — Yordam\n",
        reply_markup=main_menu,
    )


# ── 🏠 Asosiy menyu (callback) ──
@dp.callback_query(F.data == "to_main")
async def cb_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("🏠 Asosiy menyu")
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n⬇️ <i>Kerakli bo'limni tanlang:</i>",
        reply_markup=main_menu,
    )


# ════════════════════════════════════════════════════
#          ADMINGA OGOHLANTIRISH
# ════════════════════════════════════════════════════
async def _notify_admins(code, data, full_name, from_user, photo_file_id=None):
    """Yangi murojaat haqida barcha adminlarga xabar (+skrinshot) yuboradi."""
    ids = list(ADMIN_CHAT_IDS)
    try:
        ids += await get_admin_chat_ids()
    except Exception:
        logger.warning("Admin chat ID larini olishda xato")
    ids = list(dict.fromkeys(str(i) for i in ids if i))  # noyob
    if not ids:
        logger.info("Admin chat ID topilmadi — faqat dashboardga yozildi.")
        return

    uname = f"@{from_user.username}" if from_user.username else "—"
    cat = CATEGORY_LABELS.get(data.get('category'), data.get('category', '—'))
    prio = PRIORITY_LABELS.get(data.get('priority', 'normal'), '—')
    phone = data.get('phone') or ''
    contact = data.get('contact') or ''
    contact_line = (f"+998 {phone}" if phone else (contact or '—'))

    text = (
        "🔔 <b>YANGI TEXNIK MUROJAAT</b>\n"
        f"{DIV}\n"
        f"  🆔 Raqam:    <b>{code}</b>\n"
        f"  📂 Bo'lim:   <b>{cat}</b>\n"
        f"  ⚡ Muhimlik: <b>{prio}</b>\n"
        f"  👤 Kimdan:   <b>{full_name}</b> ({uname})\n"
        f"  📞 Aloqa:    <b>{contact_line}</b>\n"
        f"{DIV}\n"
        "  📝 <b>Tavsif:</b>\n"
        f"  <i>{data.get('description', '')}</i>\n"
        f"{DIV}\n"
        "💻 To'liq ko'rinishi: <b>Settings → Yordam markazi</b>"
    )

    for cid in ids:
        try:
            if photo_file_id:
                await bot.send_photo(cid, photo_file_id, caption=text)
            else:
                await bot.send_message(cid, text)
        except Exception:
            logger.warning("Adminga (%s) xabar yuborib bo'lmadi", cid)


# ════════════════════════════════════════════════════
#          FALLBACK
# ════════════════════════════════════════════════════
@dp.message()
async def fallback(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        # FSM ichida kutilmagan kontent
        await message.answer(
            "⚠️ Iltimos, ko'rsatmaga amal qiling yoki\n"
            "«❌ Bekor qilish» tugmasini bosing.",
        )
        return
    await message.answer(
        "❓ <b>Tushunarsiz buyruq.</b>\n\n"
        "Quyidagi tugmalardan foydalaning 👇",
        reply_markup=main_menu,
    )


# ════════════════════════════════════════════════════
#          STARTUP
# ════════════════════════════════════════════════════
async def on_startup():
    me = await bot.get_me()
    logger.info("=" * 50)
    logger.info("🛠  %s Technic Bot v%s", BOT_NAME, BOT_VERSION)
    logger.info("🤖  @%s ishga tushdi!", me.username)
    logger.info("=" * 50)


async def main():
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
