# 🚀 Wall Street — PythonAnywhere'ga deploy (mobil ilova uchun)

Bu qo'llanma backend'ni PythonAnywhere'ga joylab, mobil ilova **istalgan joydan**
ulanadigan qiladi. Hamma joyda `USERNAME` o'rniga o'z PythonAnywhere
foydalanuvchi nomingizni qo'ying (manzilingiz: `https://USERNAME.pythonanywhere.com`).

> ⚠️ **Bepul tarif = 1 ta web app.** Agar Fan Lider CRM allaqachon shu akkauntning
> bitta bepul web app'ini band qilgan bo'lsa, Wall Street uchun:
> – alohida bepul akkaunt oching (boshqa username), **yoki**
> – pullik tarifga o'ting (bir nechta web app + custom domen).

---

## 1-qadam — Kodni PythonAnywhere'ga yuklash

### Variant A — ZIP yuklash (eng oson, git shart emas)
Kompyuteringizda (loyiha papkasida) ZIP yarating — keraksiz og'ir papkalarsiz:

```powershell
cd "D:\Loyihalarim\Wall Street"
$exclude = @('.venv','staticfiles','__pycache__','.git','node_modules')
$items = Get-ChildItem -Force | Where-Object { $_.Name -notin $exclude }
Compress-Archive -Path $items.FullName -DestinationPath "$env:USERPROFILE\Desktop\wallstreet.zip" -Force
Write-Host "Tayyor: Desktop\wallstreet.zip"
```

> `db.sqlite3` ataylab ZIP ichida qoldiriladi — shunda barcha studentlar
> (51 ta) va `test.student` ham serverga ko'chadi, qaytadan seed qilish shart emas.

So'ng PythonAnywhere'da: **Files** → `wallstreet.zip` ni yuklang → **Bash console** oching:

```bash
cd ~
unzip wallstreet.zip -d wallstreet
cd wallstreet
ls   # manage.py ko'rinishi kerak
```

### Variant B — GitHub orqali (tanlangan usul ✅)
1. Loyihani GitHub'ga push qiling. **Diqqat:** `.env` va `db.sqlite3` repoga
   **kirmaydi** (gitignore qilingan — maxfiy/og'ir fayllar).
2. PythonAnywhere **Bash console**'da klon qiling (`<USERNAME>/<REPO>` ni almashtiring):
   ```bash
   cd ~
   git clone https://github.com/<USERNAME>/<REPO>.git wallstreet
   cd wallstreet
   ls   # manage.py ko'rinishi kerak
   ```
3. **(Ixtiyoriy, tavsiya)** 51 ta studentni saqlamoqchi bo'lsangiz — lokal
   `db.sqlite3` faylni PythonAnywhere **Files** orqali `~/wallstreet/` ga yuklang.
   Yuklamasangiz — 4-qadamda seed bilan qaytadan yaratiladi.

> ⚠️ GitHub'da `.env` **yo'q** — 3-qadamda uni qo'lda yaratasiz. Aks holda
> Gmail kodi va bot ishlamaydi.

---

## 2-qadam — Virtualenv va paketlar

Bash console'da (Django 6 uchun Python 3.12+ kerak):

```bash
cd ~/wallstreet
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pa.txt
```

---

## 3-qadam — `.env` (production sozlamalari)

**GitHub orqali kelgan bo'lsangiz** — `.env` repoda yo'q, uni `.env.example`'dan yarating:
```bash
cd ~/wallstreet
cp .env.example .env
nano .env          # yoki: Files → wallstreet/.env → Edit
```
(ZIP orqali kelgan bo'lsangiz `.env` allaqachon bor — shunchaki tahrirlang.)

`.env` ichida quyidagilar **to'ldirilgan** bo'lishi shart:
```env
SECRET_KEY=uzun-tasodifiy-maxfiy-kalit
DEBUG=False
ALLOWED_HOSTS=USERNAME.pythonanywhere.com
WEBSITE_URL=https://USERNAME.pythonanywhere.com

# Gmail — bularsiz ro'yxatdan o'tishda KOD KELMAYDI
EMAIL_HOST_USER=sizning@gmail.com
EMAIL_HOST_PASSWORD=gmail-app-parol-16-belgi

# Telegram bot — busiz bot KODI KELMAYDI
TELEGRAM_BOT_TOKEN=bot-token
```

> 💡 `EMAIL_HOST_USER/PASSWORD`, `TELEGRAM_BOT_TOKEN` va `SECRET_KEY` qiymatlarini
> **lokal kompyuteringizdagi `.env` faylidan** ko'chiring (ular o'sha yerda bor).
> `ALLOWED_HOSTS` standart sozlamada ham `.pythonanywhere.com` ni qabul qiladi,
> lekin aniq yozish xavfsizroq.

---

## 4-qadam — Migratsiya, statik fayllar, seed

```bash
cd ~/wallstreet
source .venv/bin/activate
python manage.py migrate
python manage.py createcachetable
python manage.py collectstatic --noinput
```

**Bazani to'ldirish — 2 holat:**

- **`db.sqlite3` ni Files orqali yuklagan bo'lsangiz** — hamma narsa (51 student,
  test.student) allaqachon bor, seed shart emas. Faqat tasdiqlash uchun:
  ```bash
  python manage.py shell -c "exec(open('seed_test_student.py', encoding='utf-8').read())"
  ```

