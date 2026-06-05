import io
import base64
import os
from datetime import datetime
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import Payment
from wallstreet.error_notifications import notify_developer

# ── reportlab imports ──────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import (
    HexColor, white, black, Color
)
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import ImageReader

# QR kod uchun (ixtiyoriy — o'rnatilmagan bo'lsa, QR chizilmaydi)
try:
    import qrcode
except Exception:
    qrcode = None


# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY      = HexColor('#0E5C60')
PRIMARY_DARK = HexColor('#093D40')
PRIMARY_LIGHT= HexColor('#1a8a8f')
GOLD         = HexColor('#C9A84C')
GOLD_LIGHT   = HexColor('#e8c97a')
LIGHT_BG     = HexColor('#f0f9f9')
BORDER       = HexColor('#b2d8da')
TEXT_DARK    = HexColor('#0a2426')
TEXT_MID     = HexColor('#2d5a5d')
TEXT_SOFT    = HexColor('#6b9ea1')
SUCCESS      = HexColor('#10b981')
WARNING      = HexColor('#f59e0b')
DANGER       = HexColor('#ef4444')
GREY_LIGHT   = HexColor('#f8fafa')


# ── helpers ────────────────────────────────────────────────────────────────────
def _month_name(n):
    names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
             'July', 'August', 'September', 'October', 'November', 'December']
    return names[n] if 1 <= n <= 12 else str(n)


def _status_color(status):
    return {
        'paid': SUCCESS, 'pending': WARNING,
        'partial': HexColor('#3b82f6'), 'overdue': DANGER,
        'cancelled': HexColor('#6b7280'),
    }.get(status, TEXT_SOFT)


def _status_label(status):
    return {
        'paid': 'PAID', 'pending': 'PENDING',
        'partial': 'PARTIALLY PAID', 'overdue': 'OVERDUE',
        'cancelled': 'CANCELLED',
    }.get(status, status.upper())


