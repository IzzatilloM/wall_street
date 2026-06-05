# -*- coding: utf-8 -*-
"""
Kurs sahifasidagi "Studentlar" ro'yxati (courses.Student — eski model) ni
enrollments.Enrollment asosida to'ldiradi. Shunda kurs kartasida
"Studentlar: N" to'g'ri ko'rinadi va modal ro'yxat to'ladi.

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_course_students.py', encoding='utf-8').read())"
Idempotent.
"""
from courses.models import Student as CourseStudent
from enrollments.models import Enrollment

_STATUS_MAP = {
    'active': 'active',
    'completed': 'active',
    'pending': 'inactive',
    'cancelled': 'inactive',
    'frozen': 'frozen',
}

created = 0
for e in Enrollment.objects.select_related('student', 'course').all():
    if not e.course:
        continue
    full_name = e.student.full_name
    phone = e.student.phone or ''
    status = _STATUS_MAP.get(e.status, 'active')

    obj, was_created = CourseStudent.objects.get_or_create(
        course=e.course,
        full_name=full_name,
        phone=phone,
        defaults={'status': status},
    )
    if not was_created and obj.status != status:
        obj.status = status
        obj.save(update_fields=['status'])
    if was_created:
        created += 1

print(f"Yangi courses.Student: {created}")
print(f"Jami courses.Student: {CourseStudent.objects.count()}")
print("Kurs bo'yicha (kartada ko'rinadigan) student soni:")
from courses.models import Course
for c in Course.objects.order_by('id'):
    print(f"  {c.title}: {c.students.count()}")
