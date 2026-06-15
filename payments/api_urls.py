# -*- coding: utf-8 -*-
"""Mobil to'lov API marshrutlari (/api/payments/...)."""
from django.urls import path

from . import api_views

app_name = 'payments_api'

urlpatterns = [
    # Mobil ilova
    path('courses/', api_views.payable_courses, name='payable_courses'),
    path('create/', api_views.create_payment, name='create_payment'),
    path('<int:pk>/status/', api_views.payment_status, name='payment_status'),

    # Provayder callback'lari
    path('payme/', api_views.payme_callback, name='payme_callback'),
    path('click/', api_views.click_callback, name='click_callback'),
]
