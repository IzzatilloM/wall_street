from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import (
    WEBSITE_URL, LOGIN_URL, REGISTER_URL, RESET_URL, COURSES_URL,
    SUPPORT_URL, TELEGRAM_CHANNEL, INSTAGRAM_URL, YOUTUBE_URL, LINKEDIN_URL,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#        🏦 WALL STREET CRM BOT
#         Professional Keyboards v3
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ╔══════════════════════════════════╗
#          MAIN MENU (Reply)
# ╚══════════════════════════════════╝
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝  Ro'yxatdan o'tish")],
        [
            KeyboardButton(text="🎓  Kurslar"),
            KeyboardButton(text="🆔  ID Raqamim"),
        ],
        [
            KeyboardButton(text="📊  Platforma"),
            KeyboardButton(text="🛟  Yordam"),
        ],
        [KeyboardButton(text="ℹ️  Bot haqida")],
    ],
    resize_keyboard=True,
    input_field_placeholder="⌨️ Bo'limni tanlang...",
)

# ── Telefon raqam so'rash uchun ──
phone_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        [KeyboardButton(text="❌ Bekor qilish")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Telefon raqamingizni yuboring...",
)

skip_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏭ O'tkazib yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# ╔══════════════════════════════════╗
#          REGISTER CONFIRM (inline)
# ╚══════════════════════════════════╝
register_confirm_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅  Tasdiqlash", callback_data="reg_confirm"),
            InlineKeyboardButton(text="🔄  Qaytadan", callback_data="reg_restart"),
        ],
        [InlineKeyboardButton(text="❌  Bekor qilish", callback_data="reg_cancel")],
    ]
)


def register_success_inline(login_url=LOGIN_URL):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀  Platformaga kirish", url=login_url)],
            [InlineKeyboardButton(text="🎓  Kurslarni ko'rish", url=COURSES_URL)],
            [InlineKeyboardButton(text="🏠  Asosiy menyu", callback_data="back_to_main")],
        ]
    )


# ╔══════════════════════════════════╗
#        ID PANEL (inline)
# ╚══════════════════════════════════╝
id_panel_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝  Bot orqali ro'yxatdan o'tish", callback_data="start_register")],
        [InlineKeyboardButton(text="🔐  Saytda ro'yxatdan o'tish", url=REGISTER_URL)],
        [InlineKeyboardButton(text="📋  Qo'llanma ko'rish", callback_data="show_guide")],
    ]
)

# ╔══════════════════════════════════╗
#        ABOUT (inline)
# ╚══════════════════════════════════╝
about_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🌐  Platformaga o'tish", url=WEBSITE_URL)],
        [InlineKeyboardButton(text="📈  Kurslar va narxlar", url=COURSES_URL)],
        [
            InlineKeyboardButton(text="📩  Admin", callback_data="contact_admin"),
            InlineKeyboardButton(text="🌟  Tarmoqlar", callback_data="social_links"),
        ],
        [InlineKeyboardButton(text="⬅️  Orqaga", callback_data="back_to_main")],
    ]
)

# ╔══════════════════════════════════╗
#        HELP (inline)
# ╚══════════════════════════════════╝
help_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📖  To'liq qo'llanma", callback_data="show_guide")],
        [InlineKeyboardButton(text="🤝  Admin bilan bog'lanish", url=SUPPORT_URL)],
        [InlineKeyboardButton(text="❓  FAQ — savol-javob", callback_data="show_faq")],
        [InlineKeyboardButton(text="⬅️  Orqaga", callback_data="back_to_main")],
    ]
)

# ╔══════════════════════════════════╗
#        PLATFORM (inline)
# ╚══════════════════════════════════╝
platform_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀  Platformaga kirish", url=LOGIN_URL)],
        [InlineKeyboardButton(text="🆕  Yangi hisob ochish", url=REGISTER_URL)],
        [InlineKeyboardButton(text="🔑  Parolni tiklash", url=RESET_URL)],
        [InlineKeyboardButton(text="⬅️  Orqaga", callback_data="back_to_main")],
    ]
)

# ╔══════════════════════════════════╗
#        SOCIAL (inline)
# ╚══════════════════════════════════╝
social_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💬  Telegram", url=TELEGRAM_CHANNEL),
            InlineKeyboardButton(text="📸  Instagram", url=INSTAGRAM_URL),
        ],
        [
            InlineKeyboardButton(text="▶️  YouTube", url=YOUTUBE_URL),
            InlineKeyboardButton(text="💼  LinkedIn", url=LINKEDIN_URL),
        ],
        [InlineKeyboardButton(text="⬅️  Orqaga", callback_data="back_to_about")],
    ]
)


# ╔══════════════════════════════════╗
#      DYNAMIC COURSES (inline)
# ╚══════════════════════════════════╝
def build_courses_inline(courses):
    """DB dan kelgan kurslardan inline klaviatura yasaydi."""
    rows = []
    pair = []
    for c in courses:
        pair.append(
            InlineKeyboardButton(text=f"🎓 {c['title']}", callback_data=f"course_{c['id']}")
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)

    rows.append([InlineKeyboardButton(text="📚  Barcha kurslar (sayt)", url=COURSES_URL)])
    rows.append([InlineKeyboardButton(text="⬅️  Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_detail_inline(course_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝  Ushbu kursga yozilish", callback_data="start_register")],
            [InlineKeyboardButton(text="🌐  Saytda ko'rish", url=COURSES_URL)],
            [InlineKeyboardButton(text="⬅️  Kurslarga qaytish", callback_data="back_to_courses")],
        ]
    )
