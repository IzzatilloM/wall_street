# -*- coding: utf-8 -*-
"""
Mavjud o'qituvchi/talaba akkauntlari uchun ochiq parol (plain_password)
nusxasini SEED_CREDENTIALS.txt faylidan to'ldiradi.

Django asosiy parolni hash qiladi va uni qaytarib bo'lmaydi — shuning uchun
sozlamalar bo'limida parol ko'rinishi uchun ushbu fayldagi ma'lum parollar
ochiq holda yoziladi. Fayl topilmasa yoki o'qib bo'lmasa — hech narsa
qilinmaydi (migratsiya baribir muvaffaqiyatli o'tadi).
"""
import os
import re

from django.conf import settings
from django.db import migrations


def _parse_credentials(path):
    """username -> password lug'atini qaytaradi."""
    creds = {}
    try:
        with open(path, encoding='utf-8') as f:
            lines = f.readlines()
    except OSError:
        return creds

    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()
        if not stripped:
            continue

        # ADMIN:    Musaev_I / izzatillo_2004
        if stripped.upper().startswith('ADMIN:'):
            m = re.search(r':\s*(\S+)\s*/\s*(\S+)', stripped)
            if m:
                creds[m.group(1)] = m.group(2)
            continue

        # Ism familiya   username   PAROL  (kamida 2 bo'shliq bilan ajratilgan)
        parts = re.split(r'\s{2,}', stripped)
        if len(parts) != 3:
            continue
        _name, username, password = parts
        # sarlavha/ajratuvchi qatorlarni o'tkazib yuboramiz
        if not username or ' ' in password:
            continue
        if username.upper() == 'USERNAME' or password.upper() == 'PAROL':
            continue
        creds[username] = password

    return creds


def backfill(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')

    path = os.path.join(str(settings.BASE_DIR), 'SEED_CREDENTIALS.txt')
    creds = _parse_credentials(path)
    if not creds:
        return

    for username, password in creds.items():
        (CustomUser.objects
         .filter(username=username)
         .exclude(plain_password=password)
         .update(plain_password=password))


def noop(apps, schema_editor):
    # Orqaga qaytarishda ochiq parolni tozalaymiz (xavfsizlik uchun)
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.exclude(plain_password='').update(plain_password='')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_plain_password'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
