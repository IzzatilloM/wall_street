import calendar
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .utils import (
    UZBEK_MONTH_NAMES,
    UZBEK_WEEKDAYS,
    get_fixed_holidays,
    get_islamic_holidays,
    merge_holidays,
    get_study_breaks,
    get_month_statistics,
)


@login_required
def calendar_view(request, year=None, month=None):
    """
    Murakkab calendar view - barcha sanalar chiqadi va eventlar rang bilan ajratiladi
    """
    today = date.today()

    # Year va Month parametrlarini olish
    if not year:
        year = int(request.GET.get("year", today.year))
    if not month:
        month = int(request.GET.get("month", today.month))

    year = int(year)
    month = int(month)

    # Validatsiya
    if month < 1 or month > 12:
        month = today.month
    if year < 2000 or year > 2100:
        year = today.year

    # Calendar object - Dushanbadan boshlanadi
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    # Barcha holiday larni olish
    fixed_holidays = get_fixed_holidays(year)
    islamic_holidays = get_islamic_holidays(year)
    holidays = merge_holidays(fixed_holidays, islamic_holidays)

    # Study breaks - har 2 oyda 2 kunlik dam
    study_breaks = get_study_breaks(year)

    # Weeks ni qayta ishlash - barcha sanalar ko'rsatiladi
    weeks = []
    for week in month_days:
        week_row = []
        for day in week:
            badges = []
            event_types = []

            # STATUS BELGILASH
            status = "other_month"

            if day.month == month:
                status = "current_month"

                # Bugungi sana
                if day == today:
                    status = "today"

            # ========== MOCK DAY - HAR YAKSHANBA ==========
            if day.weekday() == 6 and day.month == month:
                badges.append({
                    "title": "Mock Day",
                    "icon": "📝",
                    "class": "badge-red",
                    "type": "mock_day",
                    "color_hex": "#ef4444",
                })
                event_types.append("mock_day")

            # ========== MOCK RESULT - HAR PAYSHANBA ==========
            if day.weekday() == 3 and day.month == month:
                badges.append({
                    "title": "Mock Result",
                    "icon": "✓",
                    "class": "badge-green",
                    "type": "mock_result",
                    "color_hex": "#10b981",
                })
                event_types.append("mock_result")

            # ========== BAYRAMLAR - SARIQ RANG ==========
            if day in holidays:
                for holiday_item in holidays[day]:
                    badges.append({
                        "title": holiday_item["title"],
                        "title_uz": holiday_item.get("title_uz", ""),
                        "icon": "🎉",
                        "class": "badge-yellow",
                        "type": "holiday",
                        "color_hex": "#f59e0b",
                        "description": holiday_item.get("description", ""),
                    })
                    event_types.append("holiday")

            # ========== STUDY BREAKS - YASHIL RANG ==========
            if day in study_breaks:
                for break_item in study_breaks[day]:
                    badges.append({
                        "title": break_item["title"],
                        "icon": "🏖️",
                        "class": "badge-study-break",
                        "type": "study_break",
                        "color_hex": "#10b981",
                        "description": "Oqish markaz 2 kunlik damasi",
                    })
                    event_types.append("study_break")

            # VICHNI SANA KO'RSATISH
            is_weekend = day.weekday() in [5, 6]  # Shanba va Yakshanba

            week_row.append({
                "date": day,
                "day_number": day.day,
                "day_name": UZBEK_WEEKDAYS[day.weekday()],
                "weekday": day.weekday(),
                "is_current_month": day.month == month,
                "is_today": day == today,
                "is_weekend": is_weekend,
                "status": status,
                "badges": badges,
                "event_types": event_types,
                "has_events": len(badges) > 0,
                "event_count": len(badges),
            })
        weeks.append(week_row)

    # Previous month
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    # Next month
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    # Oylik statistika
    statistics = get_month_statistics(year, month)

    # Yil diapazoni
    current_year = date.today().year
    year_range = list(range(current_year - 2, current_year + 5))

    # Legend items
    legend_items = [
        {
            "title": "Mock Day",
            "title_uz": "Test uchun mo'ljallangan kun",
            "icon": "📝",
            "class": "badge-red",
            "description": "Har yakshanba - test ishlash uchun mo'ljallangan kun",
        },
        {
            "title": "Mock Result",
            "title_uz": "Test natijalarini o'rganish",
            "icon": "✓",
            "class": "badge-green",
            "description": "Har payshanba - test natijalarini o'rganish va tahlil qilish",
        },
        {
            "title": "Holiday",
            "title_uz": "Bayram kunlari",
            "icon": "🎉",
            "class": "badge-yellow",
            "description": "Rasmiy bayramlar va ta'til kunlari (Navro'z, Mustaqillik kuni, va boshqalar)",
        },
        {
            "title": "Study Break",
            "title_uz": "Oqish markaz ta'liti",
            "icon": "🏖️",
            "class": "badge-study-break",
            "description": "Har 2 oyda bir 2 kunlik dam va turish (Fevral, Aprel, Iyun, Avgust, Oktabr, Dekabr)",
        },
    ]

    context = {
        "today": today,
        "current_year": year,
        "current_month": month,
        "current_month_name": UZBEK_MONTH_NAMES[month],
        "week_names": UZBEK_WEEKDAYS,
        "weeks": weeks,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "year_range": year_range,
        "legend_items": legend_items,
        "statistics": statistics,
        "month_start": datetime(year, month, 1).strftime("%A"),
        "month_start_weekday": datetime(year, month, 1).weekday(),
    }

    return render(request, "calendar.html", context)


