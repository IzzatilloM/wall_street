import random
from django.core.cache import cache
from django.conf import settings


def generate_sms_code():
    return str(random.randint(100000, 999999))


def save_sms_code(identifier, code):
    expire = getattr(settings, 'SMS_CODE_EXPIRE_MINUTES', 5) * 60
    cache_key = f"verification_code_{identifier}"
    cache.set(cache_key, code, timeout=expire)


def verify_sms_code(identifier, code):
    cache_key = f"verification_code_{identifier}"
    saved_code = cache.get(cache_key)

    if not saved_code:
        return False, "Kod muddati tugagan yoki topilmadi!"

    if str(saved_code) != str(code):
        return False, "Kod noto'g'ri!"

    cache.delete(cache_key)
    return True, "Kod tasdiqlandi!"


def save_register_data(identifier, data):
    expire = getattr(settings, 'SMS_CODE_EXPIRE_MINUTES', 5) * 60
    cache_key = f"register_data_{identifier}"
    cache.set(cache_key, data, timeout=expire)


def get_register_data(identifier):
    cache_key = f"register_data_{identifier}"
    return cache.get(cache_key)


def delete_register_data(identifier):
    cache_key = f"register_data_{identifier}"
    cache.delete(cache_key)