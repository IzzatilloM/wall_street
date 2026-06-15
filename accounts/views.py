
import json

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

from .sms_utils import (
    generate_sms_code,
    save_sms_code,
    verify_sms_code,
    save_register_data,
    get_register_data,
    delete_register_data,
)
from .telegram_utils import send_telegram_code
from .email_utils import send_gmail_code

try:
    from instructors.models import Instructor
except Exception:
    Instructor = None


CustomUser = get_user_model()


def redirect_by_role(user):
    if user.role == 'admin':
        return redirect('dashboard')
    if user.role == 'teacher':
        return redirect('attendance:attendance_list')
    if user.role == 'student':
        return redirect('student:panel')
    return redirect('login')


def post_login_redirect(request):
    """Google OAuth (yoki Django auth) muvaffaqiyatli kirishidan keyin
    foydalanuvchini roliga qarab to'g'ri sahifaga yo'naltiradi."""
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect_by_role(request.user)


def build_register_context(
    form_data=None,
    show_verify_modal=False,
    verify_identifier='',
    verify_method='',
    selected_role='teacher',
    selected_verification_method='gmail',
):
    if form_data is None:
        form_data = {}

    selected_role = selected_role or 'teacher'
    selected_verification_method = selected_verification_method or 'gmail'

    return {
        'form_data': form_data,
        'show_verify_modal': show_verify_modal,
        'verify_identifier': verify_identifier,
        'verify_method': verify_method,
        'is_teacher_selected': selected_role == 'teacher',
        'is_admin_selected': selected_role == 'admin',
        'is_gmail_selected': selected_verification_method == 'gmail',
        'is_telegram_selected': selected_verification_method == 'telegram',
    }


def get_login_username(username_or_email):
    username_or_email = username_or_email.strip()
    user = CustomUser.objects.filter(username=username_or_email).first()
    if user:
        return user.username
    user = CustomUser.objects.filter(email=username_or_email).first()
    if user:
        return user.username
    return username_or_email


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username_or_email or not password:
            messages.error(request, "Username/Gmail va parolni to'ldiring!")
            return render(request, 'login.html')

        username = get_login_username(username_or_email)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'is_verified') and not user.is_verified:
                messages.error(request, "Hisobingiz hali tasdiqlanmagan!")
                return render(request, 'login.html')

            login(request, user)
            messages.success(request, "Tizimga muvaffaqiyatli kirildi!")
            return redirect_by_role(user)

        messages.error(request, "Username/Gmail yoki parol noto'g'ri!")

    return render(request, 'login.html')


def forgot_password_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('reset_identifier', '').strip()

        if not username_or_email:
            messages.error(request, "Username yoki Gmail kiriting!")
            return render(request, 'login.html', {'show_forgot_modal': True})

        user = (
            CustomUser.objects.filter(username=username_or_email).first()
            or CustomUser.objects.filter(email=username_or_email).first()
        )

        if not user:
            messages.error(request, "Bunday foydalanuvchi topilmadi!")
            return render(request, 'login.html', {'show_forgot_modal': True})

        code = generate_sms_code()
        identifier = user.email if user.verification_method == 'gmail' else user.phone
        save_sms_code(identifier, code)

        if user.verification_method == 'gmail':
            success, msg = send_gmail_code(user.email, code)
        elif user.verification_method == 'telegram':
            success, msg = send_telegram_code(user.telegram_chat_id, code)
        else:
            success = False
            msg = "Tasdiqlash usuli topilmadi!"

        if success:
            request.session['reset_identifier'] = identifier
            request.session['reset_user_id'] = user.id
            messages.success(request, "Parolni tiklash kodi yuborildi!")
            # Kod yuborildi — endi kod + yangi parol kiritish bosqichi ochiladi
            return render(request, 'login.html', {
                'show_reset_modal': True,
                'reset_method': user.verification_method,
            })

        messages.error(request, f"Kod yuborishda xatolik: {msg}")
        return render(request, 'login.html', {'show_forgot_modal': True})

    return redirect('login')


