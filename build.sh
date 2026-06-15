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

# Admin + 20 o'qituvchi + 50 talaba + kurslarni seed qiladi (idempotent).
# Birinchi deploy uchun shart. Keyin Render env'da RUN_SEED=false qo'ysangiz
# qayta seed bo'lmaydi.
if [ "${RUN_SEED:-true}" = "true" ]; then
  echo ">>> Seed (1/2): seed_wallstreet.py — admin/o'qituvchi/talaba/kurslar..."
  python manage.py shell -c "exec(open('seed_wallstreet.py', encoding='utf-8').read())"
  echo ">>> Seed (2/2): seed_rename_logins.py — loginlarni ism.familiya ko'rinishiga..."
  python manage.py shell -c "exec(open('seed_rename_logins.py', encoding='utf-8').read())"
fi