# ══════════════════════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def payment_list(request):
    """Main payments list page with stats."""
    qs = Payment.objects.select_related('student', 'course', 'instructor')

    # ── filters ──
    q          = request.GET.get('q', '').strip()
    status_f   = request.GET.get('status', '')
    method_f   = request.GET.get('method', '')
    month_f    = request.GET.get('month', '')
    year_f     = request.GET.get('year', str(timezone.now().year))
    course_f   = request.GET.get('course', '')

    if q:
        qs = qs.filter(
            Q(receipt_number__icontains=q) |
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q) |
            Q(course__title__icontains=q)
        )
    if status_f:
        qs = qs.filter(status=status_f)
    if method_f:
        qs = qs.filter(payment_method=method_f)
    if month_f:
        qs = qs.filter(payment_month=month_f)
    if year_f:
        qs = qs.filter(payment_year=year_f)
    if course_f:
        qs = qs.filter(course_id=course_f)

    # ── stats ──
    all_payments  = Payment.objects.filter(payment_year=year_f) if year_f else Payment.objects.all()
    total_income  = all_payments.filter(status='paid').aggregate(s=Sum('amount'))['s'] or 0
    total_discount= all_payments.aggregate(s=Sum('discount'))['s'] or 0
    pending_count = all_payments.filter(status='pending').count()
    month_income  = all_payments.filter(
        status='paid', payment_month=timezone.now().month
    ).aggregate(s=Sum('amount'))['s'] or 0

    # monthly chart data (current year)
    monthly_data = []
    for m in range(1, 13):
        val = Payment.objects.filter(
            payment_year=timezone.now().year,
            payment_month=m, status='paid'
        ).aggregate(s=Sum('amount'))['s'] or 0
        monthly_data.append({'month': _month_name(m), 'amount': float(val)})

    # ── pagination ──
    paginator = Paginator(qs, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))

    # ── choices for filters ──
    try:
        from courses.models import Course
        courses = Course.objects.filter(is_active=True)
    except Exception:
        courses = []

    years = list(range(timezone.now().year - 3, timezone.now().year + 2))

    # ── data for the "New payment" modal ──
    try:
        from students.models import Student
        from instructors.models import Instructor
        modal_students = Student.objects.filter(is_active=True)
        modal_instructors = Instructor.objects.filter(is_active=True)
    except Exception:
        modal_students = modal_instructors = []

    context = {
        'page_obj': page_obj,
        'total_income': total_income,
        'total_discount': total_discount,
        'pending_count': pending_count,
        'month_income': month_income,
        'monthly_data': monthly_data,
        'courses': courses,
        'years': years,
        'current_year': year_f,
        'payment_statuses': Payment.STATUS_CHOICES,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'months': Payment.MONTH_CHOICES,
        # active filters
        'q': q, 'status_f': status_f, 'method_f': method_f,
        'month_f': month_f, 'year_f': year_f, 'course_f': course_f,
        # modal form data
        'modal_students': modal_students,
        'modal_instructors': modal_instructors,
        'modal_statuses': Payment.STATUS_CHOICES,
        'modal_now_month': timezone.now().month,
        'modal_now_year': timezone.now().year,
        'modal_years': list(range(2023, timezone.now().year + 2)),
    }
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_create(request):
    """Create a new payment."""
    try:
        from students.models import Student
        from courses.models import Course
        from instructors.models import Instructor
        students    = Student.objects.filter(is_active=True)
        courses     = Course.objects.filter(is_active=True)
        instructors = Instructor.objects.filter(is_active=True)
    except Exception:
        students = courses = instructors = []

    if request.method != 'POST':
        # The create form is a modal on the list page.
        return redirect('payments:payment_list')

    if request.method == 'POST':
        try:
            student_id    = request.POST['student']
            course_id     = request.POST['course']
            instructor_id = request.POST.get('instructor') or None
            amount        = Decimal(request.POST['amount'])
            discount      = Decimal(request.POST.get('discount') or 0)
            method        = request.POST['payment_method']
            month         = int(request.POST['payment_month'])
            year          = int(request.POST['payment_year'])
            status        = request.POST.get('status', 'paid')
            note          = request.POST.get('note', '')

            payment = Payment.objects.create(
                student_id    = student_id,
                course_id     = course_id,
                instructor_id = instructor_id,
                amount        = amount,
                discount      = discount,
                payment_method= method,
                payment_month = month,
                payment_year  = year,
                status        = status,
                note          = note,
                paid_at       = timezone.now(),
                created_by    = request.user,
            )
            messages.success(request, f"Payment saved successfully! Receipt: {payment.receipt_number}")
            return redirect('payments:payment_detail', pk=payment.pk)

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            notify_developer("Payment create failed", str(e), request=request, exc=e)

    context = {
        'students': students,
        'courses': courses,
        'instructors': instructors,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'months': Payment.MONTH_CHOICES,
        'statuses': Payment.STATUS_CHOICES,
        'current_month': timezone.now().month,
        'current_year': timezone.now().year,
        'years': list(range(2023, timezone.now().year + 2)),
    }
    return render(request, 'payments/payment_create.html', context)


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('student', 'course', 'instructor', 'created_by'),
        pk=pk
    )
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    try:
        from students.models import Student
        from courses.models import Course
        from instructors.models import Instructor
        students    = Student.objects.filter(is_active=True)
        courses     = Course.objects.filter(is_active=True)
        instructors = Instructor.objects.filter(is_active=True)
    except Exception:
        students = courses = instructors = []

    if request.method == 'POST':
        try:
            payment.student_id     = request.POST['student']
            payment.course_id      = request.POST['course']
            payment.instructor_id  = request.POST.get('instructor') or None
            payment.amount         = Decimal(request.POST['amount'])
            payment.discount       = Decimal(request.POST.get('discount') or 0)
            payment.payment_method = request.POST['payment_method']
            payment.payment_month  = int(request.POST['payment_month'])
            payment.payment_year   = int(request.POST['payment_year'])
            payment.status         = request.POST.get('status', 'paid')
            payment.note           = request.POST.get('note', '')
            payment.save()
            messages.success(request, "Payment updated successfully!")
            return redirect('payments:payment_detail', pk=payment.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
            notify_developer("Payment edit failed", str(e), request=request, exc=e)

    context = {
        'payment': payment,
        'students': students,
        'courses': courses,
        'instructors': instructors,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'months': Payment.MONTH_CHOICES,
        'statuses': Payment.STATUS_CHOICES,
        'years': list(range(2023, timezone.now().year + 2)),
    }
    return render(request, 'payments/payment_edit.html', context)


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        receipt = payment.receipt_number
        payment.delete()
        messages.success(request, f"To'lov #{receipt} o'chirildi.")
        return redirect('payments:payment_list')
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})


