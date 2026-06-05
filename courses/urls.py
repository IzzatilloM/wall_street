from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('update/<int:pk>/', views.course_update, name='course_update'),
    path('delete/<int:pk>/', views.course_delete, name='course_delete'),
    path('move-student/<int:student_id>/', views.move_student_to_other_course, name='move_student_to_other_course'),
]