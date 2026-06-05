from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Main attendance list view
    path('', views.attendance_list, name='attendance_list'),

    # Mark attendance
    path('mark/', views.mark_attendance, name='mark_attendance'),

    # Update attendance
    path('update/<int:attendance_id>/', views.update_attendance, name='update_attendance'),

    # Delete attendance
    path('delete/<int:attendance_id>/', views.delete_attendance, name='delete_attendance'),

    # Student attendance detail
    path('student/<int:student_id>/', views.student_attendance_detail, name='student_attendance_detail'),

    # Award coins to a student
    path('student/<int:student_id>/coins/', views.award_coins, name='award_coins'),

    # Export attendance
    path('export/', views.export_attendance, name='export_attendance'),
]