def reset_password_view(request):
    """Forgot-password 2-bosqich: yuborilgan kodni tekshirib yangi parol o'rnatadi."""
    if request.method != 'POST':
        return redirect('login')

    identifier = request.session.get('reset_identifier', '')
    user_id    = request.session.get('reset_user_id')

    if not identifier or not user_id:
        messages.error(request, "Tiklash sessiyasi topilmadi! Qaytadan urinib ko'ring.")
        return render(request, 'login.html', {'show_forgot_modal': True})

    code      = request.POST.get('code', '').strip()
    password  = request.POST.get('new_password', '').strip()
    password2 = request.POST.get('new_password2', '').strip()

    context = {'show_reset_modal': True}

    if not code or not password or not password2:
        messages.error(request, "Kod va yangi parolni to'liq kiriting!")
        return render(request, 'login.html', context)

    if password != password2:
        messages.error(request, "Parollar mos kelmadi!")
        return render(request, 'login.html', context)

    if len(password) < 8:
        messages.error(request, "Parol kamida 8 ta belgidan iborat bo'lishi kerak!")
        return render(request, 'login.html', context)

    is_valid, msg = verify_sms_code(identifier, code)
    if not is_valid:
        messages.error(request, msg)
        return render(request, 'login.html', context)

    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "Foydalanuvchi topilmadi!")
        return render(request, 'login.html', {'show_forgot_modal': True})

    user.set_password(password)
    user.plain_password = password
    user.save(update_fields=['password', 'plain_password'])

    request.session.pop('reset_identifier', None)
    request.session.pop('reset_user_id', None)

    messages.success(request, "Parol muvaffaqiyatli yangilandi! Endi yangi parol bilan kiring.")
    return redirect('login')


def send_register_code(register_data):
    verification_method = register_data.get('verification_method', 'gmail')
    code = generate_sms_code()
    identifier = register_data['identifier']
    save_sms_code(identifier, code)

    if verification_method == 'gmail':
        return send_gmail_code(register_data['email'], code)
    if verification_method == 'telegram':
        return send_telegram_code(register_data['telegram_chat_id'], code)

    return False, "Tasdiqlash usuli noto'g'ri tanlangan!"


