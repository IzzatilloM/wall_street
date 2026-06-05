from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('users/<int:pk>/update/', views.user_update, name='settings_user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='settings_user_delete'),
]
