# -*- coding: utf-8 -*-
"""Onlayn to'lov provayderlari uchun checkout URL yasovchi yordamchilar.

Payme: base64 kodlangan parametrlar bilan checkout sahifasi.
Click: query-parametrli to'lov sahifasi.
"""
import base64
from urllib.parse import urlencode

from django.conf import settings


# Payme kabinetida sozlanadigan "account" maydoni nomi.
# CheckPerformTransaction da Payme shu nom bilan order_id yuboradi.
PAYME_ACCOUNT_FIELD = 'order_id'


def payme_checkout_url(payment, return_url=''):
    """Payme checkout URL — to'lovni brauzer/ilovada ochish uchun.

    amount — tiyinda (so'm * 100).
    """
    merchant_id = settings.PAYME_MERCHANT_ID
    amount_tiyin = int(round(float(payment.net_amount) * 100))
    parts = [
        f"m={merchant_id}",
        f"ac.{PAYME_ACCOUNT_FIELD}={payment.id}",
        f"a={amount_tiyin}",
    ]
    if return_url:
        parts.append(f"c={return_url}")
    raw = ";".join(parts)
    encoded = base64.b64encode(raw.encode()).decode()
    base = settings.PAYME_CHECKOUT_URL.rstrip('/')
    return f"{base}/{encoded}"


def click_checkout_url(payment, return_url=''):
    """Click to'lov sahifasi URL."""
    params = {
        'service_id': settings.CLICK_SERVICE_ID,
        'merchant_id': settings.CLICK_MERCHANT_ID,
        'amount': float(payment.net_amount),
        'transaction_param': payment.id,
    }
    if return_url:
        params['return_url'] = return_url
    base = settings.CLICK_CHECKOUT_URL
    return f"{base}?{urlencode(params)}"


def available_providers():
    """Sozlangan (kaliti bor) provayderlar ro'yxati."""
    out = []
    if settings.PAYME_MERCHANT_ID:
        out.append('payme')
    if settings.CLICK_SERVICE_ID:
        out.append('click')
    return out
