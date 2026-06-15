# -*- coding: utf-8 -*-
"""
SEED_CREDENTIALS.txt dagi login/parollarni bazaga moslaydi.
Hujjatdagi har bir foydalanuvchi (admin/teacher/student) o'sha parol bilan
kira olishini kafolatlaydi. plain_password ham yangilanadi (admin ko'rishi uchun).

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_fix_passwords.py', encoding='utf-8').read())"
Idempotent.
"""
import re
from accounts.models import CustomUser

updated, missing = 0, []
with open('SEED_CREDENTIALS.txt', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n')
        # parol ustunida '@' bor (masalan AliKarimov@01) — faqat shunday qatorlar
        if '@' not in line:
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        username, password = tokens[-2], tokens[-1]
        # username odatda nuqta yoki harf bilan; parolda '@' bor
        if '@' not in password:
            continue
        u = CustomUser.objects.filter(username=username).first()
        if not u:
            missing.append(username)
            continue
        u.set_password(password)
        u.plain_password = password
        u.is_active = True
        u.save(update_fields=['password', 'plain_password', 'is_active'])
        updated += 1

print(f"Yangilandi: {updated} | topilmadi: {len(missing)}")
if missing:
    print("Topilmadi:", ', '.join(missing[:20]))
print('TAYYOR.')
