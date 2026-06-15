# 🛠 Wall Street Technic Bot — texnik yordam boti

Texnik nosozliklar, **parolni tiklash** va boshqa murojaatlarni qabul qiluvchi
alohida Telegram bot. Murojaatlar bazaga yoziladi va **Dashboard → Settings →
«Yordam markazi»** bo'limida ko'rinadi. Admin u yerdan javob yozsa — javob
foydalanuvchining shu botiga avtomatik qaytadi.

---

## 1. Botni yaratish (@BotFather)

1. Telegramda [@BotFather](https://t.me/BotFather) ni oching → `/newbot`
2. Nom: `Wall Street Technic`, username: `wall_street_technic_bot` (yoki bo'sh bo'lgan boshqasi)
3. BotFather bergan **tokenni** nusxalang.

## 2. `.env` ga sozlamalarni yozish

```env
TECHNIC_BOT_TOKEN=BOTFATHER_BERGAN_TOKEN
TECHNIC_BOT_USERNAME=wall_street_technic_bot

# (ixtiyoriy) Yangi murojaat kelganda darhol xabar boradigan adminlar chat ID si.
# Bo'sh qoldirsangiz — tizimdagi role=admin foydalanuvchilarning Telegramiga boradi.
TECHNIC_ADMIN_CHAT_IDS=123456789,987654321
```

> Chat ID ni bilish uchun asosiy botda `/id` buyrug'idan foydalaning yoki
> [@userinfobot](https://t.me/userinfobot) ga yozing.

## 3. Migratsiya (faqat birinchi marta)

```bash
python manage.py makemigrations settings_app
python manage.py migrate
```

## 4. Botni ishga tushirish

**Lokalda:**
```bash
python run_technic_bot.py
```

**Hostda (Render / Railway):** `Procfile` ga `technic` jarayoni qo'shilgan:
```
technic: python run_technic_bot.py
```
Render'da bu alohida **Background Worker** sifatida ishga tushiriladi.

---

## Bot imkoniyatlari

| Tugma | Vazifasi |
|-------|----------|
| 🆘 Muammoni bildirish | Kategoriya → tavsif → skrinshot (ixtiyoriy) → aloqa → muhimlik → tasdiq |
| 🔑 Parolni unutdim | Login/telefon so'raydi → admin yangi parolni botga yuboradi |
| 📋 Murojaatlarim | O'z murojaatlari va ularning holatini ko'radi |
| ❓ Savol-javob | Ko'p so'raladigan savollar |
| 👨‍💻 Admin | Admin bilan to'g'ridan-to'g'ri bog'lanish |

**Animatsiyalar:** «yozmoqda…» effekti, to'lib boradigan progress-bar,
muvaffaqiyatda Telegram xabar effektlari (🎉/🔥).

## Admin tomoni (Settings → Yordam markazi)

- Murojaatlarni holat bo'yicha filtrlash (Barchasi / Yangi / Jarayonda / Hal qilingan)
- Har bir murojaatni ochib **javob yozish** + holatni o'zgartirish
  (javob foydalanuvchining Telegramiga ketadi)
- Murojaatni **o'chirish**
- Tab ustida **yangi murojaatlar soni** (qizil badge)

---

## Texnik tafsilotlar

| Komponent | Joylashuv |
|-----------|-----------|
| Bot kodi | `wallstreet/technic_bot/` (bot.py, keyboards.py, states.py, db.py, config.py, storage.py) |
| Launcher | `run_technic_bot.py` |
| Model | `settings_app/models.py → SupportTicket` |
| Admin sahifa | `templates/settings/settings.html` (Yordam markazi tab) |
| View'lar | `settings_app/views.py → ticket_update / ticket_delete` |
| Telegramga javob | `settings_app/notifications.py` |

> Eslatma: `TECHNIC_BOT_TOKEN` bo'sh bo'lsa, web'dan yuborilgan javoblar
> zaxira sifatida asosiy bot tokeni (`TELEGRAM_BOT_TOKEN`) orqali yuboriladi.
