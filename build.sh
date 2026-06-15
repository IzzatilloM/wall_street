#!/usr/bin/env bash
# ============================================================
# Render build bosqichi — Wall Street CRM (Django)
# Render dashboard yoki render.yaml buni "buildCommand" sifatida chaqiradi.
# ============================================================
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Statik fayllar (WhiteNoise uzatadi)
python manage.py collectstatic --no-input

# Bazani yaratish / yangilash
python manage.py migrate --no-input

# Cache jadvali (settings.CACHES = DatabaseCache "cache_table" ishlatadi).
# Bo'lmasa cache operatsiyalari xato beradi. Idempotent — qayta yaratmaydi.
python manage.py createcachetable

# Admin + o'qituvchi + talaba + kurslarni seed qiladi — FAQAT birinchi deploy uchun.
# ⚠️ Default = false: takror seed dublikat user yaratadi / login nomlarini qayta
# nomlashda "duplicate key" xatosi beradi va deployni yiqitadi. Birinchi deployda
# bir marta RUN_SEED=true qo'ying, muvaffaqiyatdan keyin false ga qaytaring.
# `|| echo ...` — seed yiqilsa ham deploy davom etadi (seed ixtiyoriy, sayt'ga shart emas).
if [ "${RUN_SEED:-false}" = "true" ]; then
  echo ">>> Seed (1/2): seed_wallstreet.py — admin/o'qituvchi/talaba/kurslar..."
  python manage.py shell -c "exec(open('seed_wallstreet.py', encoding='utf-8').read())" \
    || echo "⚠️ Seed 1 o'tkazib yuborildi (xato yoki allaqachon mavjud)."
  echo ">>> Seed (2/2): seed_rename_logins.py — loginlarni ism.familiya ko'rinishiga..."
  python manage.py shell -c "exec(open('seed_rename_logins.py', encoding='utf-8').read())" \
    || echo "⚠️ Seed 2 o'tkazib yuborildi (xato yoki allaqachon mavjud)."
fi
