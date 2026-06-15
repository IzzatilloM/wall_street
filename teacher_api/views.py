"""O'qituvchi mobil API — CRM bilan BOG'LANGAN DRF view'lar.

⚠️ MUHIM: Bu modul endi o'zining alohida jadvallaridan (TGroup/TStudent/...)
EMAS, balki Wall Street CRM'ning HAQIQIY ma'lumotlaridan foydalanadi:

  • "Guruh"      = o'qituvchi dars beradigan `courses.Course`
  • "O'quvchi"   = o'sha kursga yozilgan `attendance.Student` (CRM student bilan bog'liq)
  • "Davomat"    = `attendance.Attendance` (admin ham CRM'da ko'radi)
  • "Oylik"      = `instructors.Instructor.salary` + `staff_salary.SalaryPayment`

Endpoint manzillari va `{success, message, data}` javob formati o'zgarmagan —
shuning uchun mavjud Flutter ilovasi ishlashda davom etadi.
Auth: JWT Bearer token (SimpleJWT).
"""
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import authenticate
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from instructors.models import Instructor
from courses.models import Course
from enrollments.models import Enrollment
from attendance.models import (
    Course as AttCourse,
    Student as AttStudent,
    Attendance,
)
from staff_salary.models import SalaryPayment


# ─── Javob yordamchilari ─────────────────────────────────────────────────────
def ok(data=None, message="OK", code=200):
    body = {'success': True, 'message': message}
    if data is not None:
        body['data'] = data
    return Response(body, status=code)


def fail(error, code=400):
    return Response({'success': False, 'error': error}, status=code)