# ══════════════════════════════════════════════════════════════════════════════
# PDF RECEIPT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@xframe_options_sameorigin  # PDF ni o'sha domendagi <iframe> (modal) ichida ko'rsatishga ruxsat
def payment_receipt_pdf(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('student', 'course', 'instructor', 'created_by'),
        pk=pk
    )

    buffer = io.BytesIO()
    W, H   = A4  # 595 x 842 pt
    c      = canvas.Canvas(buffer, pagesize=A4)

    # ── 1. Full-page background ──────────────────────────────────────────────
    c.setFillColor(GREY_LIGHT)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── 2. Decorative side bar ───────────────────────────────────────────────
    c.setFillColor(PRIMARY_DARK)
    c.rect(0, 0, 18*mm, H, fill=1, stroke=0)

    # Gold stripe on sidebar
    c.setFillColor(GOLD)
    c.rect(14*mm, 0, 4*mm, H, fill=1, stroke=0)

    # ── 3. Header panel ──────────────────────────────────────────────────────
    # Dark header background
    c.setFillColor(PRIMARY_DARK)
    _rounded_rect(c, 22*mm, H - 52*mm, W - 30*mm, 44*mm, 4*mm, fill=1, stroke=0)

    # Gold top accent line
    c.setFillColor(GOLD)
    _rounded_rect(c, 22*mm, H - 10*mm, W - 30*mm, 4*mm, 2*mm, fill=1, stroke=0)

    # ── Logo in header ───────────────────────────────────────────────────────
    logo_path = _find_logo()
    if logo_path:
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, 28*mm, H - 46*mm, width=28*mm, height=28*mm,
                        mask='auto', preserveAspectRatio=True)
        except Exception:
            _draw_monogram(c, 28*mm + 14*mm, H - 32*mm)
    else:
        _draw_monogram(c, 28*mm + 14*mm, H - 32*mm)

    # Brand name
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(62*mm, H - 28*mm, 'WALL STREET')
    c.setFont('Helvetica', 11)
    c.setFillColor(GOLD_LIGHT)
    c.drawString(62*mm, H - 37*mm, 'Education Centre')

    # "RECEIPT" label (right side of header)
    c.setFillColor(GOLD)
    _rounded_rect(c, W - 58*mm, H - 46*mm + 6*mm, 48*mm, 14*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(PRIMARY_DARK)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(W - 58*mm + 24*mm, H - 46*mm + 11*mm, 'RECEIPT')

    # Receipt number (panel ostida, kulrang fonda)
    c.setFillColor(PRIMARY_DARK)
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(W - 11*mm, H - 59*mm, f'# {payment.receipt_number}')

    # ── Status badge ─────────────────────────────────────────────────────────
    sc = _status_color(payment.status)
    _rounded_rect(c, W - 50*mm, H - 65*mm, 40*mm, 9*mm, 4.5*mm, fill=1, stroke=0,
                  fill_color=sc)
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(W - 50*mm + 20*mm, H - 65*mm + 3*mm,
                        _status_label(payment.status))

    # ── 4. Info grid ─────────────────────────────────────────────────────────
    cy = H - 80*mm
    col1x = 24*mm
    col2x = W / 2 + 4*mm

    group_name = _student_group_name(payment)

    _info_card(c, col1x, cy - 38*mm, (W/2 - col1x - 6*mm), 38*mm, [
        ("Student",  f"{payment.student.first_name} {payment.student.last_name}"),
        ("Phone",    getattr(payment.student, 'phone', '—') or '—'),
        ("Course",   str(payment.course.title)),
    ])

    _info_card(c, col2x, cy - 38*mm, (W - 8*mm - col2x), 38*mm, [
        ("Teacher",  _instructor_name(payment.instructor)),
        ("Group",    group_name),
        ("Month / Year", f"{_month_name(payment.payment_month)} {payment.payment_year}"),
    ])

    # ── 5. Amount box ────────────────────────────────────────────────────────
    ay = cy - 74*mm   # info kartochkalar ostida (ular cy-38mm da tugaydi)
    c.setFillColor(PRIMARY)
    _rounded_rect(c, col1x, ay, W - col1x - 8*mm, 28*mm, 4*mm, fill=1, stroke=0)

    # Label
    c.setFillColor(GOLD_LIGHT)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(col1x + 6*mm, ay + 19*mm, "PAYMENT AMOUNT")

    net = payment.net_amount
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 26)
    c.drawString(col1x + 6*mm, ay + 8*mm, f"{net:,.0f}  UZS")

    if payment.discount > 0:
        c.setFillColor(GOLD_LIGHT)
        c.setFont('Helvetica', 9)
        c.drawRightString(W - 14*mm, ay + 8*mm,
                          f"Discount: -{payment.discount:,.0f} UZS")

    # ── 6. Date & Note ───────────────────────────────────────────────────────
    dy = ay - 18*mm
    c.setFillColor(TEXT_MID)
    c.setFont('Helvetica', 9)
    paid_str = payment.paid_at.strftime('%d.%m.%Y %H:%M') if payment.paid_at else '—'
    c.drawString(col1x, dy, f"Payment date: {paid_str}")
    if payment.note:
        c.setFont('Helvetica-Oblique', 9)
        c.setFillColor(TEXT_SOFT)
        c.drawString(col1x, dy - 8*mm, f"Note: {payment.note[:80]}")

    # ── 7. Signature block ───────────────────────────────────────────────────
    sy = 52*mm
    # divider line above the signature area
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(col1x, sy + 20*mm, W - 8*mm, sy + 20*mm)

    # ── 7a. QR code (chap tomonda) ────────────────────────────────────────────
    qr_size = 30*mm
    qr_img = _build_receipt_qr(payment, request)
    if qr_img is not None:
        c.drawImage(qr_img, col1x, sy - 4*mm, width=qr_size, height=qr_size,
                    mask='auto', preserveAspectRatio=True)
        c.setFillColor(TEXT_SOFT)
        c.setFont('Helvetica', 7)
        c.drawString(col1x, sy - 7*mm, "Scan to verify receipt")

    # ── 7b. Director signature (o'ng tomonda) ─────────────────────────────────
    sig_x  = W - 82*mm
    sig_lw = 56*mm
    director_name = _get_director_name()

    # Signature line
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(sig_x, sy + 11*mm, sig_x + sig_lw, sy + 11*mm)

    # E-signature decoration (stylised script) — chiziq ustida
    _draw_esignature(c, sig_x + 4*mm, sy + 13*mm, sig_lw - 10*mm, director_name)

    # Director name + title
    c.setFillColor(PRIMARY_DARK)
    c.setFont('Helvetica-Bold', 9.5)
    c.drawCentredString(sig_x + sig_lw / 2, sy + 5*mm, director_name)

    c.setFillColor(TEXT_SOFT)
    c.setFont('Helvetica', 8)
    c.drawCentredString(sig_x + sig_lw / 2, sy + 0.5*mm, "Director  •  Wall Street Education Centre")

    # ── 7c. Round stamp / seal (pechat) — imzo chizig'i ustida, o'ng chetda ────
    _draw_stamp(c, sig_x + sig_lw + 1*mm, sy + 16*mm, 14.5*mm)

    # ── 8. Footer strip ──────────────────────────────────────────────────────
    c.setFillColor(PRIMARY_DARK)
    c.rect(0, 0, W, 18*mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, 17*mm, W, 1*mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont('Helvetica', 8)
    c.drawCentredString(W/2, 7*mm,
        'Wall Street Education Centre  •  Tashkent, Uzbekistan  •  www.wallstreet.uz')
    c.setFillColor(GOLD_LIGHT)
    c.setFont('Helvetica-Bold', 7)
    c.drawRightString(W - 8*mm, 7*mm, f"Printed: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    # ── Watermark diagonal text ───────────────────────────────────────────────
    c.saveState()
    c.setFillColor(Color(0.055, 0.361, 0.376, alpha=0.04))
    c.setFont('Helvetica-Bold', 52)
    c.translate(W/2, H/2)
    c.rotate(35)
    c.drawCentredString(0, 0, 'WALL STREET')
    c.restoreState()

    c.save()
    buffer.seek(0)

    fname = f"receipt_{payment.receipt_number}.pdf"
    # ?inline=1 → brauzerda / modal iframe ichida ochiladi (yuklab olmasdan)
    inline = request.GET.get('inline') in ('1', 'true', 'yes')
    disposition = 'inline' if inline else 'attachment'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'{disposition}; filename="{fname}"'
    return response


# ── Drawing helpers ────────────────────────────────────────────────────────────

def _rounded_rect(c, x, y, w, h, r, fill=0, stroke=1,
                  fill_color=None, stroke_color=None):
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
    path = c.beginPath()
    path.moveTo(x + r, y)
    path.lineTo(x + w - r, y)
    path.arcTo(x + w - 2*r, y, x + w, y + 2*r, -90, 90)
    path.lineTo(x + w, y + h - r)
    path.arcTo(x + w - 2*r, y + h - 2*r, x + w, y + h, 0, 90)
    path.lineTo(x + r, y + h)
    path.arcTo(x, y + h - 2*r, x + 2*r, y + h, 90, 90)
    path.lineTo(x, y + r)
    path.arcTo(x, y, x + 2*r, y + 2*r, 180, 90)
    path.close()
    c.drawPath(path, fill=fill, stroke=stroke)


def _info_card(c, x, y, w, h, items):
    """Draw a light card with key-value pairs."""
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.6)
    _rounded_rect(c, x, y, w, h, 3*mm, fill=1, stroke=1)

    row_h = h / len(items)
    for i, (label, value) in enumerate(items):
        ry = y + h - (i + 1) * row_h + row_h * 0.25

        # Label
        c.setFillColor(TEXT_SOFT)
        c.setFont('Helvetica', 7.5)
        c.drawString(x + 5*mm, ry + row_h * 0.45, label.upper())

        # Value
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 9.5)
        c.drawString(x + 5*mm, ry, str(value)[:38])

        # Divider
        if i < len(items) - 1:
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.3)
            c.line(x + 3*mm, ry - 1.5*mm, x + w - 3*mm, ry - 1.5*mm)


