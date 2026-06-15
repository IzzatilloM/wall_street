# -*- coding: utf-8 -*-
"""Mobil ilova uchun onlayn to'lov API (Payme / Click).

Oqim:
  1) Talaba ilovada to'lovni boshlaydi  → POST /api/payments/create/
     → Payment(status='pending') + checkout URL(lar) qaytadi.
  2) Talaba Payme/Click sahifasida to'laydi.
  3) Provayder bizning callback'ni chaqiradi (Payme JSON-RPC / Click Prepare-Complete)
     → to'lov tasdiqlanadi: Payment.status='paid' + Enrollment.paid_amount yangilanadi
     → CRM "To'lovlar" bo'limida darhol ko'rinadi.
"""
import base64
import time as _time
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from students.models import Student
from courses.models import Course
from enrollments.models import Enrollment
from .models import Payment, PaymentTransaction
from .gateways import payme_checkout_url, click_checkout_url, available_providers, PAYME_ACCOUNT_FIELD


# ═══════════════════════════════════════════════════════════════════════════
#  1) MOBIL: to'lovni boshlash
# ═══════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payable_courses(request):
    """GET /api/payments/courses/  →  talaba to'lashi mumkin bo'lgan kurslar."""
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return Response({'courses': []})
    out = []
    for e in (Enrollment.objects.filter(student=student)
              .select_related('course').order_by('-enrolled_at')):
        if not e.course:
            continue
        out.append({
            'enrollment_id': e.id,
            'course_id': e.course.id,
            'course_title': e.course.title,
            'net_fee': float(e.net_fee),
            'paid_amount': float(e.paid_amount),
            'remaining': float(e.remaining_amount),
            'payment_status': e.payment_status,
            'payment_percent': e.payment_percent,
        })
    return Response({'courses': out})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    """POST /api/payments/create/  →  pending Payment + checkout URL(lar).

    body: {course_id, amount, month?, year?}
    """
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return Response({'detail': "Student profili topilmadi."}, status=404)

    course_id = request.data.get('course_id')
    course = Course.objects.filter(id=course_id).first()
    if not course:
        return Response({'detail': "Kurs topilmadi."}, status=404)

    try:
        amount = Decimal(str(request.data.get('amount')))
    except Exception:
        return Response({'detail': "Summa noto'g'ri."}, status=400)
    if amount <= 0:
        return Response({'detail': "Summa 0 dan katta bo'lishi kerak."}, status=400)

    now = timezone.now()
    month = int(request.data.get('month') or now.month)
    year = int(request.data.get('year') or now.year)

    instructor = course.teacher
    payment = Payment.objects.create(
        student=student,
        course=course,
        instructor=instructor,
        amount=amount,
        payment_method='online',
        payment_month=month,
        payment_year=year,
        status='pending',          # to'langach callback'da 'paid' bo'ladi
        note="Mobil ilova orqali onlayn to'lov",
        created_by=request.user,
    )

    return_url = request.data.get('return_url') or ''
    providers = available_providers()
    urls = {
        'payme': payme_checkout_url(payment, return_url),
        'click': click_checkout_url(payment, return_url),
    }

    return Response({
        'payment_id': payment.id,
        'receipt_number': payment.receipt_number,
        'amount': float(payment.net_amount),
        'available': providers,            # sozlangan (kaliti bor) provayderlar
        'checkout': urls,                  # har ikkala URL (sozlanganini ishlating)
        'configured': bool(providers),
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, pk):
    """GET /api/payments/<id>/status/  →  to'lov holatini tekshirish (polling)."""
    p = Payment.objects.filter(id=pk, student__user=request.user).first()
    if not p:
        return Response({'detail': "To'lov topilmadi."}, status=404)
    return Response({
        'payment_id': p.id,
        'status': p.status,
        'paid': p.status == 'paid',
        'amount': float(p.net_amount),
        'receipt_number': p.receipt_number,
    })


# ═══════════════════════════════════════════════════════════════════════════
#  To'lovni tasdiqlash (umumiy) — Payment → paid + Enrollment yangilash
# ═══════════════════════════════════════════════════════════════════════════
def _apply_paid(payment, provider):
    """To'lov muvaffaqiyatli — Payment 'paid' va Enrollment.paid_amount yangilanadi."""
    if payment.status == 'paid':
        return
    payment.status = 'paid'
    payment.payment_method = 'online'
    payment.paid_at = timezone.now()
    payment.save(update_fields=['status', 'payment_method', 'paid_at', 'updated_at'])

    # Tegishli enrollment'ni topib, to'langan summani oshiramiz
    en = (Enrollment.objects
          .filter(student=payment.student, course=payment.course)
          .order_by('-enrolled_at').first())
    if en:
        en.paid_amount = (en.paid_amount or Decimal('0')) + payment.net_amount
        if en.paid_amount >= en.net_fee:
            en.payment_status = 'paid'
        elif en.paid_amount > 0:
            en.payment_status = 'partial'
        en.save(update_fields=['paid_amount', 'payment_status', 'updated_at'])


def _revert_paid(payment):
    """To'lov bekor qilindi — Payment 'cancelled' va enrollment qaytariladi."""
    was_paid = payment.status == 'paid'
    payment.status = 'cancelled'
    payment.save(update_fields=['status', 'updated_at'])
    if was_paid:
        en = (Enrollment.objects
              .filter(student=payment.student, course=payment.course)
              .order_by('-enrolled_at').first())
        if en:
            en.paid_amount = max((en.paid_amount or Decimal('0')) - payment.net_amount, Decimal('0'))
            en.payment_status = 'paid' if en.paid_amount >= en.net_fee else (
                'partial' if en.paid_amount > 0 else 'unpaid')
            en.save(update_fields=['paid_amount', 'payment_status', 'updated_at'])


# ═══════════════════════════════════════════════════════════════════════════
#  2) PAYME — Merchant API (JSON-RPC) callback
# ═══════════════════════════════════════════════════════════════════════════
# Payme xato kodlari
PE_AUTH = -32504
PE_METHOD = -32601
PE_AMOUNT = -31001
PE_ACCOUNT = -31050          # order_id topilmadi / noto'g'ri
PE_TX_NOT_FOUND = -31003
PE_CANT_PERFORM = -31008
PE_CANT_CANCEL = -31007


def _payme_error(req_id, code, message_ru="", data=None):
    msg = {'ru': message_ru, 'uz': message_ru, 'en': message_ru}
    err = {'code': code, 'message': msg}
    if data is not None:
        err['data'] = data
    return {'jsonrpc': '2.0', 'id': req_id, 'error': err}


def _payme_ok(req_id, result):
    return {'jsonrpc': '2.0', 'id': req_id, 'result': result}


def _payme_authorized(request):
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        _login, _, password = decoded.partition(':')
    except Exception:
        return False
    valid = settings.PAYME_TEST_KEY if settings.PAYME_TEST else settings.PAYME_KEY
    # Ikkala kalitni ham qabul qilamiz (test/prod aralashmasligi uchun)
    return password and password in {settings.PAYME_KEY, settings.PAYME_TEST_KEY, valid}


def _now_ms():
    return int(_time.time() * 1000)


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def payme_callback(request):
    """POST /api/payments/payme/  →  Payme Merchant API (JSON-RPC)."""
    body = request.data if isinstance(request.data, dict) else {}
    req_id = body.get('id')
    method = body.get('method')
    params = body.get('params') or {}

    if not _payme_authorized(request):
        return Response(_payme_error(req_id, PE_AUTH, "Ruxsat yo'q"))

    handler = {
        'CheckPerformTransaction': _payme_check_perform,
        'CreateTransaction': _payme_create,
        'PerformTransaction': _payme_perform,
        'CancelTransaction': _payme_cancel,
        'CheckTransaction': _payme_check,
        'GetStatement': _payme_statement,
    }.get(method)

    if not handler:
        return Response(_payme_error(req_id, PE_METHOD, "Metod topilmadi"))
    return Response(handler(req_id, params))


def _payme_find_payment(params):
    account = params.get('account') or {}
    order_id = account.get(PAYME_ACCOUNT_FIELD) or account.get('order_id')
    if not order_id:
        return None
    try:
        return Payment.objects.filter(id=int(order_id)).first()
    except (TypeError, ValueError):
        return None


def _payme_check_perform(req_id, params):
    payment = _payme_find_payment(params)
    if not payment:
        return _payme_error(req_id, PE_ACCOUNT, "Buyurtma topilmadi",
                            data=PAYME_ACCOUNT_FIELD)
    if payment.status == 'cancelled':
        return _payme_error(req_id, PE_ACCOUNT, "Buyurtma bekor qilingan",
                            data=PAYME_ACCOUNT_FIELD)
    amount_tiyin = int(round(float(payment.net_amount) * 100))
    if int(params.get('amount') or 0) != amount_tiyin:
        return _payme_error(req_id, PE_AMOUNT, "Summa noto'g'ri")
    return _payme_ok(req_id, {'allow': True})


def _payme_create(req_id, params):
    payment = _payme_find_payment(params)
    if not payment:
        return _payme_error(req_id, PE_ACCOUNT, "Buyurtma topilmadi",
                            data=PAYME_ACCOUNT_FIELD)
    amount_tiyin = int(round(float(payment.net_amount) * 100))
    if int(params.get('amount') or 0) != amount_tiyin:
        return _payme_error(req_id, PE_AMOUNT, "Summa noto'g'ri")

    payme_id = params.get('id')
    tx = PaymentTransaction.objects.filter(provider='payme', provider_tx_id=payme_id).first()
    if tx:
        if tx.state != PaymentTransaction.STATE_CREATED:
            return _payme_error(req_id, PE_CANT_PERFORM, "Tranzaksiya holati noto'g'ri")
        return _payme_ok(req_id, {
            'create_time': tx.create_time,
            'transaction': str(tx.id),
            'state': tx.state,
        })

    # Shu buyurtma uchun boshqa faol tranzaksiya bo'lmasligi kerak
    existing = PaymentTransaction.objects.filter(
        payment=payment, provider='payme',
        state=PaymentTransaction.STATE_CREATED,
    ).first()
    if existing:
        return _payme_error(req_id, PE_CANT_PERFORM, "Buyurtma uchun ochiq tranzaksiya mavjud")

    create_time = int(params.get('time') or _now_ms())
    tx = PaymentTransaction.objects.create(
        payment=payment, provider='payme', provider_tx_id=payme_id,
        amount=payment.net_amount, state=PaymentTransaction.STATE_CREATED,
        create_time=create_time,
    )
    return _payme_ok(req_id, {
        'create_time': tx.create_time,
        'transaction': str(tx.id),
        'state': tx.state,
    })


def _payme_perform(req_id, params):
    tx = PaymentTransaction.objects.filter(
        provider='payme', provider_tx_id=params.get('id')).select_related('payment').first()
    if not tx:
        return _payme_error(req_id, PE_TX_NOT_FOUND, "Tranzaksiya topilmadi")

    if tx.state == PaymentTransaction.STATE_COMPLETED:
        return _payme_ok(req_id, {
            'transaction': str(tx.id),
            'perform_time': tx.perform_time,
            'state': tx.state,
        })
    if tx.state != PaymentTransaction.STATE_CREATED:
        return _payme_error(req_id, PE_CANT_PERFORM, "Tranzaksiya holati noto'g'ri")

    with db_transaction.atomic():
        tx.state = PaymentTransaction.STATE_COMPLETED
        tx.perform_time = _now_ms()
        tx.save(update_fields=['state', 'perform_time', 'updated_at'])
        _apply_paid(tx.payment, 'payme')

    return _payme_ok(req_id, {
        'transaction': str(tx.id),
        'perform_time': tx.perform_time,
        'state': tx.state,
    })


def _payme_cancel(req_id, params):
    tx = PaymentTransaction.objects.filter(
        provider='payme', provider_tx_id=params.get('id')).select_related('payment').first()
    if not tx:
        return _payme_error(req_id, PE_TX_NOT_FOUND, "Tranzaksiya topilmadi")

    reason = params.get('reason')
    if tx.state in (PaymentTransaction.STATE_CANCELLED, PaymentTransaction.STATE_CANCELLED_AFTER):
        return _payme_ok(req_id, {
            'transaction': str(tx.id),
            'cancel_time': tx.cancel_time,
            'state': tx.state,
        })

    with db_transaction.atomic():
        if tx.state == PaymentTransaction.STATE_COMPLETED:
            tx.state = PaymentTransaction.STATE_CANCELLED_AFTER
            _revert_paid(tx.payment)
        else:
            tx.state = PaymentTransaction.STATE_CANCELLED
            tx.payment.status = 'cancelled'
            tx.payment.save(update_fields=['status', 'updated_at'])
        tx.cancel_time = _now_ms()
        tx.reason = reason
        tx.save(update_fields=['state', 'cancel_time', 'reason', 'updated_at'])

    return _payme_ok(req_id, {
        'transaction': str(tx.id),
        'cancel_time': tx.cancel_time,
        'state': tx.state,
    })


def _payme_check(req_id, params):
    tx = PaymentTransaction.objects.filter(
        provider='payme', provider_tx_id=params.get('id')).first()
    if not tx:
        return _payme_error(req_id, PE_TX_NOT_FOUND, "Tranzaksiya topilmadi")
    return _payme_ok(req_id, {
        'create_time': tx.create_time,
        'perform_time': tx.perform_time,
        'cancel_time': tx.cancel_time,
        'transaction': str(tx.id),
        'state': tx.state,
        'reason': tx.reason,
    })


def _payme_statement(req_id, params):
    frm = int(params.get('from') or 0)
    to = int(params.get('to') or _now_ms())
    txs = PaymentTransaction.objects.filter(
        provider='payme', create_time__gte=frm, create_time__lte=to)
    return _payme_ok(req_id, {'transactions': [{
        'id': t.provider_tx_id,
        'time': t.create_time,
        'amount': int(round(float(t.amount) * 100)),
        'account': {PAYME_ACCOUNT_FIELD: t.payment_id},
        'create_time': t.create_time,
        'perform_time': t.perform_time,
        'cancel_time': t.cancel_time,
        'transaction': str(t.id),
        'state': t.state,
        'reason': t.reason,
    } for t in txs]})


# ═══════════════════════════════════════════════════════════════════════════
#  3) CLICK — Prepare / Complete callback
# ═══════════════════════════════════════════════════════════════════════════
import hashlib


def _click_signature(data, secret_key, with_merchant_prepare=False):
    """Click imzosi (md5)."""
    parts = [
        str(data.get('click_trans_id', '')),
        str(data.get('service_id', '')),
        secret_key,
        str(data.get('merchant_trans_id', '')),
    ]
    if with_merchant_prepare:
        parts.append(str(data.get('merchant_prepare_id', '')))
    parts += [
        str(data.get('amount', '')),
        str(data.get('action', '')),
        str(data.get('sign_time', '')),
    ]
    return hashlib.md5(''.join(parts).encode()).hexdigest()


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def click_callback(request):
    """POST /api/payments/click/  →  Click Prepare(action=0) / Complete(action=1)."""
    d = request.data
    action = str(d.get('action', ''))

    # Imzo tekshiruvi
    is_complete = action == '1'
    expected = _click_signature(d, settings.CLICK_SECRET_KEY, with_merchant_prepare=is_complete)
    if d.get('sign_string') != expected:
        return Response({'error': -1, 'error_note': 'SIGN CHECK FAILED'})

    payment = Payment.objects.filter(id=d.get('merchant_trans_id')).first()
    if not payment:
        return Response({'error': -5, 'error_note': 'Order not found'})

    amount_ok = abs(float(d.get('amount') or 0) - float(payment.net_amount)) < 0.01
    if not amount_ok:
        return Response({'error': -2, 'error_note': 'Incorrect amount'})

    if action == '0':  # Prepare
        if payment.status == 'cancelled':
            return Response({'error': -9, 'error_note': 'Transaction cancelled'})
        tx, _ = PaymentTransaction.objects.get_or_create(
            payment=payment, provider='click',
            provider_tx_id=str(d.get('click_trans_id', '')),
            defaults={'amount': payment.net_amount, 'state': PaymentTransaction.STATE_CREATED,
                      'create_time': _now_ms()},
        )
        return Response({
            'click_trans_id': d.get('click_trans_id'),
            'merchant_trans_id': d.get('merchant_trans_id'),
            'merchant_prepare_id': tx.id,
            'error': 0, 'error_note': 'Success',
        })

    if action == '1':  # Complete
        tx = PaymentTransaction.objects.filter(
            provider='click', id=d.get('merchant_prepare_id')).select_related('payment').first()
        if not tx:
            return Response({'error': -6, 'error_note': 'Transaction not found'})
        if int(d.get('error', 0)) < 0:
            tx.state = PaymentTransaction.STATE_CANCELLED
            tx.cancel_time = _now_ms()
            tx.save(update_fields=['state', 'cancel_time', 'updated_at'])
            payment.status = 'cancelled'
            payment.save(update_fields=['status', 'updated_at'])
            return Response({'error': -9, 'error_note': 'Payment cancelled'})

        with db_transaction.atomic():
            if tx.state != PaymentTransaction.STATE_COMPLETED:
                tx.state = PaymentTransaction.STATE_COMPLETED
                tx.perform_time = _now_ms()
                tx.save(update_fields=['state', 'perform_time', 'updated_at'])
                _apply_paid(payment, 'click')
        return Response({
            'click_trans_id': d.get('click_trans_id'),
            'merchant_trans_id': d.get('merchant_trans_id'),
            'merchant_confirm_id': tx.id,
            'error': 0, 'error_note': 'Success',
        })

    return Response({'error': -3, 'error_note': 'Action not found'})
