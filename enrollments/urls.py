from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    path('',                        views.enrollment_list,          name='enrollment_list'),
    path('create/',                 views.enrollment_create,        name='enrollment_create'),
    path('<int:pk>/update/',        views.enrollment_update,        name='enrollment_update'),
    path('<int:pk>/delete/',        views.enrollment_delete,        name='enrollment_delete'),
    path('<int:pk>/toggle-status/', views.enrollment_toggle_status, name='enrollment_toggle_status'),
    path('<int:pk>/note/',          views.enrollment_add_note,      name='enrollment_add_note'),
    path('ai-recommend/<int:student_id>/', views.enrollment_ai_recommend, name='enrollment_ai_recommend'),
]