def _draw_monogram(c, cx, cy):
    """Draw a stylised WS monogram when no logo is found."""
    c.setFillColor(GOLD)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(cx, cy - 8, 'WS')


def _draw_esignature(c, x, y, width, name):
    """
    Realistik qo'lda yozilgandek elektron imzo chizadi.

    Bir nechta bezier "qalam zarbalari", bosim o'zgarishi (turli chiziq
    qalinligi), boshlang'ich bosh harf sirtmog'i va tagidagi naqshli
    chiziqdan iborat — haqiqiy ruchka bilan qo'yilgan imzoga o'xshaydi.
    """
    import math

    INK = HexColor('#15366b')  # to'q ko'k siyoh rangi (real ruchka)
    c.saveState()
    c.setStrokeColor(INK)
    c.setLineCap(1)   # round
    c.setLineJoin(1)  # round
    sc = width / 100.0   # masshtab koeffitsienti

    def stroke(points, lw):
        """Nuqtalar ketma-ketligini silliq egri chiziq sifatida chizadi."""
        c.setLineWidth(lw)
        p = c.beginPath()
        p.moveTo(x + points[0][0] * sc, y + points[0][1])
        for i in range(1, len(points) - 2, 1):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            # Catmull-Rom -> bezier control points (silliq)
            c1x = x0 + (x1 - x0) * 0.5
            c2x = x1 - (x2 - x1) * 0.0
            p.curveTo(x + (x0 + (x1 - x0) * 0.6) * sc, y + y0 + (y1 - y0) * 0.4,
                      x + (x1 - (x2 - x1) * 0.2) * sc, y + y1,
                      x + x1 * sc, y + y1)
        # oxirgi nuqta
        lx, ly = points[-1]
        p.lineTo(x + lx * sc, y + ly)
        c.drawPath(p, stroke=1, fill=0)

    # 1) Boshlang'ich katta sirtmoq (bosh harf) — qalin zarba
    c.setLineWidth(2.2)
    p = c.beginPath()
    p.moveTo(x + 2 * sc, y - 2)
    p.curveTo(x + 0 * sc,  y + 16, x + 14 * sc, y + 20, x + 16 * sc, y + 4)
    p.curveTo(x + 18 * sc, y - 10, x + 6 * sc,  y - 8,  x + 10 * sc, y + 6)
    p.curveTo(x + 13 * sc, y + 16, x + 22 * sc, y + 12, x + 26 * sc, y + 2)
    c.drawPath(p, stroke=1, fill=0)

    # 2) Asosiy oqim — o'rta qalinlik, to'lqinli yozuv
    c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(x + 24 * sc, y + 2)
    p.curveTo(x + 32 * sc, y + 14, x + 40 * sc, y - 8, x + 48 * sc, y + 5)
    p.curveTo(x + 55 * sc, y + 15, x + 60 * sc, y - 6, x + 67 * sc, y + 3)
    p.curveTo(x + 73 * sc, y + 11, x + 80 * sc, y - 4, x + 88 * sc, y + 6)
    c.drawPath(p, stroke=1, fill=0)

    # 3) Yakuniy naqsh (flourish) — ingichka, uzun dum
    c.setLineWidth(0.9)
    p = c.beginPath()
    p.moveTo(x + 88 * sc, y + 6)
    p.curveTo(x + 95 * sc, y + 12, x + 100 * sc, y + 2, x + 96 * sc, y - 4)
    p.curveTo(x + 92 * sc, y - 9, x + 70 * sc, y - 8, x + 50 * sc, y - 6)
    p.curveTo(x + 35 * sc, y - 5, x + 20 * sc, y - 6, x + 8 * sc, y - 7)
    c.drawPath(p, stroke=1, fill=0)

    # 4) Kichik "i" nuqtasi / aksent
    c.setFillColor(INK)
    c.circle(x + 58 * sc, y + 17, 1.0, fill=1, stroke=0)

    c.restoreState()


