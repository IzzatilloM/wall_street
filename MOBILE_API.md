# Wall Street — Mobil ilova API (DRF)

Mobil ilova uchun `api` app orqali REST endpointlar. Autentifikatsiya: **JWT**
(`djangorestframework-simplejwt`). Barcha manzillar `/api/` prefiksi bilan.

## Sozlash
`requirements.txt` o'rnatish:
```bash
pip install -r requirements.txt
```
`settings.py` ga qo'shilgan: `rest_framework`, `rest_framework_simplejwt`,
`corsheaders`, `news`, `api`. CORS barcha manbalarga ochiq (`CORS_ALLOW_ALL_ORIGINS=True`).

Migratsiya va test ma'lumotlar:
```bash
python manage.py migrate
python manage.py shell -c "exec(open('seed_mobile.py', encoding='utf-8').read())"
```

## Endpointlar

### 🔐 Auth
| Metod | URL | Tavsif |
|-------|-----|--------|
| POST | `/api/auth/login/` | `{username, password}` → `{access, refresh, user}` |
| POST | `/api/auth/refresh/` | `{refresh}` → yangi `{access}` |
| POST | `/api/auth/verify/` | tokenni tekshirish |

Har bir himoyalangan so'rovda header: `Authorization: Bearer <access>`

### 👤 Profil
| Metod | URL | Tavsif |
|-------|-----|--------|
| GET | `/api/me/` | joriy student profili |
| PATCH | `/api/me/` | `phone, parent_phone, email, address, image` ni yangilash |

### 🎓 Mening kurslarim
| Metod | URL | Tavsif |
|-------|-----|--------|
| GET | `/api/me/courses/` | studentning yozilgan kurslari (Enrollment): `course_title, level, teacher, status, payment_status, payment_percent, paid_amount, remaining, start_date, end_date` (sahifalangan) |

### 💳 To'lovlar
| Metod | URL | Tavsif |
|-------|-----|--------|
| GET | `/api/me/payments/` | studentning to'lovlari (sahifalangan) |
| GET | `/api/me/payments/summary/` | `{total_paid, pending, count, coins}` |

### 📰 Yangiliklar (ochiq)
| Metod | URL | Tavsif |
|-------|-----|--------|
| GET | `/api/news/` | chop etilgan yangiliklar |
| GET | `/api/news/<id>/` | bitta yangilik |

## Studentni mobil ilovaga ulash
Mobil ilovaga kira olishi uchun studentga **CustomUser** (login/parol) berilishi
va `Student.user` maydoni o'sha userga bog'lanishi kerak:
1. Admin panel → Users → yangi user yarating (`role=student`).
2. Admin panel → Students → kerakli studentni tanlab, `user` maydoniga ulang.

> `accounts/models.py`: `CustomUser` (role: admin/teacher/**student**)
> `students/models.py`: `Student.user` = OneToOne → CustomUser

## Tez sinov (PowerShell)
```powershell
$r = Invoke-RestMethod http://127.0.0.1:8000/api/auth/login/ -Method Post `
  -Body (@{username='student1';password='student123'}|ConvertTo-Json) -ContentType 'application/json'
$h = @{Authorization="Bearer $($r.access)"}
Invoke-RestMethod http://127.0.0.1:8000/api/me/ -Headers $h
Invoke-RestMethod http://127.0.0.1:8000/api/me/payments/summary/ -Headers $h
```
