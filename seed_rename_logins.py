# -*- coding: utf-8 -*-
"""
Har bir o'qituvchi va talabaning username/parolini ism-familiyasiga
mos ravishda (har xil) qilib yangilaydi.

Ishga tushirish:
    .venv/Scripts/python.exe manage.py shell -c "exec(open('seed_rename_logins.py', encoding='utf-8').read())"

  username:  ism.familiya  (lotin, kichik harf; dublikatlarda raqam qo'shiladi)
  parol:     IsmFamiliya@NN (har kishida har xil)
Enrollment/Student bog'lanishlari o'zgarmaydi (FK obyektga bog'lanadi).
"""
import re
import unicodedata

from accounts.models import CustomUser
from students.models import Student
from instructors.models import Instructor

# Lotin translit: apostrof/maxsus belgilarni tozalash
_REPLACE = {
    "o‘": "o", "o'": "o", "g‘": "g", "g'": "g",
    "‘": "", "'": "", "ʻ": "", "`": "", "ʼ": "",
}


def _ascii(s: str) -> str:
    s = (s or "").strip()
    for a, b in _REPLACE.items():
        s = s.replace(a, b)
    # diakritiklarni olib tashlash
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z]", "", s)
    return s


used = set(
    CustomUser.objects.exclude(role__in=["teacher", "student"])
    .values_list("username", flat=True)
)  # admin va boshqalarni band deb belgilaymiz


def make_username(first: str, last: str) -> str:
    base = f"{_ascii(first).lower()}.{_ascii(last).lower()}".strip(".")
    if not base or base == ".":
        base = "user"
    uname = base
    i = 1
    while uname in used:
        i += 1
        uname = f"{base}{i}"
    used.add(uname)
    return uname


def make_password(first: str, last: str, seq: int) -> str:
    f = _ascii(first).capitalize() or "User"
    l = _ascii(last).capitalize() or "X"
    return f"{f}{l}@{seq:02d}"


creds_teacher = []
creds_student = []

# ── O'QITUVCHILAR ──────────────────────────────────────
seq = 0
for inst in Instructor.objects.filter(user__role="teacher").order_by("id"):
    u = inst.user
    first = u.first_name or (inst.full_name.split(" ")[0] if inst.full_name else "")
    last = u.last_name or (inst.full_name.split(" ", 1)[1] if " " in (inst.full_name or "") else "")
    seq += 1
    uname = make_username(first, last)
    pwd = make_password(first, last, seq)
    u.username = uname
    u.set_password(pwd)
    u.save()
    creds_teacher.append((inst.full_name or f"{first} {last}".strip(), uname, pwd))

# ── TALABALAR ──────────────────────────────────────────
seq = 0
for st in Student.objects.all().order_by("id"):
    seq += 1
    uname = make_username(st.first_name, st.last_name)
    pwd = make_password(st.first_name, st.last_name, seq)
    if st.user:
        u = st.user
    else:
        u = CustomUser(role="student", is_verified=True)
    u.username = uname
    u.first_name = st.first_name
    u.last_name = st.last_name
    u.role = "student"
    u.is_verified = True
    u.set_password(pwd)
    u.save()
    if not st.user:
        st.user = u
        st.save()
    creds_student.append((st.full_name, uname, pwd))

# ── HISOBOT FAYLI ──────────────────────────────────────
with open("SEED_CREDENTIALS.txt", "w", encoding="utf-8") as f:
    f.write("WALL STREET CRM — KIRISH MA'LUMOTLARI (ism-familiyaga mos)\n")
    f.write("=" * 64 + "\n")
    f.write("ADMIN:    Musaev_I / izzatillo_2004\n")
    f.write("=" * 64 + "\n")
    f.write(f"O'QITUVCHILAR ({len(creds_teacher)} ta):\n")
    f.write(f"{'ISM FAMILIYA':<28}{'USERNAME':<24}PAROL\n")
    f.write("-" * 64 + "\n")
    for name, un, pw in creds_teacher:
        f.write(f"{name:<28}{un:<24}{pw}\n")
    f.write("=" * 64 + "\n")
    f.write(f"TALABALAR ({len(creds_student)} ta) — tizim va ilova kirish:\n")
    f.write(f"{'ISM FAMILIYA':<28}{'USERNAME':<24}PAROL\n")
    f.write("-" * 64 + "\n")
    for name, un, pw in creds_student:
        f.write(f"{name:<28}{un:<24}{pw}\n")

print(f"O'qituvchilar yangilandi: {len(creds_teacher)}")
print(f"Talabalar yangilandi:     {len(creds_student)}")
print("Namuna o'qituvchilar:")
for row in creds_teacher[:3]:
    print("  ", row)
print("Namuna talabalar:")
for row in creds_student[:3]:
    print("  ", row)
print("To'liq ro'yxat: SEED_CREDENTIALS.txt")
