# Wall Street — Deploy va sinov qo'llanmasi (UZ)

Endi **bitta Django backend** ikkala mobil ilovaga ham xizmat qiladi:

| Ilova | Backend manzili |
|-------|-----------------|
| **Talaba** (WallStreetMobile) | `…/api/...` (avvalgidek) |
| **O'qituvchi** (WallStreetTeacherMobile) | `…/api/teacher/...` (YANGI, Django REST) |

> ⚠️ Eski **PHP** `teacher_api` (`D:/davomat/online`) endi **kerak emas** — uning
> o'rniga Django'da `teacher_api` ilovasi yozildi. PHP fayllarni o'chirsangiz ham bo'ladi.

---

## 0. Login ma'lumotlari
Toza bazada seed quyidagini yaratadi (to'liq ro'yxat: `SEED_CREDENTIALS.txt`):
- **Admin:** `Musaev_I` / `izzatillo_2004`
- **O'qituvchi (misol):** `jasur.karimov` / `JasurKarimov@01`
- **Talaba (misol):** `ali.karimov` / `AliKarimov@01`

---

## 1. LOKAL SINOV (hozir, kompyuterda)

**A. Backendni ishga tushiring:**
```bash
cd "D:/Loyihalarim/Wall Street"
.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

**B. O'qituvchi ilovasini lokal backendga ulang** (Flutter web yoki emulyator):
```bash
cd "D:/WallStreetTeacherMobile"
# Flutter web:
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
# Android emulyator bo'lsa: --dart-define=API_BASE_URL=http://10.0.2.2:8000
```
Talaba ilovasi uchun ham xuddi shunday `--dart-define=API_BASE_URL=...`.

---

## 2. ENG TEZ YO'L — mavjud PythonAnywhere'ni yangilash
Talaba backendi allaqachon `wallstreetcrm.pythonanywhere.com` da ishlayapti.
Yangi o'qituvchi API ham xuddi shu repoda — faqat yangilash kerak:

PythonAnywhere **Bash console**'da:
```bash
cd ~/<loyiha-papkangiz>          # masalan: ~/wallstreet
git pull                          # yangi kodni torting
pip install -r requirements.txt   # (dj-database-url, psycopg qo'shilgan)
python manage.py migrate          # teacher_api jadvallari yaratiladi
python manage.py shell -c "exec(open('seed_wallstreet.py', encoding='utf-8').read())"
python manage.py shell -c "exec(open('seed_rename_logins.py', encoding='utf-8').read())"
```
So'ng **Web → Reload**. Tamom — ikkala ilova ham ishlaydi
(ilovalardagi `prodBaseUrl` allaqachon shu manzilga ishora qiladi).

---

## 3. RENDER'GA DEPLOY (yangi, zamonaviy)

1. Loyihani **GitHub**'ga yuklang (private repo bo'lsa ham bo'ladi).
2. [render.com](https://render.com) → **New +** → **Blueprint** → repoyingizni tanlang.
   Render `render.yaml`dan **web servis + PostgreSQL** ni avtomatik yaratadi.
3. Birinchi deployّda `build.sh` o'zi: migratsiya + statik + **seed** ni bajaradi.
4. Deploy tugagach Render domeningiz bo'ladi, masalan:
   `https://wallstreet-crm.onrender.com`
5. **Ilovalardagi manzilni yangilang** (ikkalasida ham `prodBaseUrl`):
   - `D:/WallStreetMobile/lib/core/constants.dart` → `prodBaseUrl`
   - `D:/WallStreetTeacherMobile/lib/core/constants.dart` → `prodBaseUrl`
   Render domeningizga o'zgartiring va APK'ni qayta build qiling.
6. Birinchi deploy'dan keyin Render env'da `RUN_SEED=false` qo'ying
   (qayta seed bo'lmasligi uchun).

### Render env (ixtiyoriy)
- `ANTHROPIC_API_KEY` — AI tahlil (o'qituvchi statistikasi) uchun. Bo'lmasa
  oddiy hisobga asoslangan tahlil chiqadi.
- `BOT_TOKEN` — Telegram bot uchun.

---

## 4. APK build qilish (telefon uchun)
```bash
cd "D:/WallStreetTeacherMobile"
flutter build apk --release --dart-define=API_BASE_URL=https://SIZNING-DOMEN
```
(`--dart-define` bermasangiz `prodBaseUrl` ishlatiladi.)

---

## Eslatma — "Parolni unutdingizmi?"
Ikkala ilovada ham parolni unutgan foydalanuvchi **Adminga (Telegram)** tugmasini
bosadi. Telegram manzilini o'zingiznikiga moslang:
- Talaba: `constants.dart` → `adminTelegramUrl`
- O'qituvchi: `constants.dart` → `adminTelegramUrl`
