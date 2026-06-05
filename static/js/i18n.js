/* ============================================================================
   Wall Street CRM — 3 tilli interfeys (O'zbek / Русский / English)
   ----------------------------------------------------------------------------
   Ishlash printsipi:
     • Sahifadagi matnlar manba (source) qatori bo'yicha lug'atdan tarjima
       qilinadi. Manba qatorlari aralash (inglizcha va o'zbekcha) bo'lishi
       mumkin — har bir kalit uchun [uz, ru, en] tarjimasi beriladi.
     • Til localStorage'da saqlanadi (kalit: "wallstreet-lang"), standart: uz.
     • MutationObserver tufayli JS orqali keyin qo'shilgan matnlar (modal,
       AJAX ro'yxat va h.k.) ham avtomatik tarjima qilinadi.
     • Til tugmasi (topbar yoki suzuvchi) bosilganda butun sahifa darrov
       almashadi — qayta yuklash shart emas.
   ========================================================================== */
(function () {
    'use strict';

    var STORE_KEY = 'wallstreet-lang';
    var DEFAULT   = 'uz';
    var LANGS     = ['uz', 'ru', 'en'];
    var IDX       = { uz: 0, ru: 1, en: 2 };
    var LANG_NAME = { uz: "O'zbek", ru: 'Русский', en: 'English' };

    /* ──────────────────────────────────────────────────────────────────────
       LUG'AT — manba qatori : [uz, ru, en]
       (Agar manba inglizcha bo'lsa en = manba; agar o'zbekcha bo'lsa uz = manba)
       ────────────────────────────────────────────────────────────────────── */
    var T = {
        /* ── Umumiy / Common ── */
        "Search": ["Qidirish", "Поиск", "Search"],
        "Search...": ["Qidirish...", "Поиск...", "Search..."],
        "Cancel": ["Bekor qilish", "Отмена", "Cancel"],
        "Save": ["Saqlash", "Сохранить", "Save"],
        "Save changes": ["O'zgarishlarni saqlash", "Сохранить изменения", "Save changes"],
        "Update": ["Yangilash", "Обновить", "Update"],
        "Edit": ["Tahrirlash", "Редактировать", "Edit"],
        "Delete": ["O'chirish", "Удалить", "Delete"],
        "O'chirish": ["O'chirish", "Удалить", "Delete"],
        "Close": ["Yopish", "Закрыть", "Close"],
        "Yopish": ["Yopish", "Закрыть", "Close"],
        "View": ["Ko'rish", "Просмотр", "View"],
        "View details": ["Batafsil ko'rish", "Подробнее", "View details"],
        "Details": ["Tafsilotlar", "Подробности", "Details"],
        "Back": ["Orqaga", "Назад", "Back"],
        "Ortga": ["Orqaga", "Назад", "Back"],
        "Back to list": ["Ro'yxatga qaytish", "К списку", "Back to list"],
        "Yes, delete": ["Ha, o'chirish", "Да, удалить", "Yes, delete"],
        "Status": ["Holat", "Статус", "Status"],
        "Actions": ["Amallar", "Действия", "Actions"],
        "Action": ["Amal", "Действие", "Action"],
        "Phone": ["Telefon", "Телефон", "Phone"],
        "Email": ["Email", "Эл. почта", "Email"],
        "Name": ["Ism", "Имя", "Name"],
        "First name": ["Ism", "Имя", "First name"],
        "Last name": ["Familiya", "Фамилия", "Last name"],
        "First name *": ["Ism *", "Имя *", "First name *"],
        "Last name *": ["Familiya *", "Фамилия *", "Last name *"],
        "Phone *": ["Telefon *", "Телефон *", "Phone *"],
        "Course": ["Kurs", "Курс", "Course"],
        "Courses": ["Kurslar", "Курсы", "Courses"],
        "Teacher": ["O'qituvchi", "Преподаватель", "Teacher"],
        "Teachers": ["O'qituvchilar", "Преподаватели", "Teachers"],
        "Instructor": ["O'qituvchi", "Преподаватель", "Instructor"],
        "Instructors": ["O'qituvchilar", "Преподаватели", "Instructors"],
        "Student": ["Talaba", "Студент", "Student"],
        "Students": ["Talabalar", "Студенты", "Students"],
        "Active": ["Faol", "Активный", "Active"],
        "Inactive": ["Nofaol", "Неактивный", "Inactive"],
        "Nofaol": ["Nofaol", "Неактивный", "Inactive"],
        "All": ["Hammasi", "Все", "All"],
        "Date": ["Sana", "Дата", "Date"],
        "Sana": ["Sana", "Дата", "Date"],
        "Amount": ["Summa", "Сумма", "Amount"],
        "Note": ["Izoh", "Заметка", "Note"],
        "Note (optional)": ["Izoh (ixtiyoriy)", "Заметка (необязательно)", "Note (optional)"],
        "Gender": ["Jinsi", "Пол", "Gender"],
        "Male": ["Erkak", "Мужской", "Male"],
        "Female": ["Ayol", "Женский", "Female"],
        "👦 Male": ["👦 Erkak", "👦 Мужской", "👦 Male"],
        "👧 Female": ["👧 Ayol", "👧 Женский", "👧 Female"],
        "Address": ["Manzil", "Адрес", "Address"],
        "Source": ["Manba", "Источник", "Source"],
        "Payment": ["To'lov", "Оплата", "Payment"],
        "Payments": ["To'lovlar", "Платежи", "Payments"],
        "Date of birth": ["Tug'ilgan sana", "Дата рождения", "Date of birth"],
        "Username": ["Foydalanuvchi nomi", "Имя пользователя", "Username"],
        "Password": ["Parol", "Пароль", "Password"],
        "Bio": ["Bio", "Биография", "Bio"],
        "Specialization": ["Mutaxassislik", "Специализация", "Specialization"],
        "Experience": ["Tajriba", "Опыт", "Experience"],
        "Salary": ["Maosh", "Зарплата", "Salary"],
        "Group": ["Guruh", "Группа", "Group"],
        "Start date": ["Boshlanish sanasi", "Дата начала", "Start date"],
        "End date": ["Tugash sanasi", "Дата окончания", "End date"],
        "Start": ["Boshlanish", "Начало", "Start"],
        "End": ["Tugash", "Конец", "End"],
        "Created by": ["Kim yaratgan", "Кем создан", "Created by"],
        "Discount": ["Chegirma", "Скидка", "Discount"],
        "Method": ["Usul", "Способ", "Method"],
        "Search by student name or ID...": ["Talaba ismi yoki ID bo'yicha qidirish...", "Поиск по имени или ID студента...", "Search by student name or ID..."],
        "🔍 Search by student name or ID...": ["🔍 Talaba ismi yoki ID bo'yicha qidirish...", "🔍 Поиск по имени или ID студента...", "🔍 Search by student name or ID..."],
        "Tozalash": ["Tozalash", "Очистить", "Clear"],
        "Clear": ["Tozalash", "Очистить", "Clear"],
        "Filter": ["Filtr", "Фильтр", "Filter"],
        "Export CSV": ["CSV yuklab olish", "Экспорт CSV", "Export CSV"],
        "No data": ["Ma'lumot yo'q", "Нет данных", "No data"],
        "Oldingi": ["Oldingi", "Предыдущая", "Previous"],
        "Keyingi": ["Keyingi", "Следующая", "Next"],

        /* ── Sidebar / Nav ── */
        "Education Centre": ["O'quv markazi", "Учебный центр", "Education Centre"],
        "Current Access": ["Joriy ruxsat", "Текущий доступ", "Current Access"],
        "Teacher panel — attendance only": ["O'qituvchi paneli — faqat davomat", "Панель преподавателя — только посещаемость", "Teacher panel — attendance only"],
        "Admin panel — full management access": ["Admin paneli — to'liq boshqaruv", "Панель администратора — полный доступ", "Admin panel — full management access"],
        "Learning": ["Ta'lim", "Обучение", "Learning"],
        "Main": ["Asosiy", "Главная", "Main"],
        "Dashboard": ["Boshqaruv paneli", "Панель", "Dashboard"],
        "Analytics & Overview": ["Tahlil va umumiy ko'rinish", "Аналитика и обзор", "Analytics & Overview"],
        "Student management": ["Talabalarni boshqarish", "Управление студентами", "Student management"],
        "Course management": ["Kurslarni boshqarish", "Управление курсами", "Course management"],
        "Course registrations": ["Kursga yozilishlar", "Запись на курсы", "Course registrations"],
        "Enrollments": ["Ro'yxatga olish", "Зачисления", "Enrollments"],
        "Enrollment": ["Ro'yxatga olish", "Зачисление", "Enrollment"],
        "Attendance": ["Davomat", "Посещаемость", "Attendance"],
        "Class attendance": ["Dars davomati", "Посещаемость занятий", "Class attendance"],
        "Finance": ["Moliya", "Финансы", "Finance"],
        "Student payments": ["Talaba to'lovlari", "Платежи студентов", "Student payments"],
        "Staff salaries": ["Xodimlar maoshi", "Зарплаты сотрудников", "Staff salaries"],
        "Reports": ["Hisobotlar", "Отчёты", "Reports"],
        "Reports & analytics": ["Hisobot va tahlil", "Отчёты и аналитика", "Reports & analytics"],
        "Reports &amp; analytics": ["Hisobot va tahlil", "Отчёты и аналитика", "Reports & analytics"],
        "Other": ["Boshqa", "Прочее", "Other"],
        "Calendar": ["Kalendar", "Календарь", "Calendar"],
        "Settings": ["Sozlamalar", "Настройки", "Settings"],
        "Logout": ["Chiqish", "Выход", "Logout"],
        "Home": ["Bosh sahifa", "Главная", "Home"],
        "Administrator": ["Administrator", "Администратор", "Administrator"],
        "Toggle theme": ["Mavzuni almashtirish", "Сменить тему", "Toggle theme"],
        "Notifications": ["Bildirishnomalar", "Уведомления", "Notifications"],
        "📨 Telegram arizalar": ["📨 Telegram arizalar", "📨 Заявки из Telegram", "📨 Telegram requests"],
        "Yangi ariza yo'q": ["Yangi ariza yo'q", "Нет новых заявок", "No new requests"],
        "📨 Telegram bot orqali ariza": ["📨 Telegram bot orqali ariza", "📨 Заявка через Telegram-бот", "📨 Request via Telegram bot"],
        "Ism F.": ["Ism F.", "Ф.И.О.", "Full name"],
        "Telefon": ["Telefon", "Телефон", "Phone"],
        "Telegram": ["Telegram", "Telegram", "Telegram"],
        "Vaqt": ["Vaqt", "Время", "Time"],
        "Ro'yxatga olish": ["Ro'yxatga olish", "Зачислить", "Enroll"],
        "Privacy Policy": ["Maxfiylik siyosati", "Политика конфиденциальности", "Privacy Policy"],
        "Terms & Conditions": ["Shartlar va qoidalar", "Условия и положения", "Terms & Conditions"],
        "Support": ["Yordam", "Поддержка", "Support"],
        "Contact": ["Aloqa", "Контакты", "Contact"],

        /* ── Dashboard ── */
        "Control  Panel": ["Boshqaruv paneli", "Панель управления", "Control Panel"],
        "Control Panel": ["Boshqaruv paneli", "Панель управления", "Control Panel"],
        "Wall Street Education Centre": ["Wall Street o'quv markazi", "Учебный центр Wall Street", "Wall Street Education Centre"],
        "📊 Professional analytics dashboard for comprehensive student management, course monitoring, payment tracking, attendance records, instructor oversight, and expense analysis. Real-time insights for better decision making.":
            ["📊 Talabalarni boshqarish, kurs monitoringi, to'lov nazorati, davomat, o'qituvchilar va xarajatlar tahlili uchun professional boshqaruv paneli. Yaxshiroq qaror qabul qilish uchun real vaqt ma'lumotlari.",
             "📊 Профессиональная аналитическая панель для управления студентами, мониторинга курсов, отслеживания платежей, посещаемости, преподавателей и анализа расходов. Данные в реальном времени для лучших решений.",
             "📊 Professional analytics dashboard for comprehensive student management, course monitoring, payment tracking, attendance records, instructor oversight, and expense analysis. Real-time insights for better decision making."],
        "📈 Monthly Income": ["📈 Oylik daromad", "📈 Месячный доход", "📈 Monthly Income"],
        "Completed payments": ["Yakunlangan to'lovlar", "Завершённые платежи", "Completed payments"],
        "⏳ Pending Amount": ["⏳ Kutilayotgan summa", "⏳ Ожидаемая сумма", "⏳ Pending Amount"],
        "Awaiting confirmation": ["Tasdiqlash kutilmoqda", "Ожидает подтверждения", "Awaiting confirmation"],
        "👥 Active Students": ["👥 Faol talabalar", "👥 Активные студенты", "👥 Active Students"],
        "Currently enrolled": ["Hozir o'qiyotgan", "Сейчас обучаются", "Currently enrolled"],
        "👨‍🏫 Instructors": ["👨‍🏫 O'qituvchilar", "👨‍🏫 Преподаватели", "👨‍🏫 Instructors"],
        "Teaching staff": ["O'qituvchilar tarkibi", "Преподавательский состав", "Teaching staff"],
        "Total Students": ["Jami talabalar", "Всего студентов", "Total Students"],
        "Active Courses": ["Faol kurslar", "Активные курсы", "Active Courses"],
        "Monthly Revenue": ["Oylik daromad", "Месячный доход", "Monthly Revenue"],
        "Pending Payments": ["Kutilayotgan to'lovlar", "Ожидаемые платежи", "Pending Payments"],
        "Attendance Records": ["Davomat yozuvlari", "Записи посещаемости", "Attendance Records"],
        "Present": ["Kelgan", "Присутствует", "Present"],
        "Absent": ["Kelmagan", "Отсутствует", "Absent"],
        "Late Arrivals": ["Kechikkanlar", "Опоздания", "Late Arrivals"],
        "Late": ["Kechikkan", "Опоздал", "Late"],
        "Students present in class": ["Darsda hozir bo'lganlar", "Присутствовали на занятии", "Students present in class"],
        "Students absent from class": ["Darsga kelmaganlar", "Отсутствовали на занятии", "Students absent from class"],
        "Students who arrived late": ["Kechikib kelganlar", "Опоздавшие студенты", "Students who arrived late"],
        "Complete attendance history": ["To'liq davomat tarixi", "Полная история посещаемости", "Complete attendance history"],
        "Awaiting confirmation from students": ["Talabalardan tasdiq kutilmoqda", "Ожидает подтверждения от студентов", "Awaiting confirmation from students"],
        "💹 Revenue Trends": ["💹 Daromad tendensiyalari", "💹 Динамика доходов", "💹 Revenue Trends"],
        "Monthly income analysis for the last 6 months": ["So'nggi 6 oylik daromad tahlili", "Анализ дохода за последние 6 месяцев", "Monthly income analysis for the last 6 months"],
        "Live Data": ["Jonli ma'lumot", "Данные в реальном времени", "Live Data"],
        "💳 Recent Transactions": ["💳 So'nggi tranzaksiyalar", "💳 Последние транзакции", "💳 Recent Transactions"],
        "Latest 10 payment records from the system": ["Tizimdagi so'nggi 10 ta to'lov", "Последние 10 платежей в системе", "Latest 10 payment records from the system"],
        "View All": ["Hammasini ko'rish", "Показать все", "View All"],
        "Receipt": ["Chek", "Чек", "Receipt"],
        "No payment records found": ["To'lov yozuvlari topilmadi", "Платежи не найдены", "No payment records found"],
        "📍 Recent Attendance": ["📍 So'nggi davomat", "📍 Последняя посещаемость", "📍 Recent Attendance"],
        "Latest attendance records and class participation": ["So'nggi davomat va darsda ishtirok", "Последние записи посещаемости", "Latest attendance records and class participation"],
        "No attendance records found": ["Davomat yozuvlari topilmadi", "Записи посещаемости не найдены", "No attendance records found"],
        "📊 Payment Status": ["📊 To'lov holati", "📊 Статус платежей", "📊 Payment Status"],
        "Completed, pending, cancelled breakdown": ["Yakunlangan, kutilayotgan, bekor qilingan", "Завершено, в ожидании, отменено", "Completed, pending, cancelled breakdown"],
        "💸 Expenses": ["💸 Xarajatlar", "💸 Расходы", "💸 Expenses"],
        "Current month expense distribution": ["Joriy oy xarajatlari taqsimoti", "Распределение расходов за месяц", "Current month expense distribution"],
        "No Data": ["Ma'lumot yo'q", "Нет данных", "No Data"],
        "Current month": ["Joriy oy", "Текущий месяц", "Current month"],
        "No expense data available": ["Xarajat ma'lumoti yo'q", "Нет данных о расходах", "No expense data available"],
        "🏆 Top Courses": ["🏆 Eng yaxshi kurslar", "🏆 Топ курсы", "🏆 Top Courses"],
        "Courses with highest attendance": ["Eng yuqori davomatli kurslar", "Курсы с наибольшей посещаемостью", "Courses with highest attendance"],
        "👨‍🏫 Teacher Activity": ["👨‍🏫 O'qituvchi faolligi", "👨‍🏫 Активность преподавателей", "👨‍🏫 Teacher Activity"],
        "Attendance records by instructor": ["O'qituvchilar bo'yicha davomat", "Посещаемость по преподавателям", "Attendance records by instructor"],

        /* ── Students ── */
        "Total students": ["Jami talabalar", "Всего студентов", "Total students"],
        "Name, phone or email...": ["Ism, telefon yoki email...", "Имя, телефон или email...", "Name, phone or email..."],
        "Ota-ona tel": ["Ota-ona tel", "Тел. родителя", "Parent phone"],
        "Ota-ona telefoni": ["Ota-ona telefoni", "Телефон родителя", "Parent phone"],
        "Edit student": ["Talabani tahrirlash", "Редактировать студента", "Edit student"],
        "✏️ Edit student": ["✏️ Talabani tahrirlash", "✏️ Редактировать студента", "✏️ Edit student"],
        "Profil rasmi": ["Profil rasmi", "Фото профиля", "Profile photo"],
        "JPG yoki PNG, kvadrat shaklda eng yaxshi ko'rinadi.": ["JPG yoki PNG, kvadrat shaklda eng yaxshi ko'rinadi.", "JPG или PNG, лучше всего квадратное изображение.", "JPG or PNG, square images look best."],
        "Rasm tanlash": ["Rasm tanlash", "Выбрать фото", "Choose photo"],
        "📷 Rasm tanlash": ["📷 Rasm tanlash", "📷 Выбрать фото", "📷 Choose photo"],
        "Active status": ["Faol holati", "Активный статус", "Active status"],
        "Are you sure you want to delete?": ["Rostan o'chirmoqchimisiz?", "Вы уверены, что хотите удалить?", "Are you sure you want to delete?"],
        "This student will be permanently removed from the system.": ["Bu talaba tizimdan butunlay o'chiriladi.", "Этот студент будет навсегда удалён из системы.", "This student will be permanently removed from the system."],
        "\"{name}\" will be permanently removed. This action cannot be undone.": ["\"{name}\" butunlay o'chiriladi. Bu amalni ortga qaytarib bo'lmaydi.", "«{name}» будет навсегда удалён. Это действие нельзя отменить.", "\"{name}\" will be permanently removed. This action cannot be undone."],
        "\"{name}\" enrollment will be permanently removed. This action cannot be undone.": ["\"{name}\" ro'yxati butunlay o'chiriladi. Bu amalni ortga qaytarib bo'lmaydi.", "Зачисление «{name}» будет навсегда удалено. Это действие нельзя отменить.", "\"{name}\" enrollment will be permanently removed. This action cannot be undone."],
        "— Tanlang —": ["— Tanlang —", "— Выберите —", "— Select —"],
        "Go to the Enrollments page": ["Ro'yxatga olish sahifasiga o'tish", "Перейти на страницу зачисления", "Go to the Enrollments page"],

        /* ── Courses ── */
        "Duration": ["Davomiyligi", "Длительность", "Duration"],
        "Number of students": ["Talabalar soni", "Количество студентов", "Number of students"],
        "Category": ["Kategoriya", "Категория", "Category"],
        "Dars kunlari": ["Dars kunlari", "Дни занятий", "Class days"],
        "Dars vaqti": ["Dars vaqti", "Время занятий", "Class time"],
        "Course description": ["Kurs tavsifi", "Описание курса", "Course description"],
        "Ushbu kurs uchun batafsil tavsif kiritilmagan.": ["Ushbu kurs uchun batafsil tavsif kiritilmagan.", "Подробное описание курса не указано.", "No detailed description for this course."],
        "Edit course": ["Kursni tahrirlash", "Редактировать курс", "Edit course"],
        "Delete course": ["Kursni o'chirish", "Удалить курс", "Delete course"],
        "Course name": ["Kurs nomi", "Название курса", "Course name"],
        "Select teacher": ["O'qituvchini tanlang", "Выберите преподавателя", "Select teacher"],
        "Level": ["Daraja", "Уровень", "Level"],
        "Duration unit": ["Davomiylik birligi", "Единица длительности", "Duration unit"],
        "Price (UZS)": ["Narxi (UZS)", "Цена (UZS)", "Price (UZS)"],
        "Description": ["Tavsif", "Описание", "Description"],
        "Boshlanish vaqti": ["Boshlanish vaqti", "Время начала", "Start time"],
        "Tugash vaqti": ["Tugash vaqti", "Время окончания", "End time"],
        "Dars kunlari (odatda haftada 3 kun)": ["Dars kunlari (odatda haftada 3 kun)", "Дни занятий (обычно 3 дня в неделю)", "Class days (usually 3 days a week)"],
        "Are you sure you want to delete this course?": ["Ushbu kursni o'chirmoqchimisiz?", "Вы уверены, что хотите удалить этот курс?", "Are you sure you want to delete this course?"],
        "Transfer": ["O'tkazish", "Перевести", "Transfer"],
        "Transfer student to another course": ["Talabani boshqa kursga o'tkazish", "Перевести студента на другой курс", "Transfer student to another course"],
        "Hozirgi kurs:": ["Hozirgi kurs:", "Текущий курс:", "Current course:"],
        "Select new course": ["Yangi kursni tanlang", "Выберите новый курс", "Select new course"],
        "Select course": ["Kursni tanlang", "Выберите курс", "Select course"],
        "No students in this course yet.": ["Bu kursda hali talaba yo'q.", "На этом курсе пока нет студентов.", "No students in this course yet."],
        "Unknown": ["Noma'lum", "Неизвестно", "Unknown"],

        /* ── Enrollments ── */
        "Total enrolled": ["Jami yozilganlar", "Всего зачислено", "Total enrolled"],
        "Kutilmoqda": ["Kutilmoqda", "В ожидании", "Pending"],
        "Pending": ["Kutilmoqda", "В ожидании", "Pending"],
        "Fully paid": ["To'liq to'langan", "Полностью оплачено", "Fully paid"],
        "Total income (UZS)": ["Umumiy daromad (UZS)", "Общий доход (UZS)", "Total income (UZS)"],
        "Umumiy qarzdorlik": ["Umumiy qarzdorlik", "Общая задолженность", "Total debt"],
        "Name, phone or course...": ["Ism, telefon yoki kurs...", "Имя, телефон или курс...", "Name, phone or course..."],
        "Muzlatilgan": ["Muzlatilgan", "Заморожено", "Frozen"],
        "Yakunlangan": ["Yakunlangan", "Завершено", "Completed"],
        "Cancelled": ["Bekor qilingan", "Отменено", "Cancelled"],
        "New enrollment": ["Yangi ro'yxat", "Новое зачисление", "New enrollment"],
        "Payment:": ["To'lov:", "Оплата:", "Payment:"],
        "To'lanmagan": ["To'lanmagan", "Не оплачено", "Unpaid"],
        "Qisman": ["Qisman", "Частично", "Partial"],
        "To'liq": ["To'liq", "Полностью", "Full"],
        "Muddati o'tgan": ["Muddati o'tgan", "Просрочено", "Overdue"],
        "Course / Group": ["Kurs / Guruh", "Курс / Группа", "Course / Group"],
        "Summa / Qarz": ["Summa / Qarz", "Сумма / Долг", "Amount / Debt"],
        "Change status": ["Holatni o'zgartirish", "Изменить статус", "Change status"],
        "Hali hech kim ro'yxatga olinmagan": ["Hali hech kim ro'yxatga olinmagan", "Пока никто не зачислен", "No one enrolled yet"],
        "Student information": ["Talaba ma'lumotlari", "Информация о студенте", "Student information"],
        "🎓 Student information": ["🎓 Talaba ma'lumotlari", "🎓 Информация о студенте", "🎓 Student information"],
        "Phone * (used as login)": ["Telefon * (login sifatida)", "Телефон * (используется как логин)", "Phone * (used as login)"],
        "Yashash manzili": ["Yashash manzili", "Адрес проживания", "Residential address"],
        "🔑 Tizimga kirish ma'lumotlari": ["🔑 Tizimga kirish ma'lumotlari", "🔑 Данные для входа", "🔑 Login credentials"],
        "Username (login)": ["Foydalanuvchi nomi (login)", "Имя пользователя (логин)", "Username (login)"],
        "Avtomatik: telefon raqami": ["Avtomatik: telefon raqami", "Автоматически: номер телефона", "Auto: phone number"],
        "Avtomatik: 12345678": ["Avtomatik: 12345678", "Автоматически: 12345678", "Auto: 12345678"],
        "Course & group": ["Kurs va guruh", "Курс и группа", "Course & group"],
        "📚 Course &amp; group": ["📚 Kurs va guruh", "📚 Курс и группа", "📚 Course & group"],
        "📚 Course & group": ["📚 Kurs va guruh", "📚 Курс и группа", "📚 Course & group"],
        "📚 Course information": ["📚 Kurs ma'lumotlari", "📚 Информация о курсе", "📚 Course information"],
        "Course information": ["Kurs ma'lumotlari", "Информация о курсе", "Course information"],
        "💳 Moliyaviy ma'lumotlar": ["💳 Moliyaviy ma'lumotlar", "💳 Финансовые данные", "💳 Financial details"],
        "Moliyaviy ma'lumotlar": ["Moliyaviy ma'lumotlar", "Финансовые данные", "Financial details"],
        "Course price (UZS)": ["Kurs narxi (UZS)", "Цена курса (UZS)", "Course price (UZS)"],
        "Discount (UZS)": ["Chegirma (UZS)", "Скидка (UZS)", "Discount (UZS)"],
        "Initial payment (UZS)": ["Boshlang'ich to'lov (UZS)", "Первоначальный платёж (UZS)", "Initial payment (UZS)"],
        "Paid amount (UZS)": ["To'langan summa (UZS)", "Оплаченная сумма (UZS)", "Paid amount (UZS)"],
        "Payment status": ["To'lov holati", "Статус оплаты", "Payment status"],
        "⚙️ Status &amp; note": ["⚙️ Holat va izoh", "⚙️ Статус и заметка", "⚙️ Status & note"],
        "⚙️ Status & note": ["⚙️ Holat va izoh", "⚙️ Статус и заметка", "⚙️ Status & note"],
        "Status & note": ["Holat va izoh", "Статус и заметка", "Status & note"],
        "Enrollment holati": ["Ro'yxat holati", "Статус зачисления", "Enrollment status"],
        "Qo'shimcha ma'lumot...": ["Qo'shimcha ma'lumot...", "Дополнительная информация...", "Additional info..."],
        "Enroll": ["Ro'yxatga olish", "Зачислить", "Enroll"],
        "✅ Enroll": ["✅ Ro'yxatga olish", "✅ Зачислить", "✅ Enroll"],
        "Enrollment tahrirlash": ["Ro'yxatni tahrirlash", "Редактировать зачисление", "Edit enrollment"],
        "✏️ Enrollment tahrirlash": ["✏️ Ro'yxatni tahrirlash", "✏️ Редактировать зачисление", "✏️ Edit enrollment"],
        "This enrollment will be permanently removed from the system.": ["Bu ro'yxat tizimdan butunlay o'chiriladi.", "Это зачисление будет навсегда удалено из системы.", "This enrollment will be permanently removed from the system."],
        "Yuklanmoqda...": ["Yuklanmoqda...", "Загрузка...", "Loading..."],
        "Ma'lumotlar yuklanmoqda...": ["Ma'lumotlar yuklanmoqda...", "Загрузка данных...", "Loading data..."],
        "📋 New enrollment": ["📋 Yangi ro'yxat", "📋 Новое зачисление", "📋 New enrollment"],
        "Ota-ona": ["Ota-ona", "Родитель", "Parent"],
        "Tug'ilgan": ["Tug'ilgan", "Дата рождения", "Born"],
        "✅ Active": ["✅ Faol", "✅ Активный", "✅ Active"],
        "❌ Nofaol": ["❌ Nofaol", "❌ Неактивный", "❌ Inactive"],
        "🔑 Tizimga kirish": ["🔑 Tizimga kirish", "🔑 Вход в систему", "🔑 Login"],
        "Login": ["Login", "Логин", "Login"],
        "💳 Financial status": ["💳 Moliyaviy holat", "💳 Финансовое состояние", "💳 Financial status"],
        "Paid amount": ["To'langan summa", "Оплаченная сумма", "Paid amount"],
        "Course price": ["Kurs narxi", "Цена курса", "Course price"],
        "Net price": ["Sof narx", "Чистая цена", "Net price"],
        "Paid": ["To'langan", "Оплачено", "Paid"],
        "Remaining": ["Qoldiq", "Остаток", "Remaining"],
        "Net price": ["Sof narx", "Чистая цена", "Net price"],
        "💬 Note history": ["💬 Izohlar tarixi", "💬 История заметок", "💬 Note history"],
        "Write a new note...": ["Yangi izoh yozing...", "Напишите новую заметку...", "Write a new note..."],
        "Add note": ["Izoh qo'shish", "Добавить заметку", "Add note"],
        "No notes yet": ["Hali izoh yo'q", "Заметок пока нет", "No notes yet"],
        "Noma'lum": ["Noma'lum", "Неизвестно", "Unknown"],

        /* ── Instructors ── */
        "Total instructors": ["Jami o'qituvchilar", "Всего преподавателей", "Total instructors"],
        "Active instructors": ["Faol o'qituvchilar", "Активные преподаватели", "Active instructors"],
        "Add teacher": ["O'qituvchi qo'shish", "Добавить преподавателя", "Add teacher"],
        "Add admin": ["Admin qo'shish", "Добавить администратора", "Add admin"],
        "Adminlar": ["Adminlar", "Администраторы", "Admins"],
        "Adminlar (limit)": ["Adminlar (limit)", "Администраторы (лимит)", "Admins (limit)"],
        "Admin ro'yxati": ["Adminlar ro'yxati", "Список администраторов", "Admin list"],
        "Teacher ro'yxati": ["O'qituvchilar ro'yxati", "Список преподавателей", "Teacher list"],
        "Admin": ["Admin", "Администратор", "Admin"],
        "No admins": ["Adminlar yo'q", "Нет администраторов", "No admins"],
        "No teachers": ["O'qituvchilar yo'q", "Нет преподавателей", "No teachers"],
        "Add an admin using the button above.": ["Yuqoridagi tugma orqali admin qo'shing.", "Добавьте администратора с помощью кнопки выше.", "Add an admin using the button above."],
        "Add a teacher using the button above.": ["Yuqoridagi tugma orqali o'qituvchi qo'shing.", "Добавьте преподавателя с помощью кнопки выше.", "Add a teacher using the button above."],
        "Add new teacher": ["Yangi o'qituvchi qo'shish", "Добавить нового преподавателя", "Add new teacher"],
        "Add new admin": ["Yangi admin qo'shish", "Добавить нового администратора", "Add new admin"],
        "Account va profil bir vaqtda yaratiladi": ["Account va profil bir vaqtda yaratiladi", "Аккаунт и профиль создаются одновременно", "Account and profile are created together"],
        "Account ma'lumotlari": ["Account ma'lumotlari", "Данные аккаунта", "Account details"],
        "Profil ma'lumotlari": ["Profil ma'lumotlari", "Данные профиля", "Profile details"],
        "Username *": ["Foydalanuvchi nomi *", "Имя пользователя *", "Username *"],
        "Parol *": ["Parol *", "Пароль *", "Password *"],
        "To'liq ism *": ["To'liq ism *", "Полное имя *", "Full name *"],
        "Experience (years)": ["Tajriba (yil)", "Опыт (лет)", "Experience (years)"],
        "Salary ($)": ["Maosh ($)", "Зарплата ($)", "Salary ($)"],
        "Set as active": ["Faol deb belgilash", "Сделать активным", "Set as active"],
        "Instructor profili": ["O'qituvchi profili", "Профиль преподавателя", "Instructor profile"],
        "To'liq ma'lumotlar": ["To'liq ma'lumotlar", "Полная информация", "Full details"],
        "Instructorni tahrirlash": ["O'qituvchini tahrirlash", "Редактировать преподавателя", "Edit instructor"],
        "Profil ma'lumotlarini yangilash": ["Profil ma'lumotlarini yangilash", "Обновить данные профиля", "Update profile details"],
        "Delete instructor": ["O'qituvchini o'chirish", "Удалить преподавателя", "Delete instructor"],
        "Bu amal ortga qaytarilmaydi": ["Bu amal ortga qaytarilmaydi", "Это действие необратимо", "This action cannot be undone"],
        "Ushbu instructorning account va barcha profil ma'lumotlari tizimdan olib tashlanadi. Davom etishni xohlaysizmi?":
            ["Ushbu o'qituvchining account va barcha profil ma'lumotlari tizimdan olib tashlanadi. Davom etishni xohlaysizmi?",
             "Аккаунт и все данные профиля этого преподавателя будут удалены из системы. Продолжить?",
             "This instructor's account and all profile data will be removed from the system. Continue?"],
        "No email": ["Email yo'q", "Нет email", "No email"],
        "Kiritilmagan": ["Kiritilmagan", "Не указано", "Not specified"],
        "Qo'shimcha ma'lumot kiritilmagan.": ["Qo'shimcha ma'lumot kiritilmagan.", "Дополнительная информация не указана.", "No additional information provided."],

        /* ── Attendance ── */
        "Attendance management": ["Davomatni boshqarish", "Управление посещаемостью", "Attendance management"],
        "Attendance rate": ["Davomat darajasi", "Уровень посещаемости", "Attendance rate"],
        "Total": ["Jami", "Всего", "Total"],
        "Today": ["Bugun", "Сегодня", "Today"],
        "Today's records": ["Bugungi yozuvlar", "Сегодняшние записи", "Today's records"],
        "Attendance list": ["Davomat ro'yxati", "Список посещаемости", "Attendance list"],
        "Mark attendance": ["Davomat belgilash", "Отметить посещаемость", "Mark attendance"],
        "Coin berish": ["Coin berish", "Начислить коины", "Give coins"],
        "🪙 Coin berish": ["🪙 Coin berish", "🪙 Начислить коины", "🪙 Give coins"],
        "All courses": ["Barcha kurslar", "Все курсы", "All courses"],
        "All statuses": ["Barcha holatlar", "Все статусы", "All statuses"],
        "Attendance %": ["Davomat %", "Посещаемость %", "Attendance %"],
        "🪙 Coins": ["🪙 Coinlar", "🪙 Коины", "🪙 Coins"],
        "Filtrlarni o'zgartiring yoki yangi davomat belgilang.": ["Filtrlarni o'zgartiring yoki yangi davomat belgilang.", "Измените фильтры или отметьте новую посещаемость.", "Change the filters or mark new attendance."],
        "Edit attendance": ["Davomatni tahrirlash", "Редактировать посещаемость", "Edit attendance"],
        "Delete record": ["Yozuvni o'chirish", "Удалить запись", "Delete record"],
        "Ishonchingiz komilmi?": ["Ishonchingiz komilmi?", "Вы уверены?", "Are you sure?"],
        "Bu amalni ortga qaytarib bo'lmaydi.": ["Bu amalni ortga qaytarib bo'lmaydi.", "Это действие нельзя отменить.", "This action cannot be undone."],
        "Select a course first...": ["Avval kursni tanlang...", "Сначала выберите курс...", "Select a course first..."],
        "Students depend on the selected course.": ["Talabalar tanlangan kursga bog'liq.", "Студенты зависят от выбранного курса.", "Students depend on the selected course."],
        "Select a student...": ["Talabani tanlang...", "Выберите студента...", "Select a student..."],
        "Add a note...": ["Izoh qo'shing...", "Добавьте заметку...", "Add a note..."],
        "Joriy balans:": ["Joriy balans:", "Текущий баланс:", "Current balance:"],
        "Talaba": ["Talaba", "Студент", "Student"],
        "Tezkor tanlov": ["Tezkor tanlov", "Быстрый выбор", "Quick select"],
        "— Talabani tanlang —": ["— Talabani tanlang —", "— Выберите студента —", "— Select student —"],
        "Coin miqdori (manfiy = ayirish)": ["Coin miqdori (manfiy = ayirish)", "Кол-во коинов (минус = вычесть)", "Coin amount (negative = subtract)"],
        "Sabab (ixtiyoriy)": ["Sabab (ixtiyoriy)", "Причина (необязательно)", "Reason (optional)"],
        "Masalan: Faollik uchun, uy vazifasi...": ["Masalan: Faollik uchun, uy vazifasi...", "Например: за активность, домашнее задание...", "e.g.: for activity, homework..."],
        "🪙 Saqlash": ["🪙 Saqlash", "🪙 Сохранить", "🪙 Save"],
        "Iltimos, avval talabani tanlang.": ["Iltimos, avval talabani tanlang.", "Пожалуйста, сначала выберите студента.", "Please select a student first."],

        /* ── Reports ── */
        "Reports &amp; analytics": ["Hisobot va tahlil", "Отчёты и аналитика", "Reports & analytics"],
        "Financial metrics for": ["Moliyaviy ko'rsatkichlar:", "Финансовые показатели за", "Financial metrics for"],
        "Total income (UZS)": ["Umumiy daromad (UZS)", "Общий доход (UZS)", "Total income (UZS)"],
        "Expenses / salaries (UZS)": ["Xarajatlar / maoshlar (UZS)", "Расходы / зарплаты (UZS)", "Expenses / salaries (UZS)"],
        "Net profit (UZS)": ["Sof foyda (UZS)", "Чистая прибыль (UZS)", "Net profit (UZS)"],
        "Income &amp; expense trends": ["Daromad va xarajat tendensiyalari", "Динамика доходов и расходов", "Income & expense trends"],
        "Income & expense trends": ["Daromad va xarajat tendensiyalari", "Динамика доходов и расходов", "Income & expense trends"],
        "Overview": ["Umumiy ko'rinish", "Обзор", "Overview"],
        "Active enrollments": ["Faol ro'yxatlar", "Активные зачисления", "Active enrollments"],
        "Top courses by enrollments": ["Yozilishlar bo'yicha eng yaxshi kurslar", "Топ курсов по зачислениям", "Top courses by enrollments"],
        "Price": ["Narxi", "Цена", "Price"],

        /* ── Settings ── */
        "Manage your profile, center and security preferences": ["Profil, markaz va xavfsizlik sozlamalarini boshqaring", "Управляйте профилем, центром и настройками безопасности", "Manage your profile, center and security preferences"],
        "Profile": ["Profil", "Профиль", "Profile"],
        "Center": ["Markaz", "Центр", "Center"],
        "Security": ["Xavfsizlik", "Безопасность", "Security"],
        "Profile information": ["Profil ma'lumotlari", "Информация профиля", "Profile information"],
        "Update your personal details and profile photo.": ["Shaxsiy ma'lumotlar va profil rasmini yangilang.", "Обновите личные данные и фото профиля.", "Update your personal details and profile photo."],
        "Remove photo": ["Rasmni o'chirish", "Удалить фото", "Remove photo"],
        "Save changes": ["O'zgarishlarni saqlash", "Сохранить изменения", "Save changes"],
        "Center settings": ["Markaz sozlamalari", "Настройки центра", "Center settings"],
        "Details used across receipts, reports and the platform.": ["Cheklar, hisobotlar va platformada ishlatiladigan ma'lumotlar.", "Данные, используемые в чеках, отчётах и на платформе.", "Details used across receipts, reports and the platform."],
        "Change password": ["Parolni o'zgartirish", "Сменить пароль", "Change password"],
        "Enter your current password, then choose a new one.": ["Joriy parolni kiriting, so'ng yangisini tanlang.", "Введите текущий пароль, затем выберите новый.", "Enter your current password, then choose a new one."],
        "Reset password": ["Parolni tiklash", "Сбросить пароль", "Reset password"],
        "Set a brand new password without entering the old one.": ["Eski parolsiz yangi parol o'rnating.", "Установите новый пароль без ввода старого.", "Set a brand new password without entering the old one."],
        "Profile photo": ["Profil rasmi", "Фото профиля", "Profile photo"],
        "Center name": ["Markaz nomi", "Название центра", "Center name"],
        "Director name": ["Direktor ismi", "Имя директора", "Director name"],
        "Currency": ["Valyuta", "Валюта", "Currency"],
        "Logo": ["Logotip", "Логотип", "Logo"],
        "Current password": ["Joriy parol", "Текущий пароль", "Current password"],
        "Old password": ["Eski parol", "Старый пароль", "Old password"],
        "New password": ["Yangi parol", "Новый пароль", "New password"],
        "Confirm new password": ["Yangi parolni tasdiqlang", "Подтвердите новый пароль", "Confirm new password"],
        "Enter a new password and confirm it — no need to type your current password.": ["Yangi parol kiriting va tasdiqlang — joriy parolni kiritish shart emas.", "Введите новый пароль и подтвердите его — текущий пароль вводить не нужно.", "Enter a new password and confirm it — no need to type your current password."],
        "Update password": ["Parolni yangilash", "Обновить пароль", "Update password"],

        /* ── Settings: foydalanuvchilar ── */
        "Users": ["Foydalanuvchilar", "Пользователи", "Users"],
        "Teachers & students logins": ["O'qituvchi va talaba loginlari", "Логины преподавателей и студентов", "Teachers & students logins"],
        "View every username and password. You can edit or delete any account.": ["Har bir foydalanuvchi nomi va parolini ko'ring. Istalgan akkauntni tahrirlash yoki o'chirish mumkin.", "Просматривайте все логины и пароли. Любую учётную запись можно изменить или удалить.", "View every username and password. You can edit or delete any account."],
        "set a new one": ["yangisini o'rnating", "задайте новый", "set a new one"],
        "Edit login": ["Loginni tahrirlash", "Изменить логин", "Edit login"],
        "Delete login": ["Loginni o'chirish", "Удалить логин", "Delete login"],
        "(leave blank to keep current)": ["(o'zgartirmaslik uchun bo'sh qoldiring)", "(оставьте пустым, чтобы не менять)", "(leave blank to keep current)"],
        "Account active (can log in)": ["Akkaunt faol (tizimga kira oladi)", "Учётная запись активна (может входить)", "Account active (can log in)"],
        "Are you sure you want to delete": ["Rostdan ham o'chirmoqchimisiz", "Вы уверены, что хотите удалить", "Are you sure you want to delete"],
        "This permanently removes the user and all linked data. This cannot be undone.": ["Bu foydalanuvchini va unga bog'liq barcha ma'lumotlarni butunlay o'chiradi. Buni qaytarib bo'lmaydi.", "Это навсегда удалит пользователя и все связанные данные. Действие необратимо.", "This permanently removes the user and all linked data. This cannot be undone."],
        "Inactive": ["Nofaol", "Неактивный", "Inactive"],

        /* ── Payments ── */
        "Yearly income": ["Yillik daromad", "Годовой доход", "Yearly income"],
        "This month's income": ["Joriy oy daromadi", "Доход за этот месяц", "This month's income"],
        "Total discounts": ["Jami chegirmalar", "Всего скидок", "Total discounts"],
        "Name, course, receipt №...": ["Ism, kurs, chek №...", "Имя, курс, чек №...", "Name, course, receipt №..."],
        "Month": ["Oy", "Месяц", "Month"],
        "Year": ["Yil", "Год", "Year"],
        "All courses": ["Barcha kurslar", "Все курсы", "All courses"],
        "payments found": ["ta to'lov topildi", "платежей найдено", "payments found"],
        "New payment": ["Yangi to'lov", "Новый платёж", "New payment"],
        "Receipt №": ["Chek №", "Чек №", "Receipt №"],
        "Month / Year": ["Oy / Yil", "Месяц / Год", "Month / Year"],
        "discount": ["chegirma", "скидка", "discount"],
        "No payments found": ["To'lovlar topilmadi", "Платежи не найдены", "No payments found"],
        "Change the filters or add a new payment": ["Filtrlarni o'zgartiring yoki yangi to'lov qo'shing", "Измените фильтры или добавьте новый платёж", "Change the filters or add a new payment"],
        "Monthly income": ["Oylik daromad", "Месячный доход", "Monthly income"],
        "💳 New payment": ["💳 Yangi to'lov", "💳 Новый платёж", "💳 New payment"],
        "👤 Student &amp; course": ["👤 Talaba va kurs", "👤 Студент и курс", "👤 Student & course"],
        "👤 Student & course": ["👤 Talaba va kurs", "👤 Студент и курс", "👤 Student & course"],
        "👤 Student &amp; course details": ["👤 Talaba va kurs ma'lumotlari", "👤 Данные студента и курса", "👤 Student & course details"],
        "👤 Student & course details": ["👤 Talaba va kurs ma'lumotlari", "👤 Данные студента и курса", "👤 Student & course details"],
        "— Select student —": ["— Talabani tanlang —", "— Выберите студента —", "— Select student —"],
        "— Select course —": ["— Kursni tanlang —", "— Выберите курс —", "— Select course —"],
        "— Select teacher —": ["— O'qituvchini tanlang —", "— Выберите преподавателя —", "— Select teacher —"],
        "✨ Course price filled automatically": ["✨ Kurs narxi avtomatik to'ldirildi", "✨ Цена курса заполнена автоматически", "✨ Course price filled automatically"],
        "💳 Payment details": ["💳 To'lov tafsilotlari", "💳 Детали платежа", "💳 Payment details"],
        "Payment details": ["To'lov tafsilotlari", "Детали платежа", "Payment details"],
        "Amount (UZS)": ["Summa (UZS)", "Сумма (UZS)", "Amount (UZS)"],
        "Payment method": ["To'lov usuli", "Способ оплаты", "Payment method"],
        "Net total": ["Sof jami", "Итого", "Net total"],
        "Payment amount": ["To'lov summasi", "Сумма платежа", "Payment amount"],
        "✅ Calculated": ["✅ Hisoblandi", "✅ Рассчитано", "✅ Calculated"],
        "Additional info...": ["Qo'shimcha ma'lumot...", "Дополнительная информация...", "Additional info..."],
        "Save & issue receipt": ["Saqlash va chek berish", "Сохранить и выдать чек", "Save & issue receipt"],
        "💾 Save &amp; issue receipt": ["💾 Saqlash va chek berish", "💾 Сохранить и выдать чек", "💾 Save & issue receipt"],
        "💾 Save & issue receipt": ["💾 Saqlash va chek berish", "💾 Сохранить и выдать чек", "💾 Save & issue receipt"],
        "Download PDF": ["PDF yuklab olish", "Скачать PDF", "Download PDF"],
        "Student information": ["Talaba ma'lumotlari", "Информация о студенте", "Student information"],
        "🎓 Student information": ["🎓 Talaba ma'lumotlari", "🎓 Информация о студенте", "🎓 Student information"],
        "📚 Course &amp; teacher": ["📚 Kurs va o'qituvchi", "📚 Курс и преподаватель", "📚 Course & teacher"],
        "📚 Course & teacher": ["📚 Kurs va o'qituvchi", "📚 Курс и преподаватель", "📚 Course & teacher"],
        "Download PDF receipt": ["PDF chekni yuklab olish", "Скачать PDF чек", "Download PDF receipt"],
        "Delete this payment?": ["Bu to'lovni o'chirasizmi?", "Удалить этот платёж?", "Delete this payment?"],
        "Delete payment": ["To'lovni o'chirish", "Удалить платёж", "Delete payment"],
        "Delete confirmation": ["O'chirishni tasdiqlash", "Подтверждение удаления", "Delete confirmation"],
        "Edit payment": ["To'lovni tahrirlash", "Редактировать платёж", "Edit payment"],
        "✏️ Edit payment": ["✏️ To'lovni tahrirlash", "✏️ Редактировать платёж", "✏️ Edit payment"],

        /* ── Salary ── */
        "Teacher salaries": ["O'qituvchilar maoshi", "Зарплаты преподавателей", "Teacher salaries"],
        "Manage salary payments to staff": ["Xodimlarga maosh to'lovlarini boshqaring", "Управляйте выплатами зарплат сотрудникам", "Manage salary payments to staff"],
        "Paid (UZS)": ["To'langan (UZS)", "Оплачено (UZS)", "Paid (UZS)"],
        "Pending (UZS)": ["Kutilmoqda (UZS)", "В ожидании (UZS)", "Pending (UZS)"],
        "Total payments": ["Jami to'lovlar", "Всего платежей", "Total payments"],
        "All years": ["Barcha yillar", "Все годы", "All years"],
        "Period": ["Davr", "Период", "Period"],
        "Paid date": ["To'langan sana", "Дата оплаты", "Paid date"],
        "No salary payments yet": ["Hali maosh to'lovlari yo'q", "Зарплатных выплат пока нет", "No salary payments yet"],
        "New salary payment": ["Yangi maosh to'lovi", "Новая выплата зарплаты", "New salary payment"],
        "Edit salary payment": ["Maosh to'lovini tahrirlash", "Редактировать выплату зарплаты", "Edit salary payment"],
        "Optional note": ["Ixtiyoriy izoh", "Необязательная заметка", "Optional note"],

        /* ── Calendar ── */
        "Yanvar": ["Yanvar", "Январь", "January"],
        "Fevral": ["Fevral", "Февраль", "February"],
        "Mart": ["Mart", "Март", "March"],
        "Aprel": ["Aprel", "Апрель", "April"],
        "May": ["May", "Май", "May"],
        "Iyun": ["Iyun", "Июнь", "June"],
        "Iyul": ["Iyul", "Июль", "July"],
        "Avgust": ["Avgust", "Август", "August"],
        "Sentabr": ["Sentabr", "Сентябрь", "September"],
        "Oktabr": ["Oktabr", "Октябрь", "October"],
        "Noyabr": ["Noyabr", "Ноябрь", "November"],
        "Dekabr": ["Dekabr", "Декабрь", "December"],
        "📋 Ro'yxat": ["📋 Ro'yxat", "📋 Список", "📋 List"],
        "Oylik Statistika": ["Oylik statistika", "Месячная статистика", "Monthly statistics"],
        "Mock Days": ["Mock kunlari", "Mock-дни", "Mock Days"],
        "Mock Results": ["Mock natijalari", "Результаты Mock", "Mock Results"],
        "Bayramlar": ["Bayramlar", "Праздники", "Holidays"],
        "Dam Kunlari": ["Dam kunlari", "Выходные дни", "Study Breaks"],
        "Mock Day natijalarini Telegramda kuzating": ["Mock Day natijalarini Telegramda kuzating", "Следите за результатами Mock Day в Telegram", "Track Mock Day results on Telegram"],
        "✈️ Telegramda ochish": ["✈️ Telegramda ochish", "✈️ Открыть в Telegram", "✈️ Open in Telegram"],
        "Belgilar Izohlanishi": ["Belgilar izohlanishi", "Обозначения", "Legend"],
        "Barcha Tadbirlar": ["Barcha tadbirlar", "Все события", "All events"],
        "Barchasi": ["Barchasi", "Все", "All"],
        "Mock Day": ["Mock Day", "Mock Day", "Mock Day"],
        "Mock Result": ["Mock natija", "Mock-результат", "Mock Result"],
        "Holiday": ["Bayram", "Праздник", "Holiday"],
        "Study Break": ["Dam kuni", "Учебный перерыв", "Study Break"],
        "No events": ["Tadbirlar yo'q", "Нет событий", "No events"],
        "There are no events or marks on this day.": ["Bu kunda tadbir yoki belgi yo'q.", "В этот день нет событий или отметок.", "There are no events or marks on this day."],
        "No events of the selected type this month.": ["Bu oyda tanlangan turdagi tadbirlar yo'q.", "В этом месяце нет событий выбранного типа.", "No events of the selected type this month."],

        /* ── Login / Auth ── */
        "Education CRM": ["Ta'lim CRM", "Образовательная CRM", "Education CRM"],
        "Welcome back": ["Xush kelibsiz", "С возвращением", "Welcome back"],
        "Manage your education center, teacher monitoring, student tracking and payments through one professional CRM.":
            ["O'quv markazingiz, o'qituvchilar monitoringi, talabalar va to'lovlarni yagona professional CRM orqali boshqaring.",
             "Управляйте учебным центром, мониторингом преподавателей, студентами и платежами через единую профессиональную CRM.",
             "Manage your education center, teacher monitoring, student tracking and payments through one professional CRM."],
        "Admin Panel": ["Admin panel", "Панель админа", "Admin Panel"],
        "Teacher Calendar": ["O'qituvchi kalendari", "Календарь преподавателя", "Teacher Calendar"],
        "Secure Login": ["Xavfsiz kirish", "Безопасный вход", "Secure Login"],
        "Sign in": ["Kirish", "Войти", "Sign in"],
        "Sign in with your username or Gmail address and password.": ["Foydalanuvchi nomi yoki Gmail manzili va parol bilan kiring.", "Войдите с помощью имени пользователя или Gmail и пароля.", "Sign in with your username or Gmail address and password."],
        "Username or Gmail": ["Foydalanuvchi nomi yoki Gmail", "Имя пользователя или Gmail", "Username or Gmail"],
        "Remember me": ["Eslab qolish", "Запомнить меня", "Remember me"],
        "Forgot password?": ["Parolni unutdingizmi?", "Забыли пароль?", "Forgot password?"],
        "Don't have an account?": ["Hisobingiz yo'qmi?", "Нет аккаунта?", "Don't have an account?"],
        "Sign up": ["Ro'yxatdan o'tish", "Зарегистрироваться", "Sign up"],
        "Enter your username or Gmail address. The system automatically detects the method you registered with: if you signed up via Gmail the code is sent to Gmail, if via Telegram it is sent to the Telegram bot.":
            ["Foydalanuvchi nomi yoki Gmail manzilini kiriting. Tizim ro'yxatdan o'tgan usulingizni avtomatik aniqlaydi: Gmail orqali bo'lsa kod Gmailga, Telegram orqali bo'lsa Telegram botga yuboriladi.",
             "Введите имя пользователя или адрес Gmail. Система автоматически определит способ регистрации: если через Gmail — код отправляется на Gmail, если через Telegram — в Telegram-бот.",
             "Enter your username or Gmail address. The system automatically detects the method you registered with: if you signed up via Gmail the code is sent to Gmail, if via Telegram it is sent to the Telegram bot."],
        "Resend code": ["Kodni qayta yuborish", "Отправить код повторно", "Resend code"],
        "Note: the code is sent based on the user's previous verification method.": ["Eslatma: kod foydalanuvchining oldingi tasdiqlash usuliga ko'ra yuboriladi.", "Примечание: код отправляется в соответствии с предыдущим способом подтверждения пользователя.", "Note: the code is sent based on the user's previous verification method."],

        /* ── Register ── */
        "Create a teacher or admin account in the Wall Street CRM. Receive your verification code via Gmail or Telegram.":
            ["Wall Street CRM'da o'qituvchi yoki admin hisob yarating. Tasdiqlash kodini Gmail yoki Telegram orqali oling.",
             "Создайте аккаунт преподавателя или администратора в Wall Street CRM. Получите код подтверждения через Gmail или Telegram.",
             "Create a teacher or admin account in the Wall Street CRM. Receive your verification code via Gmail or Telegram."],
        "Select role": ["Rolni tanlang", "Выберите роль", "Select role"],
        "For attendance and learning": ["Davomat va ta'lim uchun", "Для посещаемости и обучения", "For attendance and learning"],
        "For the full management panel": ["To'liq boshqaruv paneli uchun", "Для полной панели управления", "For the full management panel"],
        "Verification method": ["Tasdiqlash usuli", "Способ подтверждения", "Verification method"],
        "Sign up with Gmail": ["Gmail bilan ro'yxatdan o'tish", "Регистрация через Gmail", "Sign up with Gmail"],
        "A 6-digit code is sent to your email": ["Emailingizga 6 xonali kod yuboriladi", "6-значный код отправляется на email", "A 6-digit code is sent to your email"],
        "Sign up with Telegram": ["Telegram bilan ro'yxatdan o'tish", "Регистрация через Telegram", "Sign up with Telegram"],
        "A 6-digit code is sent via the bot": ["Bot orqali 6 xonali kod yuboriladi", "6-значный код отправляется через бот", "A 6-digit code is sent via the bot"],
        "Personal information": ["Shaxsiy ma'lumotlar", "Личная информация", "Personal information"],
        "Your first name": ["Ismingiz", "Ваше имя", "Your first name"],
        "Your last name": ["Familiyangiz", "Ваша фамилия", "Your last name"],
        "Phone number": ["Telefon raqami", "Номер телефона", "Phone number"],
        "Gmail address": ["Gmail manzili", "Адрес Gmail", "Gmail address"],
        "Telegram Chat ID": ["Telegram Chat ID", "Telegram Chat ID", "Telegram Chat ID"],
        "ID given by the Telegram bot": ["Telegram bot bergan ID", "ID, выданный Telegram-ботом", "ID given by the Telegram bot"],
        "Create password": ["Parol yaratish", "Создать пароль", "Create password"],
        "At least 8 characters": ["Kamida 8 ta belgi", "Минимум 8 символов", "At least 8 characters"],
        "Confirm password": ["Parolni tasdiqlash", "Подтвердите пароль", "Confirm password"],
        "Re-enter the password": ["Parolni qayta kiriting", "Введите пароль ещё раз", "Re-enter the password"],
        "Send code": ["Kod yuborish", "Отправить код", "Send code"],
        "Already have an account?": ["Hisobingiz bormi?", "Уже есть аккаунт?", "Already have an account?"],
        "Confirm code": ["Kodni tasdiqlash", "Подтвердить код", "Confirm code"],
        "Enter the 6-digit code sent via the Telegram bot.": ["Telegram bot orqali yuborilgan 6 xonali kodni kiriting.", "Введите 6-значный код, отправленный через Telegram-бот.", "Enter the 6-digit code sent via the Telegram bot."],
        "Enter the 6-digit code sent to your Gmail address.": ["Gmail manzilingizga yuborilgan 6 xonali kodni kiriting.", "Введите 6-значный код, отправленный на ваш Gmail.", "Enter the 6-digit code sent to your Gmail address."],
        "Verification code": ["Tasdiqlash kodi", "Код подтверждения", "Verification code"],
        "Confirm": ["Tasdiqlash", "Подтвердить", "Confirm"],
        "Resend": ["Qayta yuborish", "Отправить ещё раз", "Resend"],
        "The code is valid for 5 minutes. If it doesn't arrive, check your Gmail spam folder or the Telegram bot.":
            ["Kod 5 daqiqa amal qiladi. Agar kelmasa, Gmail spam papkasini yoki Telegram botni tekshiring.",
             "Код действителен 5 минут. Если он не пришёл, проверьте папку спам в Gmail или Telegram-бот.",
             "The code is valid for 5 minutes. If it doesn't arrive, check your Gmail spam folder or the Telegram bot."],

        /* ── Verify SMS ── */
        "SMS verification": ["SMS tasdiqlash", "SMS-подтверждение", "SMS verification"],
        "Verify": ["Tasdiqlash", "Подтвердить", "Verify"],
        "Resend SMS code": ["SMS kodni qayta yuborish", "Отправить SMS-код повторно", "Resend SMS code"],
        "Back to sign up": ["Ro'yxatga qaytish", "Назад к регистрации", "Back to sign up"],

        /* ── Payment detail extra ── */
        "Method": ["Usul", "Способ", "Method"]
    };

    /* ──────────────────────────────────────────────────────────────────────
       ENGINE
       ────────────────────────────────────────────────────────────────────── */
    var applying = false;

    function getLang() {
        var l = null;
        try { l = localStorage.getItem(STORE_KEY); } catch (e) {}
        return LANGS.indexOf(l) !== -1 ? l : DEFAULT;
    }

    function pick(entry, lang) {
        if (!entry) return null;
        var v = entry[IDX[lang]];
        return (v == null) ? entry[0] : v;
    }

    // matn (trim qilingan) → tarjima yoki null
    function lookup(raw, lang) {
        var trimmed = raw.trim();
        if (!trimmed) return null;
        // ichki bo'sh joylarni (yangi qator, ko'p probel) bitta probelga keltirish
        var norm = trimmed.replace(/\s+/g, ' ');
        if (T[trimmed]) return pick(T[trimmed], lang);
        if (T[norm]) return pick(T[norm], lang);

        // boshi/oxiridagi emoji va belgilarni ajratib, o'rtasini tarjima qilish
        // masalan: "✅ Active", "← Oldingi", "🔍 Filter"
        var m = norm.match(/^([^\p{L}\p{N}]*)([\s\S]*?)([^\p{L}\p{N}]*)$/u);
        if (m && (m[1] || m[3])) {
            var core = m[2].trim();
            if (core && T[core]) {
                return m[1] + pick(T[core], lang) + m[3];
            }
        }
        return null;
    }

    function translateText(node, lang) {
        // tashqaridan o'zgartirilgan bo'lsa, asl qiymatni yangilash
        if (node.__i18nWritten !== undefined && node.nodeValue !== node.__i18nWritten) {
            node.__i18nOrig = undefined;
        }
        var orig = (node.__i18nOrig !== undefined) ? node.__i18nOrig : node.nodeValue;
        if (!orig || !orig.trim()) return;

        var lead = orig.match(/^\s*/)[0];
        var trail = orig.match(/\s*$/)[0];
        var middle = orig.slice(lead.length, orig.length - trail.length);

        var tr = lookup(middle, lang);
        if (tr === null) return;

        node.__i18nOrig = orig;
        var newVal = lead + tr + trail;
        if (node.nodeValue !== newVal) {
            node.__i18nWritten = newVal;
            node.nodeValue = newVal;
        }
    }

    var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1 };

    function shouldSkip(el) {
        while (el) {
            if (el.nodeType === 1) {
                if (SKIP_TAGS[el.tagName]) return true;
                if (el.hasAttribute && el.hasAttribute('data-i18n-skip')) return true;
            }
            el = el.parentNode;
        }
        return false;
    }

    var ATTRS = ['placeholder', 'title', 'aria-label'];

    function translateAttrs(el, lang) {
        if (el.nodeType !== 1) return;
        for (var i = 0; i < ATTRS.length; i++) {
            var a = ATTRS[i];
            if (!el.hasAttribute(a)) continue;
            var key = '__i18nAttr_' + a;
            if (el[key + '_w'] !== undefined && el.getAttribute(a) !== el[key + '_w']) {
                el[key] = undefined;
            }
            var orig = (el[key] !== undefined) ? el[key] : el.getAttribute(a);
            var tr = lookup(orig, lang);
            if (tr === null) continue;
            el[key] = orig;
            if (el.getAttribute(a) !== tr) {
                el[key + '_w'] = tr;
                el.setAttribute(a, tr);
            }
        }
        // submit/button/reset input value
        if (el.tagName === 'INPUT') {
            var ty = (el.type || '').toLowerCase();
            if (ty === 'submit' || ty === 'button' || ty === 'reset') {
                var ov = (el.__i18nVal !== undefined) ? el.__i18nVal : el.value;
                var tv = lookup(ov, lang);
                if (tv !== null) { el.__i18nVal = ov; if (el.value !== tv) el.value = tv; }
            }
        }
    }

    function walk(root, lang) {
        if (!root) return;
        // matn tugunlari
        if (root.nodeType === 3) {
            if (!shouldSkip(root.parentNode)) translateText(root, lang);
            return;
        }
        if (root.nodeType !== 1) return;
        if (root.tagName && SKIP_TAGS[root.tagName]) return;
        if (root.hasAttribute && root.hasAttribute('data-i18n-skip')) return;

        translateAttrs(root, lang);

        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode: function (n) {
                return shouldSkip(n.parentNode) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
            }
        });
        var n;
        var batch = [];
        while ((n = walker.nextNode())) batch.push(n);
        for (var i = 0; i < batch.length; i++) translateText(batch[i], lang);

        // atributli elementlar
        var els = root.querySelectorAll('[placeholder],[title],[aria-label],input');
        for (var j = 0; j < els.length; j++) {
            if (!shouldSkip(els[j])) translateAttrs(els[j], lang);
        }
    }

    function apply(lang) {
        if (LANGS.indexOf(lang) === -1) lang = DEFAULT;
        applying = true;
        document.documentElement.setAttribute('lang', lang);
        if (document.body) walk(document.body, lang);
        // switcher holatini yangilash
        var codes = document.querySelectorAll('[data-lang-current]');
        for (var i = 0; i < codes.length; i++) codes[i].textContent = lang.toUpperCase();
        var opts = document.querySelectorAll('.ws-lang-opt');
        for (var k = 0; k < opts.length; k++) {
            opts[k].classList.toggle('active', opts[k].getAttribute('data-lang') === lang);
        }
        applying = false;
    }

    function setLang(lang) {
        try { localStorage.setItem(STORE_KEY, lang); } catch (e) {}
        apply(lang);
        closeMenus();
    }

    /* ── Switcher (til tugmasi) ── */
    function buildSwitcherMarkup(floating) {
        var cls = 'ws-lang' + (floating ? ' ws-lang-floating' : '');
        return '' +
            '<div class="' + cls + '" data-i18n-skip data-ws-lang>' +
            '  <button type="button" class="ws-lang-btn" aria-label="Language" title="Til / Язык / Language">' +
            '    <span class="ws-lang-flag">🌐</span><span class="ws-lang-code" data-lang-current>' + getLang().toUpperCase() + '</span>' +
            '    <span class="ws-lang-caret">▾</span>' +
            '  </button>' +
            '  <div class="ws-lang-menu">' +
            '    <button type="button" class="ws-lang-opt" data-lang="uz">🇺🇿 O\'zbek</button>' +
            '    <button type="button" class="ws-lang-opt" data-lang="ru">🇷🇺 Русский</button>' +
            '    <button type="button" class="ws-lang-opt" data-lang="en">🇬🇧 English</button>' +
            '  </div>' +
            '</div>';
    }

    function injectStyles() {
        if (document.getElementById('ws-lang-style')) return;
        var css = '' +
            '.ws-lang{position:relative;display:inline-block;z-index:50;}' +
            '.ws-lang-floating{position:fixed;top:16px;right:16px;z-index:99999;}' +
            '.ws-lang-btn{display:inline-flex;align-items:center;gap:7px;height:42px;padding:0 12px;' +
            'border-radius:12px;cursor:pointer;font-weight:800;font-size:13px;line-height:1;' +
            'background:var(--surface,rgba(255,255,255,.94));color:var(--text,#0f172a);' +
            'border:1px solid var(--border,rgba(15,23,42,.12));box-shadow:var(--shadow-sm,0 6px 16px rgba(15,23,42,.10));' +
            'transition:transform .2s,box-shadow .2s;}' +
            '.ws-lang-btn:hover{transform:translateY(-2px);box-shadow:0 12px 24px rgba(15,23,42,.16);}' +
            '.ws-lang-flag{font-size:15px;}' +
            '.ws-lang-caret{font-size:10px;opacity:.65;}' +
            '.ws-lang-menu{position:absolute;top:calc(100% + 8px);right:0;min-width:170px;' +
            'background:#ffffff;border:1px solid rgba(15,23,42,.10);border-radius:14px;padding:6px;' +
            'box-shadow:0 18px 44px rgba(15,23,42,.20);opacity:0;transform:translateY(-8px) scale(.98);' +
            'pointer-events:none;transition:opacity .18s,transform .18s;}' +
            '.ws-lang-menu.open{opacity:1;transform:none;pointer-events:auto;}' +
            '.ws-lang-opt{display:flex;align-items:center;gap:9px;width:100%;text-align:left;' +
            'padding:10px 12px;border-radius:10px;cursor:pointer;font-size:13px;font-weight:700;color:#1f2937;' +
            'background:transparent;border:none;transition:background .15s;}' +
            '.ws-lang-opt:hover{background:rgba(14,92,96,.10);}' +
            '.ws-lang-opt.active{background:linear-gradient(135deg,rgba(14,92,96,.16),rgba(14,92,96,.08));color:#0E5C60;}' +
            '@media(max-width:640px){.ws-lang-floating{top:10px;right:10px;}.ws-lang-btn{height:38px;padding:0 10px;}}';
        var st = document.createElement('style');
        st.id = 'ws-lang-style';
        st.textContent = css;
        (document.head || document.documentElement).appendChild(st);
    }

    function ensureSwitcher() {
        injectStyles();
        if (document.querySelector('[data-ws-lang]')) return; // base.html allaqachon qo'shgan
        if (!document.body) return;
        var wrap = document.createElement('div');
        wrap.innerHTML = buildSwitcherMarkup(true);
        document.body.appendChild(wrap.firstElementChild);
    }

    function closeMenus() {
        var menus = document.querySelectorAll('.ws-lang-menu.open');
        for (var i = 0; i < menus.length; i++) menus[i].classList.remove('open');
    }

    // Event delegation — switcher tugmalari
    document.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('.ws-lang-btn') : null;
        if (btn) {
            e.stopPropagation();
            var menu = btn.parentNode.querySelector('.ws-lang-menu');
            var isOpen = menu.classList.contains('open');
            closeMenus();
            if (!isOpen) menu.classList.add('open');
            return;
        }
        var opt = e.target.closest ? e.target.closest('.ws-lang-opt') : null;
        if (opt) {
            e.stopPropagation();
            setLang(opt.getAttribute('data-lang'));
            return;
        }
        closeMenus();
    });

    /* ── MutationObserver — keyin qo'shilgan matnlar uchun ── */
    function startObserver() {
        if (!window.MutationObserver || !document.body) return;
        var obs = new MutationObserver(function (muts) {
            if (applying) return;
            var lang = getLang();
            if (lang === DEFAULT && !hasNonDefault()) { /* baribir tarjima kerak */ }
            applying = true;
            for (var i = 0; i < muts.length; i++) {
                var mu = muts[i];
                if (mu.type === 'characterData') {
                    if (!shouldSkip(mu.target.parentNode)) translateText(mu.target, lang);
                } else if (mu.type === 'childList') {
                    for (var j = 0; j < mu.addedNodes.length; j++) {
                        walk(mu.addedNodes[j], lang);
                    }
                }
            }
            applying = false;
        });
        obs.observe(document.body, {
            childList: true, subtree: true, characterData: true
        });
    }
    function hasNonDefault() { return true; }

    /* ── Init ── */
    function init() {
        ensureSwitcher();
        apply(getLang());
        startObserver();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // tashqi API
    window.WSI18N = {
        setLang: setLang,
        getLang: getLang,
        apply: function () { apply(getLang()); },
        t: function (text) { var r = lookup(String(text), getLang()); return r === null ? text : r; },
        add: function (obj) { for (var k in obj) if (obj.hasOwnProperty(k)) T[k] = obj[k]; }
    };
})();