def _find_logo():
    """Try several common paths to find the logo image."""
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'wallstreet-logo.png'),
        os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'logo_transparent.png'),
        '/app/static/images/wallstreet-logo.png',
        '/app/static/images/logo_transparent.png',
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            return p
    return None


def _instructor_name(instructor):
    if not instructor:
        return '—'
    name = getattr(instructor, 'full_name', '') or ''
    if not name:
        name = f"{getattr(instructor, 'first_name', '')} {getattr(instructor, 'last_name', '')}".strip()
    return name or '—'


def _get_manager_name(request):
    u = request.user
    full = u.get_full_name() if hasattr(u, 'get_full_name') else ''
    return full or u.username or 'Manager'


def _get_director_name():
    """
    Direktor ismi — sozlamalardan yoki birinchi admin foydalanuvchidan olinadi.
    settings.DIRECTOR_NAME bo'lsa, o'sha ishlatiladi.
    """
    from django.conf import settings as dj_settings
    name = getattr(dj_settings, 'DIRECTOR_NAME', '') or ''
    if name:
        return name
    try:
        from accounts.models import CustomUser
        admin = CustomUser.objects.filter(role='admin').order_by('id').first()
        if admin:
            return admin.get_full_name() or admin.username
    except Exception:
        pass
    return 'Wall Street Director'