@login_required
def calendar_api_month(request, year, month):
    """
    JSON API - oyning ma'lumotlarini JSON formatda qaytaradi
    """
    today = date.today()

    try:
        year = int(year)
        month = int(month)

        if month < 1 or month > 12:
            return JsonResponse({"error": "Invalid month"}, status=400)

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(year, month)

        fixed_holidays = get_fixed_holidays(year)
        islamic_holidays = get_islamic_holidays(year)
        holidays = merge_holidays(fixed_holidays, islamic_holidays)
        study_breaks = get_study_breaks(year)

        weeks_data = []
        for week in month_days:
            week_data = []
            for day in week:
                day_events = []

                # Mock Day
                if day.weekday() == 6 and day.month == month:
                    day_events.append({
                        "title": "Mock Day",
                        "type": "mock_day",
                        "color": "red"
                    })

                # Mock Result
                if day.weekday() == 3 and day.month == month:
                    day_events.append({
                        "title": "Mock Result",
                        "type": "mock_result",
                        "color": "green"
                    })

                # Holidays
                if day in holidays:
                    for holiday in holidays[day]:
                        day_events.append({
                            "title": holiday["title"],
                            "type": "holiday",
                            "color": "yellow"
                        })

                # Study breaks
                if day in study_breaks:
                    for break_item in study_breaks[day]:
                        day_events.append({
                            "title": break_item["title"],
                            "type": "study_break",
                            "color": "green"
                        })

                week_data.append({
                    "date": day.isoformat(),
                    "day": day.day,
                    "weekday": day.weekday(),
                    "is_today": day == today,
                    "is_current_month": day.month == month,
                    "events": day_events,
                    "event_count": len(day_events),
                })
            weeks_data.append(week_data)

        return JsonResponse({
            "success": True,
            "year": year,
            "month": month,
            "month_name": UZBEK_MONTH_NAMES[month],
            "weeks": weeks_data,
        })

    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid parameters"}, status=400)


@login_required
def calendar_day_details(request, year, month, day):
    """
    Shu kun uchun batafsil ma'lumotlar - AJAX orqali
    """
    try:
        target_date = date(int(year), int(month), int(day))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date"}, status=400)

    today = date.today()

    fixed_holidays = get_fixed_holidays(int(year))
    islamic_holidays = get_islamic_holidays(int(year))
    holidays = merge_holidays(fixed_holidays, islamic_holidays)
    study_breaks = get_study_breaks(int(year))

    day_events = []

    # Mock Day
    if target_date.weekday() == 6:
        day_events.append({
            "icon": "📝",
            "title": "Mock Day",
            "type": "mock_day",
            "description": "Test uchun tayyorlanish kuni - barcha mavzularga qa'ta bilish",
            "color": "red"
        })

    # Mock Result
    if target_date.weekday() == 3:
        day_events.append({
            "icon": "✓",
            "title": "Mock Result",
            "type": "mock_result",
            "description": "Test natijalarini o'rganish va o'z xatolarini tahlil qilish",
            "color": "green"
        })

    # Holidays
    if target_date in holidays:
        for holiday in holidays[target_date]:
            day_events.append({
                "icon": "🎉",
                "title": holiday["title"],
                "title_uz": holiday.get("title_uz", ""),
                "type": "holiday",
                "description": holiday.get("description", ""),
                "color": "yellow"
            })

    # Study breaks
    if target_date in study_breaks:
        for break_item in study_breaks[target_date]:
            day_events.append({
                "icon": "🏖️",
                "title": break_item["title"],
                "type": "study_break",
                "description": "Oqish markazi 2 kunlik damasi - dam ola olasiz",
                "color": "green"
            })

    context = {
        "date": target_date,
        "date_str": target_date.strftime("%d-%m-%Y"),
        "day_name": UZBEK_WEEKDAYS[target_date.weekday()],
        "is_today": target_date == today,
        "is_weekend": target_date.weekday() in [5, 6],
        "events": day_events,
        "event_count": len(day_events),
    }

    return render(request, "calendar_day_details.html", context)


