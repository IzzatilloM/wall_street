import calendar
from datetime import date, timedelta
from hijri_converter import Hijri, Gregorian

# ==================== O'ZBEK TILIDA CALENDAR DATA ====================

UZBEK_MONTH_NAMES = {
    1: "Yanvar",
    2: "Fevral",
    3: "Mart",
    4: "Aprel",
    5: "May",
    6: "Iyun",
    7: "Iyul",
    8: "Avgust",
    9: "Sentabr",
    10: "Oktabr",
    11: "Noyabr",
    12: "Dekabr",
}

UZBEK_WEEKDAYS = [
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba",
    "Yakshanba",
]

UZBEK_WEEKDAYS_SHORT = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


# ==================== FIXED HOLIDAYS ====================

def get_fixed_holidays(year):
    """
    Qat'iy sanadan belgilangan bayramlar
    Navro'z, Mustaqillik kuni, Konstitutsiya kuni, va boshqalar
    """
    holidays = {}

    fixed_dates = [
        (1, 1, "New Year's Day", "Yangi yil", "Yangi yilning birinchi kuni - rasmiy ta'til"),
        (3, 8, "International Women's Day", "Ayollar kuni", "Xalqaro ayollar kuni"),
        (3, 21, "Navruz", "Navro'z", "Bahorning kelishi va yangi yil - milliy bayram"),
        (9, 1, "Independence Day", "Mustaqillik kuni", "O'zbekiston Respublikasining mustaqillik kuni"),
        (9, 16, "Memorial Day", "Xalq yodgorasi kuni", "Qahramanlarni yodga olish kuni"),
        (12, 8, "Constitution Day", "Konstitutsiya kuni", "O'zbekiston konstitutsiyas qabul qilish kuni"),
    ]

    for month, day, title_en, title_uz, description in fixed_dates:
        try:
            holiday_date = date(year, month, day)
            if holiday_date not in holidays:
                holidays[holiday_date] = []

            holidays[holiday_date].append({
                "title": title_en,
                "title_uz": title_uz,
                "type": "fixed_holiday",
                "description": description,
                "month": month,
                "day": day,
            })
        except ValueError:
            continue

    return holidays


# ==================== ISLAMIC HOLIDAYS ====================

def get_islamic_holidays(year):
    """
    Islomiy bayramlar - Hijri kalendariga asoslangan
    Ramazon bayrami va Qurbonlik bayrami
    """
    holidays = {}

    islamic_holidays_data = [
        (1, 1, "Islamic New Year", "Hijri yangi yil", "Islomiy taqvim bo'yicha yangi yil"),
        (3, 12, "Prophet Muhammad's Birthday", "Mavlid", "Payg'ambar Muhammad (s.a.v.) tug'ilgan kuni"),
        (9, 1, "Ramadan Begins", "Ramazon oyining boshlanishi", "O'roza oylining boshlanishi"),
        (10, 1, "Eid al-Fitr", "Ramazon bayrami", "O'rozaning oxiri - Ramazon bayrami"),
        (12, 8, "Eid al-Adha", "Qurbonlik bayrami", "Qurbon bayrami - Ibrohim Payg'ambar xikoyasi"),
    ]

    for hijri_month, hijri_day, title_en, title_uz, description in islamic_holidays_data:
        try:
            hijri = Hijri(year, hijri_month, hijri_day)
            gregorian = hijri.to_gregorian()
            gregorian_date = date(gregorian.year, gregorian.month, gregorian.day)

            if gregorian_date not in holidays:
                holidays[gregorian_date] = []

            holidays[gregorian_date].append({
                "title": title_en,
                "title_uz": title_uz,
                "type": "islamic_holiday",
                "description": description,
                "hijri_month": hijri_month,
                "hijri_day": hijri_day,
            })
        except Exception as e:
            continue

    return holidays


# ==================== STUDY BREAKS - HAR 2 OYDA 2 KUN ====================