def _student_group_name(payment):
    """Talabaning ushbu kursdagi guruh nomini topadi (enrollment orqali)."""
    try:
        from enrollments.models import Enrollment
        en = (
            Enrollment.objects
            .filter(student=payment.student, course=payment.course, group__isnull=False)
            .select_related('group')
            .order_by('-enrolled_at')
            .first()
        )
        if en and en.group:
            return en.group.name
    except Exception:
        pass
    return '—'


def _build_receipt_qr(payment, request):
    """Chek ma'lumotlarini kodlovchi QR rasm (ImageReader) qaytaradi."""
    if qrcode is None:
        return None
    try:
        net = payment.net_amount
        lines = [
            "WALL STREET EDUCATION CENTRE",
            f"Receipt: {payment.receipt_number}",
            f"Student: {payment.student.first_name} {payment.student.last_name}",
            f"Phone: {getattr(payment.student, 'phone', '') or '-'}",
            f"Course: {payment.course.title}",
            f"Amount: {net:,.0f} UZS",
            f"Date: {payment.paid_at.strftime('%d.%m.%Y %H:%M') if payment.paid_at else '-'}",
        ]
        try:
            verify_url = request.build_absolute_uri(
                f"/payments/{payment.pk}/"
            )
            lines.append(f"Verify: {verify_url}")
        except Exception:
            pass

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10, border=2,
        )
        qr.add_data("\n".join(lines))
        qr.make(fit=True)
        img = qr.make_image(fill_color="#093D40", back_color="white").convert('RGB')

        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        return ImageReader(bio)
    except Exception:
        return None


