"""
Google OAuth ("Google bilan kirish") uchun maxsus allauth adapter.

Nima uchun kerak: Wall Street — ichki xodimlar CRM'i. Google bilan kirgan
foydalanuvchini loyiha modeliga (CustomUser) to'g'ri moslashtirish kerak:
  • role = 'teacher' (foydalanuvchi tanlovi bo'yicha — to'g'ridan-to'g'ri o'qituvchi)
  • is_verified = True (custom login_view'dagi tekshiruvdan o'tishi uchun)
  • verification_method = 'gmail'
  • Instructor profilini yaratish (teacher/admin lar shu yerda ko'rinadi)

Agar Google email allaqachon ro'yxatdan o'tgan xodim emailiga mos kelsa,
allauth uni mavjud hisobga ulaydi (settings: SOCIALACCOUNT_EMAIL_AUTHENTICATION).
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class WallStreetSocialAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Yangi Google foydalanuvchi — o'qituvchi sifatida, tasdiqlangan holatda.
        if not user.role:
            user.role = 'teacher'
        user.verification_method = 'gmail'
        user.is_verified = True
        user.save(update_fields=['role', 'verification_method', 'is_verified'])

        # Teacher/admin uchun Instructor profilini yaratamiz (mavjud bo'lmasa).
        try:
            from instructors.models import Instructor
            if user.role in ('teacher', 'admin'):
                full_name = f"{user.first_name} {user.last_name}".strip() or user.username
                Instructor.objects.get_or_create(
                    user=user,
                    defaults={'full_name': full_name},
                )
        except Exception:
            # Instructor yaratilmasa ham kirish jarayoni buzilmasin.
            pass

        return user
