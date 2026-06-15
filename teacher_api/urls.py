from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.login, name='t_login'),
    path('auth/me/', views.me, name='t_me'),

    # Profil
    path('profile/update/', views.profile_update, name='t_profile_update'),
    path('profile/upload_photo/', views.profile_upload_photo, name='t_profile_photo'),

    # Guruhlar
    path('groups/', views.groups, name='t_groups'),

    # O'quvchilar
    path('students/', views.students, name='t_students'),
    path('students/upload_photo/', views.student_upload_photo, name='t_student_photo'),

    # Davomat
    path('attendance/save/', views.attendance_save, name='t_attendance_save'),
    path('attendance/history/', views.attendance_history, name='t_attendance_history'),

    # Statistika / oylik
    path('stats/summary/', views.stats_summary, name='t_stats_summary'),

    # AI tahlil
    path('ai/analyze/', views.ai_analyze, name='t_ai_analyze'),
]
