from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('resend-code/', views.resend_sms_view, name='resend_code'),
    path('post-login/', views.post_login_redirect, name='post_login_redirect'),
    path('logout/', views.logout_view, name='logout'),
]