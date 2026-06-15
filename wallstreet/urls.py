from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from enrollments.telegram_webhook import telegram_webhook

urlpatterns = [
    path('', lambda request: redirect('/accounts/login/')),
    path('admin/', admin.site.urls),

    # Telegram bot webhook (always-on task kerak emas)
    path('tg/webhook/<str:token>/', telegram_webhook),

    # Mobil ilova API (talaba)
    path('api/', include('api.urls')),

    # Onlayn to'lov API (Payme/Click) + mobil
    path('api/payments/', include('payments.api_urls')),

    # O'qituvchi mobil ilovasi API (DRF + JWT)
    path('api/teacher/', include('teacher_api.urls')),

    path('accounts/', include('accounts.urls')),
    # Google OAuth: /accounts/google/login/ va callback. accounts.urls'dan KEYIN
    # turadi — login/register/logout bizning maxsus view'larimizda qoladi.
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('instructors/', include('instructors.urls', namespace='instructors')),
    path('students/', include('students.urls', namespace='student')),
    path('calendar/', include('event_calendar.urls')),
    path('salary/', include('staff_salary.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('settings_app.urls')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('enrollments/', include('enrollments.urls', namespace='enrollments')),  # ← QO'SHILDI
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Media (yuklangan rasmlar) marshruti — storage rejimiga qarab:
from django.urls import re_path  # noqa: E402

if settings.CLOUDINARY_URL:
    # Cloudinary: rasm URL'lari to'g'ridan-to'g'ri bulutga ishora qiladi — lokal
    # marshrut kerak emas.
    pass
elif getattr(settings, 'USE_DB_MEDIA', False):
    # Bazada saqlangan media — /media/<name> bazadan qaytariladi.
    from dbmedia.views import serve_db_file  # noqa: E402
    urlpatterns += [
        re_path(r'^media/(?P<name>.+)$', serve_db_file, name='dbmedia_serve'),
    ]
else:
    # Lokal disk (development) — production'da ham ishlaydi, lekin Render free
    # diski efemeral bo'lgani uchun DB media yoki Cloudinary tavsiya etiladi.
    from django.views.static import serve as _media_serve  # noqa: E402
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', _media_serve, {'document_root': settings.MEDIA_ROOT}),
    ]