@login_required
def calendar_events_list(request):
    """
    Barcha eventlarni ro'yxat sifatida ko'rsatadi - filter qilish mumkin
    """
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    event_type = request.GET.get("type", None)

    fixed_holidays = get_fixed_holidays(year)
    islamic_holidays = get_islamic_holidays(year)
    holidays = merge_holidays(fixed_holidays, islamic_holidays)
    study_breaks = get_study_breaks(year)

    all_events = []

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    for week in month_days:
        for day in week:
            if day.month != month:
                continue

            # Mock Days
            if day.weekday() == 6:
                if not event_type or event_type == "mock_day":
                    all_events.append({
                        "date": day,
                        "date_str": day.strftime("%d-%m-%Y"),
                        "day_name": UZBEK_WEEKDAYS[day.weekday()],
                        "icon": "📝",
                        "title": "Mock Day",
                        "type": "mock_day",
                        "class": "badge-red",
                        "description": "Test uchun mo'ljallangan kun",
                    })

            # Mock Results
            if day.weekday() == 3:
                if not event_type or event_type == "mock_result":
                    all_events.append({
                        "date": day,
                        "date_str": day.strftime("%d-%m-%Y"),
                        "day_name": UZBEK_WEEKDAYS[day.weekday()],
                        "icon": "✓",
                        "title": "Mock Result",
                        "type": "mock_result",
                        "class": "badge-green",
                        "description": "Test natijalarini o'rganish",
                    })

            # Holidays
            if day in holidays and (not event_type or event_type == "holiday"):
                for holiday in holidays[day]:
                    all_events.append({
                        "date": day,
                        "date_str": day.strftime("%d-%m-%Y"),
                        "day_name": UZBEK_WEEKDAYS[day.weekday()],
                        "icon": "🎉",
                        "title": holiday["title"],
                        "title_uz": holiday.get("title_uz", ""),
                        "type": "holiday",
                        "class": "badge-yellow",
                        "description": holiday.get("description", ""),
                    })

            # Study Breaks
            if day in study_breaks and (not event_type or event_type == "study_break"):
                for break_item in study_breaks[day]:
                    all_events.append({
                        "date": day,
                        "date_str": day.strftime("%d-%m-%Y"),
                        "day_name": UZBEK_WEEKDAYS[day.weekday()],
                        "icon": "🏖️",
                        "title": break_item["title"],
                        "type": "study_break",
                        "class": "badge-study-break",
                        "description": "Oqish markaz 2 kunlik damasi",
                    })

    all_events.sort(key=lambda x: x["date"])

    context = {
        "events": all_events,
        "year": year,
        "month": month,
        "month_name": UZBEK_MONTH_NAMES[month],
        "event_type": event_type,
        "event_count": len(all_events),
    }

    return render(request, "calendar_events_list.html", context)


@login_required
def calendar_month_compare(request):
    """
    Ikki oyni taqqoslash
    """
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month1 = int(request.GET.get("month1", today.month))
    month2 = int(request.GET.get("month2", (today.month % 12) + 1))

    def get_month_info(year, month):
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(year, month)

        fixed_holidays = get_fixed_holidays(year)
        islamic_holidays = get_islamic_holidays(year)
        holidays = merge_holidays(fixed_holidays, islamic_holidays)
        study_breaks = get_study_breaks(year)

        stats = {
            "month": month,
            "year": year,
            "month_name": UZBEK_MONTH_NAMES[month],
            "mock_days": 0,
            "mock_results": 0,
            "holidays": 0,
            "study_breaks": 0,
        }

        for week in month_days:
            for day in week:
                if day.month != month:
                    continue

                if day.weekday() == 6:
                    stats["mock_days"] += 1

                if day.weekday() == 3:
                    stats["mock_results"] += 1

                if day in holidays:
                    stats["holidays"] += len(holidays[day])

                if day in study_breaks:
                    stats["study_breaks"] += len(study_breaks[day])

        return stats

    month1_info = get_month_info(year, month1)
    month2_info = get_month_info(year, month2)

    context = {
        "month1": month1_info,
        "month2": month2_info,
        "year": year,
    }

    return render(request, "calendar.html", context)