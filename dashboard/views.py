import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect
from django.utils import timezone

from students.models import Student
from courses.models import Course
from payments.models import Payment
from attendance.models import Attendance
from accounts.models import CustomUser

try:
    from expenses.models import Expense
except Exception:
    Expense = None


# ══════════════════════════════════════════════════════════════
#  HELPER FUNKSIYALAR
# ══════════════════════════════════════════════════════════════

def percentage_change(current, previous):
    current  = float(current  or 0)
    previous = float(previous or 0)
    if previous == 0 and current > 0:
        return 100.0
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_month_start(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_next_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1, day=1)
    return dt.replace(month=dt.month + 1, day=1)


def build_monthly_chart(completed_payments, six_months_start, next_month_start):
    """So'nggi 6 oy uchun daromad chart ma'lumotlari."""
    monthly_qs = (
        completed_payments
        .filter(paid_at__gte=six_months_start, paid_at__lt=next_month_start)
        .annotate(month=TruncMonth('paid_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    income_map = {
        row['month'].strftime('%Y-%m'): float(row['total'] or 0)
        for row in monthly_qs
    }

    labels, values = [], []
    cursor = six_months_start
    while cursor < next_month_start:
        labels.append(cursor.strftime('%b %Y'))
        values.append(income_map.get(cursor.strftime('%Y-%m'), 0))
        cursor = get_next_month(cursor)

    return labels, values


# ══════════════════════════════════════════════════════════════
#  DASHBOARD VIEW
# ══════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):

    # Dashboard faqat admin uchun. Teacherlarni attendance sahifasiga yo'naltiramiz.
    if getattr(request.user, 'role', None) != 'admin':
        return redirect('attendance:attendance_list')

    now                  = timezone.now()
    week_ago             = now - timedelta(days=7)
    current_month_start  = get_month_start(now)
    next_month_start     = get_next_month(current_month_start)
    prev_month_end       = current_month_start
    prev_month_start     = get_month_start(current_month_start - timedelta(days=1))

    # ── Talabalar ────────────────────────────────────────────
    total_students    = Student.objects.count()
    active_students   = Student.objects.filter(is_active=True).count()
    new_students_week = Student.objects.filter(created_at__gte=week_ago).count()

    # ── Kurslar ──────────────────────────────────────────────
    total_courses  = Course.objects.count()
    active_courses = Course.objects.filter(is_active=True).count()

    # ── Foydalanuvchilar ─────────────────────────────────────
    total_teachers = CustomUser.objects.filter(role='teacher').count()
    total_admins   = CustomUser.objects.filter(role='admin').count()

    # ── To'lovlar ────────────────────────────────────────────
    completed_payments = Payment.objects.filter(status='paid')
    pending_payments   = Payment.objects.filter(status='pending')

    total_income = completed_payments.aggregate(t=Sum('amount'))['t'] or Decimal('0')

    week_income = completed_payments.filter(
        paid_at__gte=week_ago
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    month_income = completed_payments.filter(
        payment_month=now.month,
        payment_year=now.year,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    prev_month = prev_month_start
    prev_month_income = completed_payments.filter(
        payment_month=prev_month.month,
        payment_year=prev_month.year,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    income_growth_percent     = percentage_change(month_income, prev_month_income)
    income_growth_percent_abs = abs(float(income_growth_percent))
    income_growth_positive    = float(income_growth_percent) >= 0

    pending_pay_count  = pending_payments.count()
    pending_pay_amount = pending_payments.aggregate(t=Sum('amount'))['t'] or Decimal('0')

    recent_payments = (
        Payment.objects
        .select_related('student', 'course')
        .order_by('-paid_at', '-id')[:10]
    )

    # ── Davomat ──────────────────────────────────────────────
    total_attendance = Attendance.objects.count()
    present_count    = Attendance.objects.filter(status='present').count()
    absent_count     = Attendance.objects.filter(status='absent').count()
    late_count       = Attendance.objects.filter(status='late').count()

    attendance_rate = (
        round(present_count / total_attendance * 100, 1)
        if total_attendance > 0 else 0
    )

    recent_attendances = (
        Attendance.objects
        .select_related('student', 'course', 'marked_by')
        .order_by('-date', '-id')[:10]
    )

    top_courses = (
        Attendance.objects
        .values('course__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    top_courses_labels = [row['course__name'] or 'Nomsiz' for row in top_courses]
    top_courses_values = [row['total']         for row in top_courses]

    teacher_activity = (
        Attendance.objects
        .values('marked_by__first_name', 'marked_by__last_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    teacher_labels = [
        f"{row['marked_by__first_name'] or ''} {row['marked_by__last_name'] or ''}".strip()
        or "Noma'lum"
        for row in teacher_activity
    ]
    teacher_values = [row['total'] for row in teacher_activity]

    # ── Oylik daromad chart (6 oy) ───────────────────────────
    six_months_start = current_month_start
    for _ in range(5):
        six_months_start = get_month_start(six_months_start - timedelta(days=1))

    chart_labels, chart_income = build_monthly_chart(
        completed_payments, six_months_start, next_month_start
    )

    # ── To'lov holati (donut chart) ──────────────────────────
    payment_status_qs = (
        Payment.objects
        .values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )
    payment_status_labels = [row['status'].title() for row in payment_status_qs]
    payment_status_values = [row['total']           for row in payment_status_qs]

    # ── Xarajatlar ───────────────────────────────────────────
    expense_this_month   = Decimal('0')
    expense_breakdown    = []
    expense_chart_labels = []
    expense_chart_values = []

    if Expense is not None:
        paid_expenses = Expense.objects.filter(status='paid')

        expense_this_month = paid_expenses.filter(
            date__gte=current_month_start,
            date__lt=next_month_start,
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

        raw_breakdown = (
            paid_expenses
            .filter(date__gte=current_month_start, date__lt=next_month_start)
            .values('category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        for row in raw_breakdown:
            amount  = float(row['total'] or 0)
            percent = round(
                (amount / float(expense_this_month)) * 100, 1
            ) if expense_this_month else 0
            label   = row['category__name'] or 'Kategoriyasiz'

            expense_breakdown.append({
                'label':   label,
                'amount':  amount,
                'percent': percent,
            })
            expense_chart_labels.append(label)
            expense_chart_values.append(amount)

    # ── Sof foyda ────────────────────────────────────────────
    net_profit = float(month_income) - float(expense_this_month)

    # ── Context ──────────────────────────────────────────────
    context = {
        # Talabalar
        'total_students':    total_students,
        'active_students':   active_students,
        'new_students_week': new_students_week,

        # Kurslar
        'total_courses':  total_courses,
        'active_courses': active_courses,

        # Foydalanuvchilar
        'total_teachers': total_teachers,
        'total_admins':   total_admins,

        # To'lovlar
        'total_income':              total_income,
        'week_income':               week_income,
        'month_income':              month_income,
        'income_growth_percent':     income_growth_percent,
        'income_growth_percent_abs': income_growth_percent_abs,
        'income_growth_positive':    income_growth_positive,
        'pending_pay_count':         pending_pay_count,
        'pending_pay_amount':        pending_pay_amount,
        'recent_payments':           recent_payments,

        # Davomat
        'total_attendance':   total_attendance,
        'present_count':      present_count,
        'absent_count':       absent_count,
        'late_count':         late_count,
        'attendance_rate':    attendance_rate,
        'recent_attendances': recent_attendances,

        # Xarajatlar
        'expense_this_month': expense_this_month,
        'expense_breakdown':  expense_breakdown,
        'net_profit':         net_profit,

        # Chart JSON-lar
        'chart_labels_json':  json.dumps(chart_labels,  cls=DjangoJSONEncoder),
        'chart_income_json':  json.dumps(chart_income,  cls=DjangoJSONEncoder),

        'payment_status_labels_json': json.dumps(payment_status_labels, cls=DjangoJSONEncoder),
        'payment_status_values_json': json.dumps(payment_status_values, cls=DjangoJSONEncoder),

        'expense_chart_labels_json': json.dumps(expense_chart_labels, cls=DjangoJSONEncoder),
        'expense_chart_values_json': json.dumps(expense_chart_values, cls=DjangoJSONEncoder),

        'top_courses_labels_json': json.dumps(top_courses_labels, cls=DjangoJSONEncoder),
        'top_courses_values_json': json.dumps(top_courses_values, cls=DjangoJSONEncoder),

        'teacher_labels_json': json.dumps(teacher_labels, cls=DjangoJSONEncoder),
        'teacher_values_json': json.dumps(teacher_values, cls=DjangoJSONEncoder),
    }

    return render(request, 'dashboard.html', context)