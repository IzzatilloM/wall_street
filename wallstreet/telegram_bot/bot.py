import asyncio
import logging
import re

import db  # ← Django ni bootstrap qiladi (django_setup) + ORM helperlar
from db import (
    get_active_courses, get_course_detail,
    register_student, register_lead, phone_exists, telegram_already_registered,
)

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from storage import DjangoFSMStorage  # FSM holati bazada (webhook uchun barqaror)

from config import BOT_TOKEN, BOT_NAME, BOT_VERSION, ADMIN_USERNAME, LOGIN_URL, PROXY_URL
from states import StudentRegistration
from keyboards import (
    main_menu, phone_request_kb, skip_kb, cancel_kb,
    about_inline, help_inline, id_panel_inline,
    platform_inline, social_inline,
    register_confirm_inline, register_success_inline,
    build_courses_inline, course_detail_inline,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("wallstreet_bot")
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi! .env faylga qo'shing.")

_session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
bot = Bot(token=BOT_TOKEN, session=_session,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=DjangoFSMStorage())

DIV = "━━━━━━━━━━━━━━━━━━━━━━━━━━"


def normalize_phone(raw: str) -> str | None:
    """Turli formatdagi raqamni 9 xonali (901234567) ko'rinishga keltiradi."""
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
    username = message.from_user.username
    chat_id = message.chat.id
    uname_display = f"@{username}" if username else "—"

    loading = await message.answer("⏳")
    await asyncio.sleep(0.5)
    await loading.delete()

    welcome = (
        f"🏦  <b>{BOT_NAME}</b>\n"
        f"{DIV}\n"
        f"👋 Xush kelibsiz, <b>{full_name}</b>!\n\n"
        "🎯 Bu — <b>Wall Street CRM</b> ta'lim\n"
        "platformasining rasmiy boti.\n\n"
        "╔══════════════════════════╗\n"
        "║   🆔  <b>SIZNING MA'LUMOTLAR</b>   ║\n"
        "╚══════════════════════════╝\n\n"
        f"  👤 Ism:       <b>{full_name}</b>\n"
        f"  🔖 Username:  <b>{uname_display}</b>\n"
        f"  🔢 Chat ID:   <code>{chat_id}</code>\n\n"
        f"{DIV}\n"
        "🚀 <b>Bot orqali nima qila olasiz?</b>\n\n"
        "  📝  To'g'ridan-to'g'ri ro'yxatdan o'tish\n"
        "  🎓  Kurslar bilan tanishish\n"
        "  📊  Platformaga kirish\n"
        "  🆔  Telegram ID olish\n\n"
        f"{DIV}\n"
        "⬇️ <b>Quyidagi bo'limni tanlang:</b>"
    )
    await message.answer(welcome, reply_markup=main_menu)


# ════════════════════════════════════════════════════
#          🆔 ID RAQAMIM
# ════════════════════════════════════════════════════
@dp.message(F.text == "🆔  ID Raqamim")
async def my_id_handler(message: Message):
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    uname_display = f"@{username}" if username else "—"

    text = (
        "┌─────────────────────────┐\n"
        "│   🆔  <b>SHAXSIY ID PANELI</b>   │\n"
        "└─────────────────────────┘\n\n"
        f"  👤 To'liq ism: <b>{full_name}</b>\n"
        f"  🔖 Username:   <b>{uname_display}</b>\n"
        f"  🔢 Chat ID:    <code>{chat_id}</code>\n\n"
        f"{DIV}\n"
        "💡 <i>ID raqamingizni saytdagi register\n"
        "oynasiga kiriting yoki to'g'ridan-to'g'ri\n"
        "bot orqali ro'yxatdan o'ting.</i>"
    )
    await message.answer(text, reply_markup=id_panel_inline)


# ════════════════════════════════════════════════════
#          📊 PLATFORMA
# ════════════════════════════════════════════════════
@dp.message(F.text == "📊  Platforma")
async def platform_handler(message: Message):
    text = (
        "┌─────────────────────────┐\n"
        "│  📊  <b>WALL STREET PLATFORMA</b>│\n"
        "└─────────────────────────┘\n\n"
        "🏦 <b>Wall Street CRM</b> — zamonaviy\n"
        "ta'lim boshqaruv platformasi.\n\n"
        f"{DIV}\n"
        "📌 <b>Imkoniyatlar:</b>\n\n"
        "  📚  Kurslar va guruhlar boshqaruvi\n"
        "  ✅  Davomat nazorati\n"
        "  💳  To'lovlar tizimi\n"
        "  📅  Kalendar va tadbirlar\n"
        "  📊  Hisobotlar va statistika\n\n"
        f"{DIV}\n"
        "⬇️ <b>Quyidagi tugmalardan foydalaning:</b>"
    )
    await message.answer(text, reply_markup=platform_inline)


# ════════════════════════════════════════════════════
#          🎓 KURSLAR  (DB dan)
# ════════════════════════════════════════════════════
@dp.message(F.text == "🎓  Kurslar")
async def courses_handler(message: Message):
    loading = await message.answer("📚 <i>Kurslar yuklanmoqda...</i>")
    try:
        courses = await get_active_courses()
    except Exception as e:
        logger.exception("Kurslarni olishda xato")
        await loading.delete()
        await message.answer("⚠️ Kurslarni yuklab bo'lmadi. Keyinroq urinib ko'ring.")
        return
    await loading.delete()

    if not courses:
        await message.answer(
            "📭 <b>Hozircha faol kurslar yo'q.</b>\n\n"
            "Tez orada yangi kurslar qo'shiladi!",
            reply_markup=main_menu,
        )
        return

    lines = [
        "┌─────────────────────────┐",
        "│     🎓  <b>TA'LIM KURSLARI</b>    │",
        "└─────────────────────────┘\n",
        "🏆 <b>Faol kurslar ro'yxati:</b>\n",
    ]
    for i, c in enumerate(courses, 1):
        lines.append(
            f"<b>{i}. {c['title']}</b>\n"
            f"   🏷 {c['category']} · 📊 {c['level']}\n"
            f"   ⏱ {c['duration']} · 💰 ${c['price']:,.0f}"
        )
    lines.append(f"\n{DIV}")
    lines.append("⬇️ <i>Batafsil ma'lumot uchun kursni tanlang:</i>")

    await message.answer("\n".join(lines), reply_markup=build_courses_inline(courses))


# ════════════════════════════════════════════════════
#          ℹ️ BOT HAQIDA
# ════════════════════════════════════════════════════
@dp.message(F.text == "ℹ️  Bot haqida")
async def about_handler(message: Message):
    text = (
        "┌─────────────────────────┐\n"
        f"│  🤖  <b>BOT HAQIDA — v{BOT_VERSION}</b>  │\n"
        "└─────────────────────────┘\n\n"
        f"🏦 <b>{BOT_NAME} Bot</b>\n\n"
        "Platformaning rasmiy yordamchi boti.\n\n"
        f"{DIV}\n"
        "🛠 <b>Imkoniyatlar:</b>\n\n"
        "  📝  Bot orqali ro'yxatdan o'tish\n"
        "  🎓  Jonli kurslar ro'yxati\n"
        "  🆔  Telegram ID olish\n"
        "  📊  Platformaga tezkor kirish\n\n"
        f"{DIV}\n"
        "⚡ <b>Texnik:</b>\n\n"
        f"  📦 Versiya:   <b>v{BOT_VERSION}</b>\n"
        "  🔧 Framework: <b>aiogram 3.x</b>\n"
        "  🗄 Backend:   <b>Django ORM</b>\n\n"
        f"{DIV}\n"
        "💼 <b>Wall Street CRM Team</b>"
    )
    await message.answer(text, reply_markup=about_inline)


# ════════════════════════════════════════════════════
#          🛟 YORDAM
# ════════════════════════════════════════════════════
@dp.message(F.text == "🛟  Yordam")
async def help_handler(message: Message):
    text = (
        "┌─────────────────────────┐\n"
        "│      🛟  <b>YORDAM MARKAZI</b>     │\n"
        "└─────────────────────────┘\n\n"
        "📋 <b>Ro'yxatdan o'tish (bot orqali):</b>\n\n"
        "  1️⃣  «📝 Ro'yxatdan o'tish» ni bosing\n"
        "  2️⃣  Ism va familiyangizni kiriting\n"
        "  3️⃣  Telefon raqamingizni yuboring\n"
        "  4️⃣  Ma'lumotlarni tasdiqlang\n"
        "  5️⃣  Tayyor — tizimga qo'shildingiz!\n\n"
        f"{DIV}\n"
        f"⚠️ Muammo bo'lsa: <b>{ADMIN_USERNAME}</b>"
    )
    await message.answer(text, reply_markup=help_inline)


# ════════════════════════════════════════════════════
#          /id va /help
# ════════════════════════════════════════════════════
@dp.message(Command("id"))
async def command_id_handler(message: Message):
    await message.answer(
        "🆔 <b>Sizning Telegram ID raqamingiz:</b>\n\n"
        f"<code>{message.chat.id}</code>\n\n"
        "📌 <i>Uni register oynasiga kiriting.</i>"
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message):
    await message.answer(
        "📋 <b>Buyruqlar:</b>\n\n"
        "  /start    — Botni qayta ishga tushirish\n"
        "  /register — Ro'yxatdan o'tish\n"
        "  /id       — Chat ID olish\n"
        "  /help     — Yordam\n",
        reply_markup=main_menu,
    )


# ════════════════════════════════════════════════════
#          📝 RO'YXATDAN O'TISH  (FSM)
# ════════════════════════════════════════════════════
async def _begin_registration(message: Message, state: FSMContext):
    if await telegram_already_registered(message.chat.id):
        await message.answer(
            "✅ <b>Siz allaqachon ro'yxatdan o'tgansiz!</b>\n\n"
            "🚀 Platformaga kirishingiz mumkin.",
            reply_markup=main_menu,
        )
        return

    await state.set_state(StudentRegistration.first_name)
    await message.answer(
        "📝 <b>TALABA RO'YXATIDAN O'TISH</b>\n"
        f"{DIV}\n"
        "1️⃣ <b>Ismingizni</b> kiriting:\n\n"
        "<i>Masalan: Ali</i>",
        reply_markup=cancel_kb,
    )


@dp.message(Command("register"))
async def command_register(message: Message, state: FSMContext):
    await _begin_registration(message, state)


@dp.message(F.text == "📝  Ro'yxatdan o'tish")
async def btn_register(message: Message, state: FSMContext):
    await _begin_registration(message, state)


@dp.callback_query(F.data == "start_register")
async def cb_start_register(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _begin_registration(callback.message, state)


# ── Bekor qilish (har qanday holatda) ──
@dp.message(F.text == "❌ Bekor qilish")
async def cancel_registration(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.clear()
    await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu)


# ── 1) Ism ──
@dp.message(StudentRegistration.first_name)
async def reg_first_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Ism juda qisqa. Qaytadan kiriting:")
        return
    await state.update_data(first_name=name)
    await state.set_state(StudentRegistration.last_name)
    await message.answer(
        "2️⃣ <b>Familiyangizni</b> kiriting:\n\n<i>Masalan: Valiyev</i>",
        reply_markup=cancel_kb,
    )


# ── 2) Familiya ──
@dp.message(StudentRegistration.last_name)
async def reg_last_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Familiya juda qisqa. Qaytadan kiriting:")
        return
    await state.update_data(last_name=name)
    await state.set_state(StudentRegistration.phone)
    await message.answer(
        "3️⃣ <b>Telefon raqamingizni</b> yuboring:\n\n"
        "Quyidagi tugmani bosing yoki qo'lda yozing\n"
        "<i>(masalan: 901234567)</i>",
        reply_markup=phone_request_kb,
    )


# ── 3) Telefon (contact yoki matn) ──
@dp.message(StudentRegistration.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    await _process_phone(message, state, message.contact.phone_number)


@dp.message(StudentRegistration.phone, F.text)
async def reg_phone_text(message: Message, state: FSMContext):
    await _process_phone(message, state, message.text)


async def _process_phone(message: Message, state: FSMContext, raw_phone: str):
    phone = normalize_phone(raw_phone)
    if not phone:
        await message.answer(
            "⚠️ Telefon raqam noto'g'ri.\n"
            "9 xonali raqam kiriting (masalan: <b>901234567</b>):",
            reply_markup=phone_request_kb,
        )
        return
    if await phone_exists(phone):
        await message.answer(
            "⚠️ Bu telefon raqam allaqachon ro'yxatdan o'tgan.\n"
            "Boshqa raqam kiriting yoki adminga murojaat qiling.",
            reply_markup=phone_request_kb,
        )
        return
    await state.update_data(phone=phone)
    await state.set_state(StudentRegistration.email)
    await message.answer(
        "4️⃣ <b>Email</b> kiriting <i>(ixtiyoriy)</i>:\n\n"
        "Email yo'q bo'lsa «⏭ O'tkazib yuborish» ni bosing.",
        reply_markup=skip_kb,
    )


# ── 4) Email (ixtiyoriy) ──
@dp.message(StudentRegistration.email)
async def reg_email(message: Message, state: FSMContext):
    text = message.text.strip()
    email = ""
    if text not in ("⏭ O'tkazib yuborish", "⏭", ""):
        if "@" not in text or "." not in text:
            await message.answer("⚠️ Email noto'g'ri. Qaytadan kiriting yoki o'tkazib yuboring:")
            return
        email = text.lower()

    await state.update_data(email=email)
    data = await state.get_data()
    await state.set_state(StudentRegistration.confirm)

    await message.answer(
        "🔎 <b>MA'LUMOTLARNI TASDIQLANG</b>\n"
        f"{DIV}\n"
        f"  👤 Ism:      <b>{data['first_name']}</b>\n"
        f"  👥 Familiya: <b>{data['last_name']}</b>\n"
        f"  📱 Telefon:  <b>+998 {data['phone']}</b>\n"
        f"  ✉️ Email:    <b>{email or '—'}</b>\n"
        f"{DIV}\n"
        "Hammasi to'g'rimi?",
        reply_markup=register_confirm_inline,
    )


# ── Tasdiqlash ──
@dp.callback_query(F.data == "reg_confirm", StudentRegistration.confirm)
async def cb_reg_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Yuborilmoqda...")
    data = await state.get_data()
    try:
        await register_lead(
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data["phone"],
            chat_id=callback.message.chat.id,
            username=callback.from_user.username,
            email=data.get("email"),
        )
    except Exception as e:
        logger.exception("Telegram ariza yaratishda xato")
        await state.clear()
        await callback.message.answer(
            "⚠️ <b>Xatolik yuz berdi.</b>\n"
            "Iltimos keyinroq qayta urinib ko'ring yoki adminga murojaat qiling.",
            reply_markup=main_menu,
        )
        return

    await state.clear()
    await callback.message.answer(
        "🎉 <b>ARIZANGIZ QABUL QILINDI!</b>\n"
        f"{DIV}\n"
        f"  👤 <b>{data['first_name']} {data['last_name']}</b>\n"
        f"  📱 +998 {data['phone']}\n\n"
        "✅ Ma'lumotlaringiz administratorga yuborildi.\n"
        "📞 Administrator tez orada siz bilan bog'lanib, "
        "ro'yxatdan o'tkazishni yakunlaydi va kirish ma'lumotlaringizni beradi.\n\n"
        "<i>Sabringiz uchun rahmat!</i>\n"
        f"{DIV}",
        reply_markup=main_menu,
    )


@dp.callback_query(F.data == "reg_restart")
async def cb_reg_restart(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🔄 Qaytadan")
    await _begin_registration(callback.message, state)


@dp.callback_query(F.data == "reg_cancel")
async def cb_reg_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer("❌ Bekor qilindi")
    await state.clear()
    await callback.message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu)


# ════════════════════════════════════════════════════
#          KURS TAFSILOTLARI (callback)
# ════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("course_"))
async def course_detail_callback(callback: CallbackQuery):
    try:
        course_id = int(callback.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Kurs topilmadi")
        return

    course = await get_course_detail(course_id)
    if not course:
        await callback.answer("⚠️ Kurs topilmadi yoki faol emas", show_alert=True)
        return

    await callback.answer(course["title"])
    await callback.message.answer(
        f"┌─────────────────────────┐\n"
        f"│  🎓  <b>KURS TAFSILOTLARI</b>    │\n"
        f"└─────────────────────────┘\n\n"
        f"<b>{course['title']}</b>\n\n"
        f"📝 {course['description']}\n\n"
        f"{DIV}\n"
        f"  🏷 Yo'nalish:  <b>{course['category']}</b>\n"
        f"  📊 Daraja:     <b>{course['level']}</b>\n"
        f"  👨‍🏫 O'qituvchi: <b>{course['teacher']}</b>\n"
        f"  ⏱ Davomiylik: <b>{course['duration']}</b>\n"
        f"  👥 Talabalar:  <b>{course['students']}</b>\n"
        f"  💰 Narxi:      <b>${course['price']:,.0f}</b>\n"
        f"{DIV}\n"
        "🚀 <i>Yozilish uchun ro'yxatdan o'ting:</i>",
        reply_markup=course_detail_inline(course_id),
    )


@dp.callback_query(F.data == "back_to_courses")
async def back_to_courses_callback(callback: CallbackQuery):
    await callback.answer("🎓 Kurslar")
    await courses_handler(callback.message)


# ════════════════════════════════════════════════════
#          BOSHQA CALLBACKLAR
# ════════════════════════════════════════════════════
@dp.callback_query(F.data == "contact_admin")
async def contact_admin_callback(callback: CallbackQuery):
    await callback.answer("📩 Admin ma'lumotlari")
    await callback.message.answer(
        "┌─────────────────────────┐\n"
        "│   📩  <b>ADMIN ALOQASI</b>      │\n"
        "└─────────────────────────┘\n\n"
        f"  💬 Telegram:  <b>{ADMIN_USERNAME}</b>\n"
        "  ⏰ Ish vaqti: <b>9:00 — 22:00</b>\n"
        "  📅 Kunlar:    <b>Dush — Shan</b>\n\n"
        f"{DIV}\n"
        "⚡ <i>Odatda 30 daqiqada javob beriladi.</i>"
    )


@dp.callback_query(F.data == "social_links")
async def social_links_callback(callback: CallbackQuery):
    await callback.answer("🌟 Ijtimoiy tarmoqlar")
    await callback.message.answer(
        "🌟 <b>IJTIMOIY TARMOQLAR</b>\n"
        f"{DIV}\n"
        "📱 Bizni kuzating va yangiliklardan\n"
        "birinchilardan bo'lib xabardor bo'ling!",
        reply_markup=social_inline,
    )


@dp.callback_query(F.data == "show_guide")
async def show_guide_callback(callback: CallbackQuery):
    await callback.answer("📖 Qo'llanma")
    await callback.message.answer(
        "📖 <b>TO'LIQ QO'LLANMA</b>\n"
        f"{DIV}\n"
        "<b>A) Bot orqali (eng oson):</b>\n"
        "  ① «📝 Ro'yxatdan o'tish» ni bosing\n"
        "  ② Ism, familiya, telefon kiriting\n"
        "  ③ Tasdiqlang — tayyor!\n\n"
        "<b>B) Sayt orqali:</b>\n"
        "  ① Bot orqali Chat ID oling\n"
        "  ② Saytda Register ni bosing\n"
        "  ③ Telegram ID maydoniga kiriting\n"
        "  ④ Botdan kelgan kodni saytga yozing\n"
        f"{DIV}\n"
        "⚠️ <i>Kod faqat 5 daqiqa amal qiladi.</i>"
    )


@dp.callback_query(F.data == "show_faq")
async def show_faq_callback(callback: CallbackQuery):
    await callback.answer("❓ FAQ")
    await callback.message.answer(
        "❓ <b>KO'P SO'RALADIGAN SAVOLLAR</b>\n"
        f"{DIV}\n"
        "❔ <b>Bot orqali ro'yxatdan o'tsam bo'ladimi?</b>\n"
        "┗ Ha! «📝 Ro'yxatdan o'tish» tugmasi.\n\n"
        "❔ <b>Kod kelmadi-ku?</b>\n"
        "┗ Botni /start bilan ishga tushiring va\n"
        "  Chat ID to'g'ri ekanini tekshiring.\n\n"
        "❔ <b>Kurslar narxi qancha?</b>\n"
        "┗ «🎓 Kurslar» bo'limida ko'rsatilgan.\n"
        f"{DIV}\n"
        f"📩 <i>Qo'shimcha savol: {ADMIN_USERNAME}</i>"
    )


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("🏠 Asosiy menyu")
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n⬇️ <i>Kerakli bo'limni tanlang:</i>",
        reply_markup=main_menu,
    )


@dp.callback_query(F.data == "back_to_about")
async def back_to_about_callback(callback: CallbackQuery):
    await callback.answer("ℹ️ Bot haqida")
    await callback.message.answer(
        f"ℹ️ <b>{BOT_NAME}</b> haqida ma'lumot:",
        reply_markup=about_inline,
    )


# ════════════════════════════════════════════════════
#          FALLBACK
# ════════════════════════════════════════════════════
@dp.message()
async def fallback_handler(message: Message, state: FSMContext):
    # FSM ichida bo'lsa — tegmaymiz (state handlerlari ushlaydi)
    if await state.get_state() is not None:
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
    logger.info(f"🏦  {BOT_NAME} v{BOT_VERSION}")
    logger.info(f"🤖  @{me.username} ishga tushdi!")
    logger.info("=" * 50)


async def main():
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
