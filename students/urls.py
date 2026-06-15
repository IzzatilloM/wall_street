from django.urls import path
from .views import (
    student_list,
    student_detail,
    student_create,
    student_update,
    student_delete,
    student_toggle_status,
    student_search_ajax,
    student_panel,
    student_churn_risk,
)

app_name = 'students'

urlpatterns = [
    path('', student_list, name='student_list'),
    path('panel/', student_panel, name='panel'),

    path('create/', student_create, name='student_create'),
    path('<int:pk>/', student_detail, name='student_detail'),
    path('<int:pk>/update/', student_update, name='student_update'),
    path('<int:pk>/delete/', student_delete, name='student_delete'),
    path('<int:pk>/toggle-status/', student_toggle_status, name='student_toggle_status'),
    path('<int:pk>/churn-risk/', student_churn_risk, name='student_churn_risk'),
    path('ajax/search/', student_search_ajax, name='student_search_ajax'),
]