def _draw_stamp(c, cx, cy, r):
    """
    Haqiqiy rezina pechatga o'xshash dumaloq rasmiy muhr (seal) chizadi.

    - tashqi qalin + ichki ingichka halqalar
    - yuqori yoyda markaz nomi, pastki yoyda shahar/davlat
    - ikkala yoy orasida ★ ajratgichlar
    - markaziy doirada yulduz, "OFFICIAL" va yil
    - biroz qiyshaytirilgan (rotate) + notekis siyoh effekti uchun
      ikki marta, ozgina siljish bilan chiziladi — qo'lda bosilgandek
    """
    import math

    INK = Color(0.10, 0.22, 0.50, alpha=0.62)  # to'q ko'k pechat siyohi

    def _render(off_x, off_y, alpha_mul):
        c.saveState()
        ink = Color(0.10, 0.22, 0.50, alpha=0.62 * alpha_mul)
        c.translate(cx + off_x, cy + off_y)
        c.rotate(-8)  # pechat odatda biroz qiyshiq bosiladi
        c.setStrokeColor(ink)
        c.setFillColor(ink)

        # halqalar
        c.setLineWidth(2.1)
        c.circle(0, 0, r, stroke=1, fill=0)
        c.setLineWidth(0.7)
        c.circle(0, 0, r - 1.3*mm, stroke=1, fill=0)
        c.setLineWidth(1.0)
        c.circle(0, 0, r * 0.46, stroke=1, fill=0)

        # markaziy yulduz
        _draw_star(c, 0, r * 0.16, r * 0.16, ink)

        # markaziy matn
        c.setFont('Helvetica-Bold', max(r * 0.085, 4.0))
        c.drawCentredString(0, -r * 0.12, 'OFFICIAL')
        c.setFont('Helvetica-Bold', max(r * 0.07, 3.4))
        c.drawCentredString(0, -r * 0.30, 'EST. 2024')

        # aylanma matnlar (rotate qilingan kontekst ichida)
        rad = r - 2.6*mm
        _draw_circular_text(c, 0, 0, rad, "WALL STREET EDUCATION CENTRE",
                            max(r * 0.085, 4.2), start_deg=158, sweep_deg=-136)
        _draw_circular_text(c, 0, 0, rad, "TASHKENT  •  UZBEKISTAN",
                            max(r * 0.085, 4.2), start_deg=-158, sweep_deg=136, flip=True)

        # yon ★ ajratgichlar
        c.setFont('Helvetica-Bold', max(r * 0.1, 5))
        for ang in (180, 0):
            a = math.radians(ang)
            c.saveState()
            c.translate(rad * math.cos(a), rad * math.sin(a))
            c.drawCentredString(0, -r * 0.05, '★')
            c.restoreState()

        c.restoreState()

    # notekis bosilgan siyoh effekti: ikki qatlam
    _render(0.4, -0.4, 0.55)
    _render(0, 0, 1.0)


def _draw_star(c, cx, cy, R, color):
    """To'ldirilgan besh burchakli yulduz."""
    import math
    c.saveState()
    c.setFillColor(color)
    p = c.beginPath()
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rr = R if i % 2 == 0 else R * 0.42
        px = cx + rr * math.cos(ang)
        py = cy + rr * math.sin(ang)
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _draw_circular_text(c, cx, cy, radius, text, font_size,
                        start_deg, sweep_deg, flip=False):
    """Matnni aylana bo'ylab yozadi (pechat uchun)."""
    import math
    n = len(text)
    if n == 0:
        return
    c.setFont('Helvetica-Bold', font_size)
    step = sweep_deg / max(n - 1, 1)
    for i, ch in enumerate(text):
        ang = start_deg + step * i
        rad = math.radians(ang)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        c.saveState()
        c.translate(x, y)
        if flip:
            c.rotate(ang - 90)
        else:
            c.rotate(ang + 90)
        c.drawCentredString(0, 0, ch)
        c.restoreState()


# ── AJAX helpers ──────────────────────────────────────────────────────────────

@login_required
def get_course_price(request):
    """Return course price + instructor for AJAX autofill."""
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'price': '', 'instructor': ''})
    try:
        from courses.models import Course
        course = Course.objects.select_related('teacher').get(pk=course_id)
        price  = str(course.price) if hasattr(course, 'price') else ''
        instructor = ''
        instructor_id = ''
        if getattr(course, 'teacher', None):
            instructor = course.teacher.full_name
            instructor_id = course.teacher.id
        return JsonResponse({'price': price, 'instructor': instructor,
                             'instructor_id': instructor_id})
    except Exception:
        return JsonResponse({'price': '', 'instructor': ''})
