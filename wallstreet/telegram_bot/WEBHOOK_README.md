# Telegram bot — Webhook rejimi (PythonAnywhere BEPUL tarif)

Bot endi alohida jarayon emas. Telegram update'larni saytning
`/tg/webhook/<BOT_TOKEN>/` manziliga POST qiladi, sayt ularni aiogram'ga uzatadi.
**Always-on task / pullik tarif KERAK EMAS.** Bot va sayt bitta bazani (SQLite) baham ko'radi.

## PythonAnywhere'da ishga tushirish

1. **Kodni yuklang** (git pull yoki yuklab) va paketlarni o'rnating:
   ```
   pip install -r requirements-pa.txt
   ```

2. **Migratsiya** (FSM holati jadvali uchun):
   ```
   python manage.py migrate
   ```

3. **.env** ichida domeningizni yozing:
   ```
   WEBSITE_URL=https://FOYDALANUVCHI.pythonanywhere.com
   TELEGRAM_BOT_TOKEN=...   (sizdagi token)
   ```

4. **Web tab → Reload** (saytni qayta yuklang).

5. **Webhook'ni Telegram'ga ro'yxatdan o'tkazing** (BIR MARTA). Bash console'da:
   ```
   cd ~/<loyiha>/wallstreet/telegram_bot
   python set_webhook.py set https://FOYDALANUVCHI.pythonanywhere.com
   ```

6. Tekshirish:
   ```
   python set_webhook.py info
   ```
   yoki brauzerda `https://FOYDALANUVCHI.pythonanywhere.com/tg/webhook/<TOKEN>/`
   ochsangiz "Wall Street bot webhook ✅" chiqadi.

Tayyor — botga `/start` yozib ko'ring.

## Lokal ishlash (polling — eski usul)
Lokalda webhook shart emas, eski polling ishlayveradi:
```
python set_webhook.py delete      # avval webhook'ni o'chiring
python bot.py                     # polling
```
> ⚠️ Polling va webhook bir vaqtda ishlamaydi. Lokalda polling yoqsangiz,
> serverdagi webhook o'chadi — qaytadan `set_webhook.py set ...` qiling.
