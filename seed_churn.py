"""Prezentatsiya skrinshoti uchun AI churn 'AI Risk' ustunini realistik
namoyish qiymatlari bilan to'ldiradi (past/o'rtacha/yuqori daraja aralash).
Telegram/email alert chaqirilmaydi."""
from django.utils import timezone
from students.models import Student

HIGH = [
    (88.0, "Davomat juda past (32%), oxirgi to'lovdan 81 kun o'tgan, muddati o'tgan to'lov bor."),
    (76.0, "Faol kurs yozilishi yo'q, davomat past (44%), umumiy qarz mavjud."),
    (72.0, "Oxirgi to'lovdan 68 kun o'tgan, bekor qilingan kurslari ko'p."),
]
MED = [
    (58.0, "Davomat o'rtacha (61%), bitta enrollment muddati o'tgan."),
    (47.0, "Oxirgi to'lovdan 35 kun o'tgan, davomat me'yorda."),
    (52.0, "Umumiy qarz summa mavjud, davomat o'rtacha (64%)."),
]
LOW = [
    (12.0, "Asosiy ko'rsatkichlar me'yorda, davomat yaxshi (92%)."),
    (8.0, "To'lovlar o'z vaqtida, faol kurs yozilishi bor."),
    (22.0, "Davomat yaxshi, kichik kechikish bor — xavf past."),
    (5.0, "Barcha ko'rsatkichlar a'lo darajada."),
]

students = list(Student.objects.all().order_by("pk"))
n = 0
for i, s in enumerate(students):
    if i % 7 == 0:
        score, reason = HIGH[i % len(HIGH)]
    elif i % 7 in (1, 4):
        score, reason = MED[i % len(MED)]
    else:
        score, reason = LOW[i % len(LOW)]
    s.churn_risk_score = score
    s.churn_risk_reason = reason
    s.churn_risk_updated_at = timezone.now()
    s.save(update_fields=["churn_risk_score", "churn_risk_reason", "churn_risk_updated_at"])
    n += 1

print(f"OK: {n} ta talabaga churn ball saqlandi")
levels = {}
for s in Student.objects.all():
    levels[s.churn_risk_level] = levels.get(s.churn_risk_level, 0) + 1
print("Darajalar:", levels)
