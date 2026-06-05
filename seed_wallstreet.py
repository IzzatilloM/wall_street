# -*- coding: utf-8 -*-
"""
Wall Street CRM — to'liq seed skripti.

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell < seed_wallstreet.py

Bajaradi:
  1) Admin Musaev_I paroliga izzatillo_2004 ni o'rnatadi.
  2) 20 ta o'qituvchi (teacher) + Instructor profili (barcha maydonlar).
  3) 50 ta talaba (student) + ilova uchun username/parol.
  4) 20 ta ingliz tili kursi (CEFR / IELTS / General English ...).
Idempotent: qayta ishga tushsa dublikat yaratmaydi.
"""
import secrets
from datetime import date

from django.db import transaction
from django.contrib.auth import authenticate

from accounts.models import CustomUser
from students.models import Student
from instructors.models import Instructor
from courses.models import Course

DIV = "=" * 60
created_accounts = []  # (rol, login, parol) — chop etish uchun


# ══════════════════════════════════════════════════════
# 1) ADMIN PAROLI
# ══════════════════════════════════════════════════════
admin = CustomUser.objects.filter(username="Musaev_I").first()
if not admin:
    admin = CustomUser.objects.create_user(
        username="Musaev_I", password="izzatillo_2004",
        first_name="Izzatillo", last_name="Musayev",
    )
    admin.role = "admin"
admin.set_password("izzatillo_2004")
admin.role = "admin"
admin.is_staff = True          # admin panelga kirishi uchun
admin.is_superuser = True
admin.is_verified = True
if not admin.first_name:
    admin.first_name = "Izzatillo"
if not admin.last_name:
    admin.last_name = "Musayev"
admin.save()
print(f"[1] Admin tayyor: Musaev_I / izzatillo_2004  "
      f"(auth check: {authenticate(username='Musaev_I', password='izzatillo_2004') is not None})")


# ══════════════════════════════════════════════════════
# 2) 20 TA O'QITUVCHI  → Instructor profili
# ══════════════════════════════════════════════════════
TEACHERS = [
    ("Jasur", "Karimov", "IELTS Speaking & Writing", 7, 850, "Toshkent, Chilonzor", "IELTS bo'yicha 8.0 bandga ega tajribali o'qituvchi."),
    ("Dilnoza", "Rahimova", "General English", 5, 650, "Toshkent, Yunusobod", "Boshlang'ich va o'rta darajalar bo'yicha mutaxassis."),
    ("Sardor", "Tursunov", "CEFR B2/C1", 6, 720, "Toshkent, Mirzo Ulug'bek", "CEFR imtihonlariga tayyorlash bo'yicha ekspert."),
    ("Madina", "Yusupova", "IELTS Reading & Listening", 4, 600, "Toshkent, Sergeli", "Akademik IELTS yo'nalishi o'qituvchisi."),
    ("Bekzod", "Aliyev", "Business English", 8, 900, "Toshkent, Shayxontohur", "Korporativ ingliz tili kurslari murabbiyi."),
    ("Nilufar", "Sobirova", "Grammar & Vocabulary", 5, 640, "Toshkent, Olmazor", "Grammatika asoslari bo'yicha kuchli metodist."),
    ("Otabek", "Nazarov", "Pre-IELTS", 3, 550, "Toshkent, Bektemir", "IELTS oldidan tayyorgarlik guruhlari o'qituvchisi."),
    ("Gulnoza", "Ismoilova", "Speaking Club", 6, 700, "Toshkent, Yashnobod", "Speaking ko'nikmalarini rivojlantirish bo'yicha murabbiy."),
    ("Aziz", "Qodirov", "Academic Writing", 7, 820, "Toshkent, Chilonzor", "Akademik yozuv va esse yozish ustasi."),
    ("Shahnoza", "Ergasheva", "General English", 4, 580, "Toshkent, Yunusobod", "Elementary va Pre-Intermediate guruhlar uchun."),
    ("Javlon", "Mahmudov", "IELTS Intensive", 9, 950, "Toshkent, Mirobod", "Intensiv IELTS kurslari bosh o'qituvchisi."),
    ("Kamola", "Hasanova", "Phonetics & Pronunciation", 5, 660, "Toshkent, Uchtepa", "Talaffuz va fonetika bo'yicha mutaxassis."),
    ("Rustam", "Sodiqov", "CEFR A1-A2", 4, 590, "Toshkent, Sergeli", "Boshlang'ich darajalar bo'yicha o'qituvchi."),
    ("Sevara", "Tojiboyeva", "Kids English", 6, 680, "Toshkent, Olmazor", "Bolalar uchun ingliz tili dasturi murabbiyi."),
    ("Eldor", "Xolmatov", "IELTS Writing Task 2", 8, 880, "Toshkent, Yakkasaroy", "Writing Task 2 bo'yicha chuqur tahlil ustasi."),
    ("Munisa", "Abdullayeva", "Conversation Course", 5, 630, "Toshkent, Yashnobod", "Erkin muloqot va so'zlashuv kurslari."),
    ("Firdavs", "Rasulov", "Upper-Intermediate", 7, 780, "Toshkent, Mirzo Ulug'bek", "Yuqori o'rta daraja guruhlari o'qituvchisi."),
    ("Zarina", "Mirzayeva", "General English", 3, 540, "Toshkent, Bektemir", "Yangi boshlovchilar uchun ingliz tili."),
    ("Akmal", "Yo'ldoshev", "Test Strategies", 6, 740, "Toshkent, Shayxontohur", "Imtihon strategiyalari bo'yicha murabbiy."),
    ("Feruza", "Saidova", "Advanced English", 9, 920, "Toshkent, Chilonzor", "Advanced (C1) daraja o'qituvchisi."),
]