def register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    context = build_register_context()

    if request.method == 'POST':
        action = request.POST.get('action', 'register').strip()

        # ── Register action ──────────────────────────────────
        if action == 'register':
            first_name          = request.POST.get('first_name', '').strip()
            last_name           = request.POST.get('last_name', '').strip()
            phone               = request.POST.get('phone', '').strip()
            email               = request.POST.get('email', '').strip().lower()
            username            = request.POST.get('username', '').strip()
            password            = request.POST.get('password', '').strip()
            password2           = request.POST.get('password2', '').strip()
            role                = request.POST.get('role', 'teacher').strip()
            verification_method = request.POST.get('verification_method', 'gmail').strip()
            telegram_chat_id    = request.POST.get('telegram_chat_id', '').strip()

            context = build_register_context(
                form_data=request.POST,
                selected_role=role,
                selected_verification_method=verification_method,
            )

            errors = []

            if not first_name:             errors.append("Ism kiritilishi shart!")
            if not last_name:              errors.append("Familiya kiritilishi shart!")
            if not phone:                  errors.append("Telefon raqam kiritilishi shart!")
            if not username:               errors.append("Username kiritilishi shart!")
            if not password or not password2:
                errors.append("Parol va parolni takrorlash maydoni to'ldirilishi shart!")

            if role not in ['teacher', 'admin']:
                errors.append("Role noto'g'ri tanlangan!")

            if verification_method not in ['gmail', 'telegram']:
                errors.append("Tasdiqlash usuli noto'g'ri tanlangan!")

            if verification_method == 'gmail' and not email:
                errors.append("Gmail orqali tasdiqlash uchun email kiritilishi shart!")

            if verification_method == 'telegram' and not telegram_chat_id:
                errors.append("Telegram orqali tasdiqlash uchun Telegram Chat ID kiritilishi shart!")

            if password and password2 and password != password2:
                errors.append("Parollar mos kelmadi!")

            if password and len(password) < 8:
                errors.append("Parol kamida 8 ta belgidan iborat bo'lishi kerak!")

            if phone and (len(phone) != 9 or not phone.isdigit()):
                errors.append("Telefon raqam 9 ta raqamdan iborat bo'lishi kerak! Masalan: 901234567")

            if username and CustomUser.objects.filter(username=username).exists():
                errors.append("Bu username band! Boshqa username tanlang.")

            if phone and CustomUser.objects.filter(phone=phone).exists():
                errors.append("Bu telefon raqam allaqachon ro'yxatdan o'tgan!")

            if email and CustomUser.objects.filter(email=email).exists():
                errors.append("Bu email allaqachon ro'yxatdan o'tgan!")

            if telegram_chat_id and CustomUser.objects.filter(
                    telegram_chat_id=telegram_chat_id).exists():
                errors.append("Bu Telegram Chat ID allaqachon ishlatilgan!")

            if role == 'admin':
                admin_count     = CustomUser.objects.filter(role='admin').count()
                max_admin_count = getattr(settings, 'MAX_ADMIN_COUNT', 2)
                if admin_count >= max_admin_count:
                    errors.append(
                        f"Faqat {max_admin_count} ta admin bo'lishi mumkin! Limit to'lgan."
                    )

            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'register.html', context)

            identifier = email if verification_method == 'gmail' else phone

            register_data = {
                'identifier':          identifier,
                'first_name':          first_name,
                'last_name':           last_name,
                'phone':               phone,
                'email':               email,
                'username':            username,
                'password':            password,
                'role':                role,
                'verification_method': verification_method,
                'telegram_chat_id':    telegram_chat_id,
            }

            save_register_data(identifier, register_data)
            success, msg = send_register_code(register_data)

            if success:
                messages.success(request, "Tasdiqlash kodi yuborildi!")
                context = build_register_context(
                    form_data=register_data,
                    show_verify_modal=True,
                    verify_identifier=identifier,
                    verify_method=verification_method,
                    selected_role=role,
                    selected_verification_method=verification_method,
                )
                return render(request, 'register.html', context)

            messages.error(request, f"Kod yuborishda xatolik: {msg}")
            return render(request, 'register.html', context)

        # ── Verify action ────────────────────────────────────
        if action == 'verify':
            identifier = request.POST.get('identifier', '').strip()
            code       = request.POST.get('code', '').strip()
            reg_data   = get_register_data(identifier)

            if not reg_data:
                messages.error(request, "Ma'lumotlar muddati tugagan! Qayta ro'yxatdan o'ting.")
                return render(request, 'register.html', build_register_context())

            context = build_register_context(
                form_data=reg_data,
                show_verify_modal=True,
                verify_identifier=identifier,
                verify_method=reg_data.get('verification_method', ''),
                selected_role=reg_data.get('role', 'teacher'),
                selected_verification_method=reg_data.get('verification_method', 'gmail'),
            )

            if not code:
                messages.error(request, "Tasdiqlash kodini kiriting!")
                return render(request, 'register.html', context)

            is_valid, msg = verify_sms_code(identifier, code)

            if not is_valid:
                messages.error(request, msg)
                return render(request, 'register.html', context)

            try:
                user = CustomUser.objects.create_user(
                    username            = reg_data['username'],
                    password            = reg_data['password'],
                    first_name          = reg_data['first_name'],
                    last_name           = reg_data['last_name'],
                    email               = reg_data.get('email', ''),
                    phone               = reg_data['phone'],
                    role                = reg_data['role'],
                    verification_method = reg_data.get('verification_method', 'gmail'),
                    telegram_chat_id    = reg_data.get('telegram_chat_id', ''),
                    is_verified         = True,
                )
                # Ochiq parol nusxasi (sozlamalarda admin uchun ko'rinadi)
                user.plain_password = reg_data['password']
                user.save(update_fields=['plain_password'])

                # ✅ TO'G'RI: Instructor modelidagi mavjud fieldlargina ishlatiladi
                # full_name — Instructor.full_name (CharField)
                # user      — Instructor.user (OneToOneField)
                # Qolgan barcha ma'lumotlar (phone, email, role) CustomUser
                # orqali @property sifatida o'qiladi
                if Instructor and user.role in ['teacher', 'admin']:
                    full_name = f"{user.first_name} {user.last_name}".strip()
                    Instructor.objects.get_or_create(
                        user=user,
                        defaults={'full_name': full_name},
                    )

                delete_register_data(identifier)

                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')

                messages.success(
                    request,
                    f"Xush kelibsiz, {user.get_full_name()}! "
                    f"Ro'yxatdan muvaffaqiyatli o'tdingiz."
                )
                return redirect_by_role(user)

            except Exception as e:
                messages.error(request, f"Foydalanuvchi yaratishda xatolik: {str(e)}")
                return render(request, 'register.html', context)

    return render(request, 'register.html', context)


@csrf_exempt
def resend_sms_view(request):
    if request.method == 'POST':
        try:
            data       = json.loads(request.body)
            identifier = data.get('identifier', '').strip()

            if not identifier:
                return JsonResponse({'success': False, 'error': "Identifier yuborilmadi!"})

            reg_data = get_register_data(identifier)
            if not reg_data:
                return JsonResponse({
                    'success': False,
                    'error': "Ma'lumotlar topilmadi! Qayta ro'yxatdan o'ting."
                })

            success, msg = send_register_code(reg_data)
            if success:
                return JsonResponse({'success': True, 'message': msg})
            return JsonResponse({'success': False, 'error': msg})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': "Noto'g'ri so'rov!"})


def logout_view(request):
    logout(request)
    messages.success(request, "Tizimdan chiqildi!")
    return redirect('login')