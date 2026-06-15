# -*- coding: utf-8 -*-
"""
Davomat (attendance.Attendance) va coin tarixi (attendance.CoinAward) uchun
demo ma'lumot. Teacher ilovasida davomat tarixi, student ilovasida darslar va
coin tarixi bo'sh ko'rinmasligi uchun.

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_attendance_demo.py', encoding='utf-8').read())"
Idempotent (mavjud sana uchun qayta yozmaydi).
"""
from datetime import timedelta
from django.utils import timezone

from attendance.models import Course as AttCourse, Student as AttStudent, Attendance, CoinAward
from students.models import Student as CRMStudent

today = timezone.localdate()

# Oxirgi 8 ta dars sanasi (dush/chor/jum tariqasida — har 2 kunda)
lesson_dates = [today - timedelta(days=2 * i) for i in range(8)]
lesson_dates.reverse()

STATUS_CYCLE = ['present', 'present', 'present', 'late', 'present', 'absent', 'present', 'present']

att_created = 0
for ac in AttCourse.objects.select_related('instructor').all():
    students = list(ac.students.all().order_by('id'))
    if not students:
        continue
    for di, d in enumerate(lesson_dates):
        for si, st in enumerate(students):
            status = STATUS_CYCLE[(di + si) % len(STATUS_CYCLE)]
            obj, was = Attendance.objects.get_or_create(
                student=st, course=ac, date=d,
                defaults={'status': status, 'marked_by': ac.instructor},
            )
            if was:
                att_created += 1

print(f"Attendance yangi: {att_created} | jami: {Attendance.objects.count()}")

# ─── Coin tarixi: har bir studentning coin balansini bir necha awardga bo'lamiz ───
REASONS = ['Faol ishtirok', 'Uy vazifasi a\'lo', 'Test natijasi', 'Yordam berdi', 'Davomat 100%']
ca_created = 0
for ats in AttStudent.objects.select_related('user').all():
    crm = CRMStudent.objects.filter(user=ats.user).first()
    if not crm or crm.coins <= 0:
        continue
    if CoinAward.objects.filter(student=ats).exists():
        continue  # idempotent
    total = crm.coins
    # 3 ta awardga bo'lamiz
    parts = [total // 2, total // 3, total - (total // 2) - (total // 3)]
    for i, amt in enumerate(parts):
        if amt <= 0:
            continue
        CoinAward.objects.create(
            student=ats, amount=amt,
            reason=REASONS[i % len(REASONS)],
            awarded_by=ats.courses.first().instructor if ats.courses.exists() else None,
        )
        ca_created += 1

print(f"CoinAward yangi: {ca_created} | jami: {CoinAward.objects.count()}")
print('TAYYOR.')