def get_study_breaks(year):
    """
    Oqish markaz 2 kunlik damasi - har 2 oyda bir
    Fevral 15-16, Aprel 15-16, Iyun 15-16,
    Avgust 15-16, Oktabr 15-16, Dekabr 15-16
    """
    study_breaks = {}

    # Har 2 oyda 2 kunlik break jadval
    break_schedule = [
        ((2, 15), (2, 16), "1-Qo'shiq 2 kunlik dam", "1-quarter study break"),
        ((4, 15), (4, 16), "2-Qo'shiq 2 kunlik dam", "2-quarter study break"),
        ((6, 15), (6, 16), "3-Qo'shiq 2 kunlik dam", "Summer break start"),
        ((8, 15), (8, 16), "4-Qo'shiq 2 kunlik dam", "Back to studies"),
        ((10, 15), (10, 16), "5-Qo'shiq 2 kunlik dam", "Mid-autumn break"),
        ((12, 15), (12, 16), "6-Qo'shiq 2 kunlik dam", "Winter break"),
    ]

    for (start_month, start_day), (end_month, end_day), title_uz, title_en in break_schedule:
        try:
            start_date = date(year, start_month, start_day)
            end_date = date(year, end_month, end_day)

            # 2 kunlik dam davomiga
            current_date = start_date
            while current_date <= end_date:
                if current_date not in study_breaks:
                    study_breaks[current_date] = []

                study_breaks[current_date].append({
                    "title": title_en,
                    "title_uz": title_uz,
                    "type": "study_break",
                    "description": f"Oqish markaz ta'liti - {title_uz}",
                    "start_date": start_date,
                    "end_date": end_date,
                })

                current_date += timedelta(days=1)
        except ValueError:
            continue

    return study_breaks


# ==================== MERGE HOLIDAYS ====================

def merge_holidays(fixed_holidays, islamic_holidays):
    """
    Barcha bayramlarni bitta dictionaryga birlashtirvish
    """
    merged = dict(fixed_holidays)

    for date_key, holiday_list in islamic_holidays.items():
        if date_key not in merged:
            merged[date_key] = []
        merged[date_key].extend(holiday_list)

    return merged


# ==================== MONTH STATISTICS ====================

def get_month_statistics(year, month):
    """
    Oyning statistikasi - mock day, result, holiday, break sonlari
    """
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    fixed_holidays = get_fixed_holidays(year)
    islamic_holidays = get_islamic_holidays(year)
    holidays = merge_holidays(fixed_holidays, islamic_holidays)
    study_breaks = get_study_breaks(year)

    stats = {
        "mock_days": 0,
        "mock_results": 0,
        "holidays": 0,
        "study_breaks": 0,
        "weekend_days": 0,
        "working_days": 0,
        "total_days": 0,
    }

    for week in month_days:
        for day in week:
            if day.month != month:
                continue

            stats["total_days"] += 1

            # Mock Days
            if day.weekday() == 6:
                stats["mock_days"] += 1

            # Mock Results
            if day.weekday() == 3:
                stats["mock_results"] += 1

            # Holidays
            if day in holidays:
                stats["holidays"] += len(holidays[day])

            # Study breaks
            if day in study_breaks:
                stats["study_breaks"] += len(study_breaks[day])

            # Weekend
            if day.weekday() in [5, 6]:
                stats["weekend_days"] += 1
            else:
                stats["working_days"] += 1

    return stats


# ==================== GET ALL MONTH EVENTS ====================

