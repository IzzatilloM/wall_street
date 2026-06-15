"""
Gunicorn sozlamalari — Render BEPUL tarif (512MB RAM, sekin cold-start) uchun.
Gunicorn ishga tushganda shu faylni (joriy papkadagi gunicorn.conf.py) avtomatik
o'qiydi — startCommand'ni o'zgartirish shart emas.
"""

# Bitta worker — 512MB xotirada bir nechta worker OOM (out of memory) beradi.
workers = 1

# Sync worker ichida bir nechta so'rovni navbatda emas, parallel ko'tarish uchun
# thread'lar (webhook + sayt bir vaqtda javob bersin).
threads = 4

# Cold-start (~50s) + og'ir import (aiogram) + webhook ishlovi uchun yetarli vaqt.
# Default 30s — kam edi va worker o'lib, 502 berardi.
timeout = 120
graceful_timeout = 120

# Uzoq uxlagandan keyin ulanishni barqaror tutadi.
keepalive = 5
