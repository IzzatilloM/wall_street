release: python manage.py migrate --noinput && python manage.py createcachetable && python manage.py collectstatic --noinput
web: gunicorn wallstreet.wsgi --log-file - --bind 0.0.0.0:$PORT

# ⚠️ WEBHOOK rejimi: botlar `web` jarayoni ichida ishlaydi (wsgi.py webhook'ni
# avtomatik o'rnatadi). Quyidagi polling worker'larini ISHGA TUSHIRMANG —
# polling ishga tushganda webhook o'chib qoladi va bot ishlamay qoladi.
# Lokalda polling sinash uchun:  python run_bot.py  /  python run_technic_bot.py
# worker: python run_bot.py
# technic: python run_technic_bot.py
