# 🤖 2 ta Telegram bot — Render'da WEBHOOK orqali (to'liq yo'riqnoma)

Bu loyihada **2 ta bot** bor va ikkalasi ham bitta web servis ichida, **webhook**
orqali ishlaydi (alohida background worker / pullik tarif KERAK EMAS):

| Bot | Vazifasi | Token (env) |
|-----|----------|-------------|
| Asosiy bot (`@wall_street_crm_bot`) | Ro'yxatdan o'tish, kurslar, ID | `TELEGRAM_BOT_TOKEN` |
| Technic bot (`@wall_street_technic_bot`) | Texnik yordam, parol tiklash | `TECHNIC_BOT_TOKEN` |

Telegram update'lar shu manzilga keladi:
`https://wallstreet-crm.onrender.com/tg/webhook/<BOT_TOKEN>/`
(token bo'yicha qaysi botga tegishli ekani avtomatik aniqlanadi).

---

## ⚙️ Qanday ishlaydi (avtomatik)

Web server (gunicorn) ko'tarilganda `wallstreet/wsgi.py` Telegram'ga `setWebhook`
so'rovini **o'zi yuboradi** — har ikkala bot uchun. Render bepul tarifida Shell
(terminal) yo'q, shuning uchun hech narsani qo'lda terish shart emas.

Shart: Render'da **`WEBSITE_URL`** `https://...` bo'lishi kerak. Aks holda
(lokal `http://...`) webhook o'rnatilmaydi va polling rejimi ishlaydi.

---

## 1️⃣ Render dashboard'da env-larni sozlang

Render → `wallstreet-crm` servisi → **Environment** → quyidagilarni qo'shing/tekshiring:

```
WEBSITE_URL        = https://wallstreet-crm.onrender.com
TELEGRAM_BOT_TOKEN = 8586812566:AAFFwpaHD7tR-nZ_WKkm05hc-YH5tw7yqyk
TECHNIC_BOT_TOKEN  = 8324320210:AAFFJYNEq3eQGRAVu9nfG_hcBih5aU1CJi8
```

> ⚠️ `WEBSITE_URL` eng muhim qator. U bo'lmasa webhook o'rnatilmaydi.

(Ixtiyoriy) Yangi texnik murojaat kelganda darhol xabar olish uchun:
```
TECHNIC_ADMIN_CHAT_IDS = 123456789        # o'z chat ID'ingiz (botda /id orqali)
```

## 2️⃣ Kodni Render'ga yuklang

Yangi kodni GitHub'ga push qiling — Render avtomatik qayta deploy qiladi:
```
git add -A
git commit -m "feat(telegram): 2 bot webhook (auto-set on startup)"
git push
```

## 3️⃣ Tekshiring

Deploy tugagach (1-2 daqiqa):

**a) Brauzerda** quyidagini oching — `Wall Street bot webhook ✅` chiqsa, tayyor:
```
https://wallstreet-crm.onrender.com/tg/webhook/8586812566:AAFFwpaHD7tR-nZ_WKkm05hc-YH5tw7yqyk/
```

**b) Render Logs**'da quyidagi qatorlarni ko'rasiz:
```
✅ Telegram webhook o'rnatildi (asosiy bot): https://.../tg/webhook/.../
✅ Telegram webhook o'rnatildi (technic bot): https://.../tg/webhook/.../
```

**c) Lokal kompyuterdan** holatni so'rang (Telegram'dan o'qiydi):
```
python manage.py tg_webhook info
```
Ikkala botda ham `URL: https://wallstreet-crm.onrender.com/...` ko'rinsa — ishlayapti.

**d)** Telegramda har ikkala botga `/start` yozib ko'ring. ✅

---

## 🛠 Qo'lda boshqarish (ixtiyoriy)

Avtomatik o'rnatish ishlamasa yoki tekshirmoqchi bo'lsangiz, lokal kompyuterdan:

```bash
# Ikkala botga ham Render manzilini o'rnatish:
python manage.py tg_webhook set --base https://wallstreet-crm.onrender.com

# Holatni ko'rish:
python manage.py tg_webhook info

# Webhook'ni o'chirish (lokalda polling sinash uchun):
python manage.py tg_webhook delete
```

---

## ⚠️ Muhim eslatma — POLLING bilan birga ishlatmang

`run_bot.py` / `run_technic_bot.py` (polling) ishga tushganda **webhook o'chib
qoladi** (polling `deleteWebhook` qiladi) va bot Render'da ishlamay qoladi.

- Render'da faqat **web** servis ishlasin (`render.yaml` shunday — worker yo'q).
- `Procfile`'dagi `worker:` / `technic:` qatorlari shu sabab izohga olingan.
- Lokalda polling sinasangiz, keyin `tg_webhook set ...` bilan webhook'ni
  qaytadan o'rnating.

---

## 🔎 Muammolarni bartaraf qilish

| Belgi | Sabab / Yechim |
|-------|----------------|
| Bot javob bermayapti | Render Logs'da `webhook o'rnatildi` borligini, `WEBSITE_URL` to'g'riligini tekshiring |
| Logda `WEBSITE_URL https emas` | Render env'da `WEBSITE_URL=https://wallstreet-crm.onrender.com` qo'ying |
| `tg_webhook info` da `Oxirgi xato` | Telegram URL'ga ulana olmagan — domen/SSL'ni tekshiring |
| Faqat 1 bot ishlayapti | Ikkinchi bot tokeni (env) to'g'ri kiritilganini tekshiring |
| Render uxlab qoladi (bepul tarif) | Bepul servis 15 daqiqa harakatsizlikdan keyin uxlaydi; birinchi xabar botni «uyg'otadi» (~30s kechikish). Doimiy uchun pullik tarif yoki tashqi ping kerak |