instructors = []
for i, (fn, ln, specialty, exp, salary, addr, bio) in enumerate(TEACHERS, 1):
    username = f"teacher{i:02d}"
    password = "Teacher@2025"
    with transaction.atomic():
        u, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={"first_name": fn, "last_name": ln,
                      "email": f"{username}@wallstreet.uz"},
        )
        u.first_name = fn
        u.last_name = ln
        u.email = f"{username}@wallstreet.uz"
        u.phone = f"+99890{700000 + i:06d}"
        u.role = "teacher"
        u.is_verified = True
        u.set_password(password)
        u.save()  # signal Instructor profilini yaratadi

        inst = Instructor.objects.get(user=u)
        inst.full_name = f"{fn} {ln}"
        inst.specialty = specialty
        inst.experience_years = exp
        inst.salary = salary
        inst.address = addr
        inst.bio = bio
        inst.is_active = True
        inst.save()
        instructors.append(inst)
    created_accounts.append(("teacher", username, password))

print(f"[2] O'qituvchilar: {Instructor.objects.filter(user__role='teacher').count()} ta "
      f"(jami instructor: {Instructor.objects.count()})")


# ══════════════════════════════════════════════════════
# 3) 50 TA TALABA  → ilova uchun username/parol
# ══════════════════════════════════════════════════════
FIRST_NAMES = [
    "Ali", "Vali", "Hasan", "Husan", "Sardor", "Bekzod", "Jasur", "Otabek",
    "Aziz", "Akmal", "Eldor", "Firdavs", "Rustam", "Javlon", "Sherzod",
    "Dilnoza", "Madina", "Nilufar", "Gulnoza", "Shahnoza", "Kamola",
    "Sevara", "Munisa", "Zarina", "Feruza", "Malika", "Ozoda", "Nodira",
    "Sabina", "Diyora",
]
LAST_NAMES = [
    "Karimov", "Rahimov", "Tursunov", "Yusupov", "Aliyev", "Sobirov",
    "Nazarov", "Ismoilov", "Qodirov", "Ergashev", "Mahmudov", "Hasanov",
    "Sodiqov", "Xolmatov", "Rasulov", "Mirzayev", "Yo'ldoshev", "Saidov",
    "Abdullayev", "Tojiboyev",
]

for i in range(1, 51):
    fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
    ln = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
    username = f"student{i:02d}"
    password = "Student@2025"
    phone = f"+99891{100000 + i:06d}"
    parent_phone = f"+99893{200000 + i:06d}"
    email = f"{username}@wallstreet.uz"
    gender = "male" if (i % 2 == 1) else "female"
    bdate = date(2005 + (i % 6), ((i % 12) + 1), ((i % 27) + 1))

    with transaction.atomic():
        u, _ = CustomUser.objects.get_or_create(
            username=username,
            defaults={"first_name": fn, "last_name": ln, "email": email},
        )
        u.first_name = fn
        u.last_name = ln
        u.email = email
        u.phone = phone
        u.role = "student"
        u.is_verified = True
        u.set_password(password)
        u.save()

        st = Student.objects.filter(user=u).first()
        if not st:
            # telefon/email unique — mavjudini ham tekshiramiz
            st = Student.objects.filter(phone=phone).first()
        if not st:
            st = Student(user=u)
        st.user = u
        st.first_name = fn
        st.last_name = ln
        st.phone = phone
        st.parent_phone = parent_phone
        st.email = email
        st.gender = gender
        st.birth_date = bdate
        st.address = f"Toshkent shahri, {i}-uy"
        st.coins = 50 + (i * 3)
        st.is_active = True
        st.save()
    created_accounts.append(("student", username, password))

print(f"[3] Talabalar: {Student.objects.count()} ta "
      f"(student rolidagi user: {CustomUser.objects.filter(role='student').count()})")


