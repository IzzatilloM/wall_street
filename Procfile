release: python manage.py migrate --noinput && python manage.py createcachetable && python manage.py collectstatic --noinput
web: gunicorn wallstreet.wsgi --log-file - --bind 0.0.0.0:$PORT
worker: python run_bot.py