def _f(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _abs(request, filefield):
    if filefield and hasattr(filefield, 'url'):
        try:
            return request.build_absolute_uri(filefield.url)
        except Exception:
            return filefield.url
    return None


# ─── CRM yordamchilari ───────────────────────────────────────────────────────
CATEGORY_COLOR = {'english': '#0D6E6E', 'it': '#C9A84C'}


def _instructor(user):
    return Instructor.objects.filter(user=user).first()


def _att_course(course):
    """courses.Course → tegishli attendance.Course (kod: WS-C{id})."""
    return AttCourse.objects.filter(code=f"WS-C{course.id}").first()


def _course_duration_min(course):
    """Kurs jadvalidan bitta dars davomiyligi (daqiqa). Belgilanmasa — 120."""
    if course and course.start_time and course.end_time:
        s = datetime.combine(date.today(), course.start_time)
        e = datetime.combine(date.today(), course.end_time)
        m = int((e - s).total_seconds() // 60)
        if m > 0:
            return m
    return 120


def _course_schedule(course):
    days = course.weekday_list
    t = course.time_display
    if days or t:
        return {'days': days, 'time': t}
    return None


def _teacher_courses(instr):
    if not instr:
        return Course.objects.none()
    return Course.objects.filter(teacher=instr).order_by('title')


# ─── Dict (serializer) yordamchilari ────────────────────────────────────────
def teacher_dict(user, request):
    instr = _instructor(user)
    salary = float(instr.salary) if instr else 0.0
    full_name = (instr.full_name if instr and instr.full_name
                 else (user.get_full_name() or user.username))
    return {
        'id': user.id,
        'full_name': full_name,
        'username': user.username,
        'phone': user.phone,
        'photo': _abs(request, user.avatar),
        'specialty': instr.specialty if instr else '',
        # Oylik CRM'da (Instructor.salary) boshqariladi → "monthly".
        'salary_type': 'monthly',
        'base_salary': salary,
        'rate_per_lesson': 0.0,
        'rate_per_hour': 0.0,
    }


def group_dict(course, students_count):
    return {
        'id': course.id,
        'name': course.title,
        'subject': course.category_badge,
        'lesson_price': _f(course.price),
        'schedule': _course_schedule(course),
        'color': CATEGORY_COLOR.get(course.category),
        'students_count': students_count,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    if not username or not password:
        return fail("Login va parolni kiriting", 400)

    user = authenticate(username=username, password=password)
    if user is None:
        return fail("Login yoki parol noto'g'ri", 401)
    if user.role not in ('teacher', 'admin'):
        return fail("Bu ilova faqat o'qituvchilar uchun", 403)

    access = RefreshToken.for_user(user).access_token
    return ok({'token': str(access), 'teacher': teacher_dict(user, request)},
              "Tizimga muvaffaqiyatli kirdingiz")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return ok({'teacher': teacher_dict(request.user, request)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profile_update(request):
    """Ism/telefonni yangilaydi. Oylik CRM'da boshqariladi (bu yerda o'zgarmaydi)."""
    user = request.user
    d = request.data

    full_name = (d.get('full_name') or '').strip()
    if full_name:
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
    if 'phone' in d:
        user.phone = d.get('phone')
    user.save()

    instr = _instructor(user)
    if instr and full_name:
        instr.full_name = full_name
        instr.save(update_fields=['full_name'])

    return ok({'teacher': teacher_dict(user, request)}, "Profil yangilandi")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile_upload_photo(request):
    f = request.FILES.get('photo')
    if not f:
        return fail("Rasm yuborilmadi", 400)
    user = request.user
    user.avatar = f
    user.save()
    return ok({'photo': _abs(request, user.avatar)}, "Rasm yangilandi")


# ═══════════════════════════════════════════════════════════════════════════
#  GURUHLAR (= o'qituvchining CRM kurslari) — faqat o'qish
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def groups(request):
    if request.method != 'GET':
        return fail("Guruhlar Wall Street tizimida (admin panel) boshqariladi", 403)

    instr = _instructor(request.user)
    courses = _teacher_courses(instr)
    result = []
    for c in courses:
        ac = _att_course(c)
        sc = (ac.students.count() if ac
              else c.enrollments.exclude(status='cancelled').count())
        result.append(group_dict(c, sc))
    return ok({'groups': result})


# ═══════════════════════════════════════════════════════════════════════════
#  O'QUVCHILAR (= kursga yozilganlar) — faqat o'qish (+rasm)
# ═══════════════════════════════════════════════════════════════════════════
def _owned_course(user, course_id):
    instr = _instructor(user)
    if not instr:
        return None
    return Course.objects.filter(id=course_id, teacher=instr).first()


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def students(request):
    if request.method != 'GET':
        return fail("O'quvchilar Wall Street tizimida boshqariladi", 403)

    user = request.user
    course = _owned_course(user, request.query_params.get('group_id'))
    if not course:
        return fail("Guruh topilmadi", 404)

    ac = _att_course(course)
    out = []
    if ac:
        fees = {
            e.student.user_id: e
            for e in Enrollment.objects.filter(course=course).select_related('student')
            if e.student and e.student.user_id
        }
        att_students = (ac.students.select_related('user')
                        .order_by('user__first_name', 'user__last_name'))
        for ats in att_students:
            crm = ats.crm_student
            en = fees.get(ats.user_id)
            out.append({
                'id': ats.id,
                'group_id': course.id,
                'full_name': ats.get_full_name(),
                'phone': (crm.phone if crm else None),
                'photo': _abs(request, crm.image) if (crm and crm.image) else None,
                'monthly_fee': _f(en.net_fee) if en else _f(course.price),
                'status': 'active',
                'coins': (crm.coins if crm else 0),
            })
    return ok({'students': out})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def student_upload_photo(request):
    """student_id = attendance.Student.id → CRM student rasmini yangilaydi."""
    sid = request.data.get('student_id')
    ats = AttStudent.objects.filter(id=sid).select_related('user').first()
    if not ats:
        return fail("O'quvchi topilmadi", 404)
    # O'qituvchi shu o'quvchining kurslaridan biriga ega bo'lishi kerak
    instr = _instructor(request.user)
    owns = ats.courses.filter(code__in=[
        f"WS-C{c.id}" for c in _teacher_courses(instr)
    ]).exists()
    if not owns:
        return fail("Ruxsat yo'q", 403)
    crm = ats.crm_student
    if not crm:
        return fail("CRM profili topilmadi", 404)
    f = request.FILES.get('photo')
    if not f:
        return fail("Rasm yuborilmadi", 400)
    crm.image = f
    crm.save(update_fields=['image'])
    return ok({'photo': _abs(request, crm.image)}, "Rasm yangilandi")


# ═══════════════════════════════════════════════════════════════════════════
#  DAVOMAT → CRM attendance.Attendance
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attendance_save(request):
    user = request.user
    d = request.data
    course = _owned_course(user, d.get('group_id'))
    if not course:
        return fail("Guruh topilmadi", 404)
    ac = _att_course(course)
    if not ac:
        return fail("Guruh CRM bilan sinxronlanmagan", 400)

    items = d.get('items') or []
    if not isinstance(items, list) or not items:
        return fail("Davomat ro'yxati bo'sh", 400)

    lesson_date = parse_date(d.get('lesson_date') or '') or timezone.localdate()
    valid_ids = set(ac.students.values_list('id', flat=True))
    counts = {'present': 0, 'absent': 0, 'late': 0}

    for it in items:
        sid = it.get('student_id')
        if sid not in valid_ids:
            continue
        st = it.get('status')
        if st not in ('present', 'absent', 'late'):
            st = 'present'
        Attendance.objects.update_or_create(
            student_id=sid, course=ac, date=lesson_date,
            defaults={'status': st, 'note': it.get('comment'), 'marked_by': user},
        )
        counts[st] += 1

    return ok({
        'id': course.id * 1000000 + lesson_date.toordinal(),
        'lesson_date': str(lesson_date),
        'duration_min': _course_duration_min(course),
        'present_count': counts['present'],
        'absent_count': counts['absent'],
        'late_count': counts['late'],
    }, "Davomat saqlandi")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_history(request):
    user = request.user
    instr = _instructor(user)
    courses = list(_teacher_courses(instr))
    code_to_course = {f"WS-C{c.id}": c for c in courses}
    accourses = AttCourse.objects.filter(code__in=code_to_course.keys())
    ac_to_course = {ac.id: code_to_course[ac.code] for ac in accourses}

    qs = Attendance.objects.filter(course_id__in=ac_to_course.keys())

    group_id = request.query_params.get('group_id')
    if group_id:
        course = code_to_course.get(f"WS-C{group_id}")
        ac = _att_course(course) if course else None
        if ac:
            qs = qs.filter(course=ac)
        else:
            return ok({'records': []})

    d_from = parse_date(request.query_params.get('from') or '')
    if d_from:
        qs = qs.filter(date__gte=d_from)
    d_to = parse_date(request.query_params.get('to') or '')
    if d_to:
        qs = qs.filter(date__lte=d_to)

    rows = (qs.values('course_id', 'date')
            .annotate(
                present_count=Count('id', filter=Q(status='present')),
                absent_count=Count('id', filter=Q(status='absent')),
                late_count=Count('id', filter=Q(status='late')),
            )
            .order_by('-date'))[:200]

    records = []
    for r in rows:
        course = ac_to_course.get(r['course_id'])
        records.append({
            'id': (course.id * 1000000 + r['date'].toordinal()) if course else 0,
            'group_id': course.id if course else 0,
            'group_name': course.title if course else '',
            'lesson_date': str(r['date']),
            'duration_min': _course_duration_min(course) if course else 0,
            'note': None,
            'present_count': r['present_count'],
            'absent_count': r['absent_count'],
            'late_count': r['late_count'],
        })
    return ok({'records': records})


# ═══════════════════════════════════════════════════════════════════════════
#  STATISTIKA / OYLIK (Instructor.salary + staff_salary)
# ═══════════════════════════════════════════════════════════════════════════
def _period_bounds(period_str):
    today = timezone.localdate()
    y, m = today.year, today.month
    if period_str and '-' in period_str:
        try:
            y, m = int(period_str[:4]), int(period_str[5:7])
        except Exception:
            pass
    start = date(y, m, 1)
    nxt = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return y, m, start, nxt


def _salary_for(instr, base_salary, yy, mm):
    if not instr:
        return base_salary
    sp = (SalaryPayment.objects
          .filter(instructor=instr, year=yy, month=mm)
          .aggregate(s=Sum('amount'))['s'])
    return float(sp) if sp is not None else base_salary


def _stats_for(ac_to_course, ac_ids, instr, base_salary, s, n, yy, mm):
    """[s, n) oraliq uchun: dars sessiyalari, ish soati, oylik."""
    sessions = list(
        Attendance.objects
        .filter(course_id__in=ac_ids, date__gte=s, date__lt=n)
        .values('course_id', 'date').distinct().order_by()  # .order_by() — model tartiblashini tozalaydi (distinct buzilmasligi uchun)
    )
    lessons = len(sessions)
    worked_min = sum(
        _course_duration_min(ac_to_course.get(x['course_id'])) for x in sessions
    )
    earned = _salary_for(instr, base_salary, yy, mm)
    return {
        'worked_minutes': worked_min,
        'worked_hours': round(worked_min / 60.0, 2),
        'lessons_count': lessons,
        'earned': round(earned, 2),
        'computed_salary': round(earned, 2),
    }


def _build_summary(user, period):
    instr = _instructor(user)
    base_salary = float(instr.salary) if instr else 0.0
    y, m, start, nxt = _period_bounds(period)

    courses = list(_teacher_courses(instr))
    code_to_course = {f"WS-C{c.id}": c for c in courses}
    accourses = list(AttCourse.objects.filter(code__in=code_to_course.keys()))
    ac_to_course = {ac.id: code_to_course[ac.code] for ac in accourses}
    ac_ids = list(ac_to_course.keys())

    current = _stats_for(ac_to_course, ac_ids, instr, base_salary, start, nxt, y, m)

    months = []
    yy, mm = y, m
    for _ in range(6):
        s = date(yy, mm, 1)
        n = date(yy + 1, 1, 1) if mm == 12 else date(yy, mm + 1, 1)
        st = _stats_for(ac_to_course, ac_ids, instr, base_salary, s, n, yy, mm)
        months.append({
            'period': f"{yy:04d}-{mm:02d}",
            'worked_hours': st['worked_hours'],
            'lessons': st['lessons_count'],
            'earned': st['earned'],
            'computed_salary': st['computed_salary'],
        })
        mm -= 1
        if mm == 0:
            mm = 12
            yy -= 1
    months.reverse()

    by_group = []
    for ac in accourses:
        course = ac_to_course[ac.id]
        lessons = (Attendance.objects
                   .filter(course=ac, date__gte=start, date__lt=nxt)
                   .values('date').distinct().count())
        if lessons == 0:
            continue
        hours = round(lessons * _course_duration_min(course) / 60.0, 2)
        by_group.append({
            'group_id': course.id,
            'group_name': course.title,
            'lessons': lessons,
            'worked_hours': hours,
            'earned': 0.0,
        })

    return {
        'period': f"{y:04d}-{m:02d}",
        'salary_type': 'monthly',
        'base_salary': base_salary,
        'current': current,
        'months': months,
        'by_group': by_group,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_summary(request):
    return ok(_build_summary(request.user, request.query_params.get('period')))


# ═══════════════════════════════════════════════════════════════════════════
#  AI TAHLIL (Claude)
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_analyze(request):
    summary = _build_summary(request.user, request.data.get('period'))
    cur = summary['current']
    y, m = summary['period'][:4], summary['period'][5:7]

    facts = (
        f"Davr: {y}-{m}\n"
        f"Darslar soni: {cur['lessons_count']}\n"
        f"Ishlangan soat: {cur['worked_hours']}\n"
        f"Oylik: {cur['computed_salary']}\n"
    )

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            model = os.environ.get('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001')
            msg = client.messages.create(
                model=model,
                max_tokens=600,
                messages=[{
                    'role': 'user',
                    'content': (
                        "Siz o'quv markazi o'qituvchisiga yordam beradigan "
                        "tahlilchisiz. Quyidagi oylik faoliyat ma'lumotlari "
                        "asosida qisqa (3-5 jumla), do'stona va foydali tahlil "
                        "hamda 1-2 tavsiya bering. O'zbek tilida yozing.\n\n" + facts
                    ),
                }],
            )
            text = ''.join(
                block.text for block in msg.content if getattr(block, 'type', '') == 'text'
            )
            if text.strip():
                return ok({'analysis': text.strip()})
        except Exception:
            pass

    if cur['lessons_count'] == 0:
        analysis = (
            f"{y}-{m} oyida hali dars belgilanmagan. Davomatlarni "
            "kiritib boring — shunda hisobingiz to'liq chiqadi."
        )
    else:
        analysis = (
            f"{y}-{m} oyida {cur['lessons_count']} ta dars o'tdingiz, "
            f"jami {cur['worked_hours']} soat. Barakali ish! "
            "Davomatni muntazam kiritib borsangiz, hisob-kitob aniqroq bo'ladi."
        )
    return ok({'analysis': analysis})