def get_all_month_events(year, month):
    """
    Oyning barcha eventlarini qaytaradi
    """
    fixed_holidays = get_fixed_holidays(year)
    islamic_holidays = get_islamic_holidays(year)
    holidays = merge_holidays(fixed_holidays, islamic_holidays)
    study_breaks = get_study_breaks(year)

    all_events = {}

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)

    for week in month_days:
        for day in week:
            if day.month != month:
                continue

            day_events = []

            # Mock Day
            if day.weekday() == 6:
                day_events.append({
                    "title": "Mock Day",
                    "type": "mock_day",
                    "color": "red",
                    "icon": "📝",
                })

            # Mock Result
            if day.weekday() == 3:
                day_events.append({
                    "title": "Mock Result",
                    "type": "mock_result",
                    "color": "green",
                    "icon": "✓",
                })

            # Holidays
            if day in holidays:
                for holiday in holidays[day]:
                    day_events.append({
                        "title": holiday["title"],
                        "title_uz": holiday.get("title_uz", ""),
                        "type": "holiday",
                        "color": "yellow",
                        "icon": "🎉",
                    })

            # Study breaks
            if day in study_breaks:
                for break_item in study_breaks[day]:
                    day_events.append({
                        "title": break_item["title"],
                        "type": "study_break",
                        "color": "green",
                        "icon": "🏖️",
                    })

            if day_events:
                all_events[day] = day_events

    return all_events


# ==================== GET UPCOMING EVENTS ====================

def get_upcoming_events(days_ahead=30):
    """
    Keyingi N kunlardagi barcha eventlar
    """
    today = date.today()
    upcoming_events = []

    for i in range(days_ahead):
        current_date = today + timedelta(days=i)
        year = current_date.year

        fixed_holidays = get_fixed_holidays(year)
        islamic_holidays = get_islamic_holidays(year)
        holidays = merge_holidays(fixed_holidays, islamic_holidays)
        study_breaks = get_study_breaks(year)

        day_events = []

        # Mock Day
        if current_date.weekday() == 6:
            day_events.append({
                "title": "Mock Day",
                "type": "mock_day",
                "color": "red",
                "icon": "📝",
            })

        # Mock Result
        if current_date.weekday() == 3:
            day_events.append({
                "title": "Mock Result",
                "type": "mock_result",
                "color": "green",
                "icon": "✓",
            })

        # Holidays
        if current_date in holidays:
            for holiday in holidays[current_date]:
                day_events.append({
                    "title": holiday["title"],
                    "type": "holiday",
                    "color": "yellow",
                    "icon": "🎉",
                })

        # Study breaks
        if current_date in study_breaks:
            for break_item in study_breaks[current_date]:
                day_events.append({
                    "title": break_item["title"],
                    "type": "study_break",
                    "color": "green",
                    "icon": "🏖️",
                })

        if day_events:
            upcoming_events.append({
                "date": current_date,
                "day_name": UZBEK_WEEKDAYS[current_date.weekday()],
                "events": day_events,
            })

    return upcoming_events


# ==================== DATE UTILITIES ====================

def is_mock_day(day):
    """Yakshanba mi tekshirish"""
    return day.weekday() == 6


def is_mock_result(day):
    """Payshanba mi tekshirish"""
    return day.weekday() == 3


def is_weekend(day):
    """Veeked mi tekshirish (Shanba-Yakshanba)"""
    return day.weekday() in [5, 6]


def get_day_events_summary(year, month, day):
    """
    Kunning barcha eventlarini qaytaradi
    """
    fixed_holidays = get_fixed_holidays(year)
    islamic_holidays = get_islamic_holidays(year)
    holidays = merge_holidays(fixed_holidays, islamic_holidays)
    study_breaks = get_study_breaks(year)

    target_date = date(year, month, day)
    events = []

    if target_date.weekday() == 6:
        events.append({"title": "Mock Day", "type": "mock_day", "icon": "📝"})

    if target_date.weekday() == 3:
        events.append({"title": "Mock Result", "type": "mock_result", "icon": "✓"})

    if target_date in holidays:
        for holiday in holidays[target_date]:
            events.append({
                "title": holiday["title"],
                "type": "holiday",
                "icon": "🎉"
            })

    if target_date in study_breaks:
        for break_item in study_breaks[target_date]:
            events.append({
                "title": break_item["title"],
                "type": "study_break",
                "icon": "🏖️"
            })

    return events