from django.urls import path
from . import views

app_name = 'instructors'

# ✅ create/ URL olib tashlandi
# Chunki instructor register orqali avtomatik qo'shiladi
# Admin panelda faqat ko'rish, tahrirlash va o'chirish qoldi

urlpatterns = [
    path('',                 views.instructor_list,   name='instructor_list'),
    path('create/',          views.instructor_create, name='instructor_create'),  # ← shu
    path('<int:pk>/update/', views.instructor_update, name='instructor_update'),
    path('<int:pk>/delete/', views.instructor_delete, name='instructor_delete'),
]