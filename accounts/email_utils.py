from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


# Jo'natuvchi nomi (Inbox da chiroyli ko'rinadi, spamga tushish ehtimoli kamayadi)
FROM_NAME = "Wall Street CRM"


def send_gmail_code(email, code):
    subject = f"{code} — Wall Street CRM tasdiqlash kodingiz"

    from_email = formataddr((FROM_NAME, settings.DEFAULT_FROM_EMAIL))

    text_body = (
        "Wall Street CRM\n\n"
        f"Tasdiqlash kodingiz: {code}\n\n"
        "Ushbu kod 5 daqiqa davomida amal qiladi.\n"
        "Agar bu so'rovni siz yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring.\n\n"
        "— Wall Street CRM jamoasi"
    )

    html_body = f"""\
    <div style="font-family:Arial,Helvetica,sans-serif;background:#f4f7f8;padding:30px;">
        <div style="max-width:560px;margin:auto;background:#ffffff;border-radius:18px;padding:28px;border:1px solid #e5e7eb;">
            <h2 style="margin:0 0 10px;color:#0f3d42;">Wall Street CRM</h2>
            <p style="font-size:15px;color:#475569;">Hisobingizni tasdiqlash uchun quyidagi kodni kiriting:</p>
            <div style="font-size:34px;font-weight:800;letter-spacing:8px;color:#0f6f74;background:#f0fbfc;border-radius:16px;padding:18px;text-align:center;margin:22px 0;">
                {code}
            </div>
            <p style="font-size:13px;color:#64748b;">Kod 5 daqiqa davomida amal qiladi.</p>
            <hr style="border:none;border-top:1px solid #e5e7eb;margin:18px 0;">
            <p style="font-size:12px;color:#94a3b8;">Agar bu so'rovni siz yubormagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.</p>
        </div>
    </div>
    """

    # Spamga tushishni kamaytiruvchi sarlavhalar (headers)
    headers = {
        "Reply-To": settings.DEFAULT_FROM_EMAIL,
        "X-Entity-Ref-ID": f"wscrm-{code}",
        "Auto-Submitted": "auto-generated",
        "X-Auto-Response-Suppress": "All",
        "List-Unsubscribe": f"<mailto:{settings.DEFAULT_FROM_EMAIL}?subject=unsubscribe>",
    }

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            headers=headers,
        )
        msg.attach_alternative(html_body, "text/html")
        sent = msg.send(fail_silently=False)

        if sent == 1:
            return True, "Kod Gmail orqali yuborildi!"

        return False, "Email yuborilmadi!"
    except Exception as e:
        return False, str(e)