- **Bazani yuklamagan bo'lsangiz** (bo'sh, yangi baza) — to'liq demo ma'lumotni yarating
  (admin `Musaev_I`, 20 o'qituvchi, 50 student, 20 kurs — idempotent):
  ```bash
  python manage.py shell < seed_wallstreet.py
  python manage.py shell -c "exec(open('seed_test_student.py', encoding='utf-8').read())"
  ```

---

## 5-qadam — Web app sozlash (Web tab)

1. **Web** → **Add a new web app** → **Manual configuration** → **Python 3.12**.
2. **Virtualenv** bo'limiga:
   ```
   /home/USERNAME/wallstreet/.venv
   ```
3. **Code → Source code** va **Working directory**:
   ```
   /home/USERNAME/wallstreet
   ```
4. **WSGI configuration file** havolasini bosing va ICHINI butunlay quyidagiga almashtiring
   (`USERNAME` ni almashtiring):

   ```python
   import os, sys

   path = '/home/USERNAME/wallstreet'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'wallstreet.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

5. **Static files** bo'limiga 2 ta qator qo'shing:

   | URL | Directory |
   |-----|-----------|
   | `/static/` | `/home/USERNAME/wallstreet/staticfiles` |
   | `/media/`  | `/home/USERNAME/wallstreet/media` |

6. Tepadagi yashil **Reload** tugmasini bosing.

---

## 6-qadam — Serverni tekshirish (deploydan keyin)

Brauzerda yoki Bash console'da:

```bash
# Yangiliklar (ochiq endpoint) — JSON qaytishi kerak
curl https://USERNAME.pythonanywhere.com/api/news/

# Login — access/refresh/user qaytishi kerak
curl -X POST https://USERNAME.pythonanywhere.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test.student","password":"Test@2026"}'
```

`access` token qaytsa — backend tayyor. ✅

---

## 7-qadam — Mobil ilovani shu manzilga ulash + APK qurish

Ilova manzilini deploy qilingan manzilga o'zgartiring. **2 yo'l bor:**

**Yo'l 1 — kodda (doimiy):** `D:\WallStreetMobile\lib\core\constants.dart` da
`defaultValue` ni o'zgartiring:
```dart
defaultValue: 'https://USERNAME.pythonanywhere.com',
```

**Yo'l 2 — qurishda (kodga tegmasdan):** `build_apk.bat` dan oldin:
```powershell
set API_BASE_URL=https://USERNAME.pythonanywhere.com
```
keyin `build_apk.bat` ni ishga tushiring.

So'ng APK tayyor bo'ladi:
```
D:\WallStreetMobile\build\app\outputs\flutter-apk\app-release.apk
```
Telefonga o'rnatib, `test.student` / `Test@2026` bilan kiring — **internetsiz
muammosi yo'qoladi**, chunki manzil endi real internetда.

---

## ✅ Yakuniy tekshiruv ro'yxati
- [ ] `https://USERNAME.pythonanywhere.com/api/news/` JSON qaytaradi
- [ ] `/api/auth/login/` `test.student` uchun token qaytaradi
- [ ] APK shu manzil bilan qurilgan (LAN IP emas)
- [ ] Telefonda login ishlaydi, "Mening kurslarim" va "To'lovlar" ko'rinadi
- [ ] Telegram tugmasi kanalni ochadi

> **Telegram bot** (`run_bot.py`) bepul PythonAnywhere'da 24/7 ishlamaydi
> (always-on task — pullik). Bot kerak bo'lsa: pullik tarif yoki Railway/VPS.
> Mobil ilova uchun esa faqat yuqoridagi **web/API** yetarli.
