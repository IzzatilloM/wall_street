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

# Media (yuklangan rasmlar) — production'da ham xizmat qiladi, chunki mobil
# ilova o'qituvchi/o'quvchi rasmlarini ko'rsatadi. (Render free diski vaqtinchalik
# bo'lgani uchun doimiy saqlash kerak bo'lsa, bulutli storage ulang.)
from django.views.static import serve as _media_serve  # noqa: E402
from django.urls import re_path  # noqa: E402

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', _media_serve, {'document_root': settings.MEDIA_ROOT}),
]