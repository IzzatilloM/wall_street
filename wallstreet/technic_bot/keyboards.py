"""
Wall Street Technic Bot — professional klaviaturalar.
Emoji-boy, ikki ustunli, animatsion his beradigan tugmalar.
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from config import LOGIN_URL, RESET_URL, SUPPORT_URL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#        🛠 WALL STREET TECHNIC BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ╔══════════════════════════════════╗
#          MAIN MENU (Reply)
# ╚══════════════════════════════════╝
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘  Muammoni bildirish")],
        [
            KeyboardButton(text="🔑  Parolni unutdim"),
            KeyboardButton(text="📋  Murojaatlarim"),
        ],
        [
            KeyboardButton(text="❓  Savol-javob"),
            KeyboardButton(text="👨‍💻  Admin"),
        ],
        [KeyboardButton(text="ℹ️  Bot haqida")],
    ],
    resize_keyboard=True,
    input_field_placeholder="⌨️ Texnik yordam — bo'limni tanlang...",
)

# ── Bekor qilish ──
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Yozing yoki «❌ Bekor qilish»...",
)

# ── Telefon so'rash ──
contact_request_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
        [
            KeyboardButton(text="⏭ O'tkazib yuborish"),
            KeyboardButton(text="❌ Bekor qilish"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Telefon yoki login yozing...",
)


# ╔══════════════════════════════════╗
#          KATEGORIYA (inline)
# ╚══════════════════════════════════╝
# Model bilan mos: (callback_key, ko'rinish)
CATEGORY_BUTTONS = [
    ("login",   "🚪 Tizimga kira olmayapman"),
    ("payment", "💳 To'lov muammosi"),
    ("account", "👤 Hisob / profil"),
    ("course",  "🎓 Kurs / dars"),
    ("bug",     "🐞 Texnik xatolik"),
    ("other",   "❓ Boshqa muammo"),
]


def category_inline():
    rows, pair = [], []
    for key, label in CATEGORY_BUTTONS:
        pair.append(InlineKeyboardButton(text=label, callback_data=f"cat_{key}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="t_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ╔══════════════════════════════════╗
#          MUHIMLIK (inline)
# ╚══════════════════════════════════╝
def priority_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Past", callback_data="prio_low"),
                InlineKeyboardButton(text="🟡 O'rta", callback_data="prio_normal"),
            ],
            [
                InlineKeyboardButton(text="🟠 Yuqori", callback_data="prio_high"),
                InlineKeyboardButton(text="🔴 Shoshilinch", callback_data="prio_urgent"),
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="t_cancel")],
        ]
    )


# ── Skrinshot bosqichi (inline) ──
attachment_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Skrinshotsiz davom etish", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="t_cancel")],
    ]
)


# ╔══════════════════════════════════╗
#          TASDIQLASH (inline)
# ╚══════════════════════════════════╝
confirm_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="t_confirm"),
            InlineKeyboardButton(text="🔄 Qaytadan", callback_data="t_restart"),
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="t_cancel")],
    ]
)


# ── Muvaffaqiyatdan keyin ──
def success_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Platformaga kirish", url=LOGIN_URL)],
            [InlineKeyboardButton(text="📋 Murojaatlarim", callback_data="my_tickets")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="to_main")],
        ]
    )


# ── Parolni unutdim oqimi tasdiqlash ──
pwd_confirm_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="pwd_confirm"),
            InlineKeyboardButton(text="🔄 Qaytadan", callback_data="pwd_restart"),
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="t_cancel")],
    ]
)


# ── Yordam / FAQ / Admin (inline) ──
faq_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Parolni o'zim tiklash", url=RESET_URL)],
        [InlineKeyboardButton(text="🆘 Muammo bildirish", callback_data="new_ticket")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="to_main")],
    ]
)

admin_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💬 Admin bilan yozishish", url=SUPPORT_URL)],
        [InlineKeyboardButton(text="🆘 Muammo bildirish", callback_data="new_ticket")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="to_main")],
    ]
)

about_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🆘 Muammo bildirish", callback_data="new_ticket")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="to_main")],
    ]
)

back_to_main_inline = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="to_main")]]
)
