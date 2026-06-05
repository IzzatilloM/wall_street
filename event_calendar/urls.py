# urls.py - Calendar App URLs

from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    # Main calendar view
    path('', views.calendar_view, name='calendar'),

    # API endpoints
    path('api/month/<int:year>/<int:month>/', views.calendar_api_month, name='api_month'),

    # Day detail view - AJAX modal
    path('day/<int:year>/<int:month>/<int:day>/', views.calendar_day_details, name='day_details'),

    # Events list
    path('events/', views.calendar_events_list, name='events_list'),

    # Compare months
    path('compare/', views.calendar_month_compare, name='compare'),
]