# ══════════════════════════════════════════════════════
# 4) 20 TA INGLIZ TILI KURSI
# ══════════════════════════════════════════════════════
def pick_teacher(idx):
    return instructors[idx % len(instructors)] if instructors else None

COURSES = [
    # (title, level, duration_value, duration_unit, price, description)
    ("General English — Beginner",          "beginner",           6, "month", 350, "Noldan boshlovchilar uchun ingliz tili asoslari."),
    ("General English — Elementary",        "elementary",         6, "month", 380, "Elementary daraja: kundalik muloqot va grammatika."),
    ("General English — Pre-Intermediate",  "pre_intermediate",   6, "month", 420, "Pre-Intermediate daraja: lug'at va gap tuzilishi."),
    ("General English — Intermediate",      "intermediate",       6, "month", 450, "Intermediate daraja: erkin so'zlashuv va yozuv."),
    ("General English — Upper-Intermediate","upper_intermediate", 6, "month", 500, "Upper-Intermediate daraja: murakkab matnlar bilan ishlash."),
    ("General English — Advanced",          "advanced",           6, "month", 550, "Advanced (C1) daraja: professional ingliz tili."),
    ("CEFR A1",                             "beginner",           4, "month", 360, "CEFR A1 darajasiga tayyorlov kursi."),
    ("CEFR A2",                             "elementary",         4, "month", 390, "CEFR A2 darajasiga tayyorlov kursi."),
    ("CEFR B1",                             "intermediate",       4, "month", 440, "CEFR B1 sertifikatiga tayyorgarlik."),
    ("CEFR B2",                             "upper_intermediate", 5, "month", 520, "CEFR B2 sertifikatiga chuqur tayyorgarlik."),
    ("CEFR C1",                             "advanced",           5, "month", 600, "CEFR C1 yuqori darajaga tayyorlov."),
    ("Pre-IELTS",                           "pre_intermediate",   3, "month", 430, "IELTS oldidan asosiy ko'nikmalarni mustahkamlash."),
    ("IELTS Foundation",                    "foundation",         3, "month", 480, "IELTS imtihoniga kirish darajasi."),
    ("IELTS General",                       "ielts",              4, "month", 600, "IELTS General Training moduli."),
    ("IELTS Academic",                      "ielts",              4, "month", 650, "IELTS Academic moduli — 6.5+ band uchun."),
    ("IELTS Intensive 7.0+",                "pro",                3, "month", 750, "Intensiv IELTS kursi — 7.0+ band maqsadi."),
    ("English Speaking Club",               "standard",           3, "month", 300, "Erkin so'zlashuv va muloqot amaliyoti."),
    ("Business English",                    "standard",           5, "month", 580, "Biznes va ish muhiti uchun ingliz tili."),
    ("Academic Writing",                    "standard",           4, "month", 520, "Akademik yozuv va esse tuzish ko'nikmalari."),
    ("Kids English",                        "beginner",           8, "month", 320, "Bolalar uchun o'yin asosida ingliz tili."),
]

for idx, (title, level, dval, dunit, price, desc) in enumerate(COURSES):
    Course.objects.update_or_create(
        title=title,
        defaults={
            "category": "english",
            "level": level,
            "teacher": pick_teacher(idx),
            "duration_value": dval,
            "duration_unit": dunit,
            "price": price,
            "description": desc,
            "is_active": True,
        },
    )

print(f"[4] Kurslar: {Course.objects.count()} ta "
      f"(faol english: {Course.objects.filter(category='english', is_active=True).count()})")


# ══════════════════════════════════════════════════════
# YAKUNIY HISOBOT — login ma'lumotlari faylga yoziladi
# ══════════════════════════════════════════════════════
with open("SEED_CREDENTIALS.txt", "w", encoding="utf-8") as f:
    f.write("WALL STREET CRM — KIRISH MA'LUMOTLARI\n")
    f.write(DIV + "\n")
    f.write("ADMIN:    Musaev_I / izzatillo_2004\n")
    f.write(DIV + "\n")
    f.write("O'QITUVCHILAR (parol: Teacher@2025):\n")
    for role, login, pw in created_accounts:
        if role == "teacher":
            f.write(f"  {login} / {pw}\n")
    f.write(DIV + "\n")
    f.write("TALABALAR — ilova kirish (parol: Student@2025):\n")
    for role, login, pw in created_accounts:
        if role == "student":
            f.write(f"  {login} / {pw}\n")

print("\n" + DIV)
print("SEED YAKUNLANDI")
print(f"  Admin:        Musaev_I / izzatillo_2004")
print(f"  O'qituvchi:   teacher01..teacher20 / Teacher@2025")
print(f"  Talaba:       student01..student50 / Student@2025")
print(f"  Kurslar:      {Course.objects.count()} ta ingliz tili kursi")
print("  Ma'lumotlar:  SEED_CREDENTIALS.txt fayliga saqlandi")
print(DIV)
