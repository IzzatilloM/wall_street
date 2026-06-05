# 🚀 Wall Street CRM — Deploy qo'llanmasi

Loyiha ikki qismdan iborat:
1. **Web (Django)** — CRM platforma
2. **Worker (Telegram bot)** — `run_bot.py`

Ikkalasi ham bitta repozitoriydan ishlaydi va bitta `.env` dan o'qiydi.

---

## 0. Tayyorgarlik (har qanday host uchun)

`.env.example` ni `.env` ga ko'chiring va to'ldiring:

```bash
cp .env.example .env
```

Eng muhim o'zgaruvchilar:
- `SECRET_KEY` — yangi maxfiy kalit
- `DEBUG=False` (productionda)
- `ALLOWED_HOSTS=sizning-domeningiz`
- `WEBSITE_URL=https://sizning-domeningiz`  ← **bot tugmalari shu yerga olib o'tadi**
- `TELEGRAM_BOT_TOKEN=...`
- Gmail SMTP sozlamalari

---

## A) Railway (tavsiya etiladi — bot + web birga)

1. GitHub ga push qiling.
2. Railway → **New Project → Deploy from GitHub repo**.
3. **Variables** bo'limiga `.env` dagi barcha o'zgaruvchilarni qo'shing.
   - `WEBSITE_URL` ni Railway bergan domenga qo'ying (masalan `https://wallstreet.up.railway.app`).
4. Railway `Procfile` ni avtomatik o'qiydi. Unda 3 ta process bor:
   - `release` → migratsiya + cache jadvali + statik fayllar
   - `web` → Django (gunicorn)
   - `worker` → Telegram bot
5. **Settings → Services** da `worker` xizmatini yoqing (bot doimiy ishlashi uchun).

> Eslatma: SQLite Railway da vaqtinchalik. Doimiy ma'lumot uchun PostgreSQL plugin
> qo'shib, `DATABASES` ni `dj-database-url` orqali ulang.

---

## B) PythonAnywhere

### Web (Django)
1. **Web** tab → Manual config (Python 3.12).
2. Virtualenv yarating va `pip install -r requirements.txt`.
3. WSGI faylida `DJANGO_SETTINGS_MODULE = 'wallstreet.settings'`.
4. **Static files**: URL `/static/` → `staticfiles/` papka.
5. Konsolda:
   ```bash
   python manage.py migrate
   python manage.py createcachetable
   python manage.py collectstatic --noinput
   ```

### Bot (Always-on task)
**Tasks** tab → **Always-on task** qo'shing:
```bash
python /home/FOYDALANUVCHI/Wall-Street/run_bot.py
```
Bu bot 24/7 ishlashini ta'minlaydi.

---

## C) VPS (qo'shimcha variant)

```bash
# Web
gunicorn wallstreet.wsgi --bind 0.0.0.0:8000

# Bot (alohida systemd service yoki screen/tmux)
python run_bot.py
```

`systemd` namuna (`/etc/systemd/system/wallstreet-bot.service`):
```ini
[Unit]
Description=Wall Street Telegram Bot
After=network.target

[Service]
WorkingDirectory=/srv/wallstreet
ExecStart=/srv/wallstreet/.venv/bin/python run_bot.py
Restart=always
EnvironmentFile=/srv/wallstreet/.env

[Install]
WantedBy=multi-user.target
```

---

## ✅ Deploydan keyin tekshiruv

- [ ] Sayt ochiladi, login/register ishlaydi
- [ ] Botda `/start` → Chat ID chiqadi
- [ ] Botda «📝 Ro'yxatdan o'tish» → talaba tizimga qo'shiladi
- [ ] Botdagi «🎓 Kurslar», «📊 Platforma» tugmalari saytga olib o'tadi
- [ ] Gmail orqali ro'yxatdan o'tishda kod keladi (Inbox)
