from django.urls import path
from . import views

urlpatterns = [
    path('', views.salary_list, name='salary_list'),
    path('add/', views.salary_create, name='salary_create'),
    path('export/excel/', views.salary_export_excel, name='salary_export_excel'),
    path('export/pdf/', views.salary_export_pdf, name='salary_export_pdf'),
    path('<uuid:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('<uuid:pk>/delete/', views.salary_delete, name='salary_delete'),
]
