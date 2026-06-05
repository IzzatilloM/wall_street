from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.MyTokenObtainPairView.as_view(), name='api_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='api_verify'),

    # Profil
    path('me/', views.ProfileView.as_view(), name='api_me'),
    path('me/courses/', views.MyCoursesView.as_view(), name='api_my_courses'),
    path('me/coins/', views.MyCoinsView.as_view(), name='api_my_coins'),
    path('me/payments/', views.MyPaymentsView.as_view(), name='api_my_payments'),
    path('me/payments/summary/', views.payments_summary, name='api_payments_summary'),

    # Yangiliklar
    path('news/', views.NewsListView.as_view(), name='api_news'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='api_news_detail'),
]
