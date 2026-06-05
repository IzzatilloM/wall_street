import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone

from payments.models import Payment
from staff_salary.models import SalaryPayment
from students.models import Student
from courses.models import Course
from enrollments.models import Enrollment
from instructors.models import Instructor


@login_required
def reports(request):
    now = timezone.now()
    try:
        year = int(request.GET.get('year', now.year))
    except (TypeError, ValueError):
        year = now.year

    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    income_by_month = [0.0] * 12
    for row in (Payment.objects.filter(paid_at__year=year)
                .values('paid_at__month').annotate(t=Sum('amount'))):
        income_by_month[row['paid_at__month'] - 1] = float(row['t'] or 0)

    expense_by_month = [0.0] * 12
    for row in (SalaryPayment.objects.filter(year=year, status='paid')
                .values('month').annotate(t=Sum('amount'))):
        expense_by_month[row['month'] - 1] = float(row['t'] or 0)

    total_income = sum(income_by_month)
    total_expense = sum(expense_by_month)
    net_profit = total_income - total_expense

    top_courses = (Course.objects
                   .annotate(n=Count('groups__enrollments'))
                   .order_by('-n')[:5])

    # available years for the filter
    pay_years = list(Payment.objects.values_list('paid_at__year', flat=True).distinct())
    sal_years = list(SalaryPayment.objects.values_list('year', flat=True).distinct())
    years = sorted(set(pay_years + sal_years + [now.year]), reverse=True)

    context = {
        'year': year,
        'years': years,
        'month_labels_json': json.dumps(month_labels),
        'income_json': json.dumps(income_by_month),
        'expense_json': json.dumps(expense_by_month),
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_instructors': Instructor.objects.count(),
        'active_enrollments': Enrollment.objects.filter(status='active').count(),
        'top_courses': top_courses,
    }
    return render(request, 'reports/reports.html', context)
