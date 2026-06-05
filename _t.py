# -*- coding: utf-8 -*-
p = 'templates/verify_sms.html'
s = open(p, encoding='utf-8').read()
rep = {
 '<h1 class="verify-title">SMS tasdiqlash</h1>': '<h1 class="verify-title">SMS verification</h1>',
 "<span class=\"phone-highlight\">{{ phone }}</span> raqamiga yuborilgan\n                6 xonali tasdiqlash kodini kiriting":
   "Enter the 6-digit verification code sent to\n                <span class=\"phone-highlight\">{{ phone }}</span>",
 '<label class="otp-label">Tasdiqlash kodi</label>': '<label class="otp-label">Verification code</label>',
 "Kodni qayta yuborish mumkin bo‘lishigacha: <span id=\"timer\">60</span> soniya":
   "You can resend the code in: <span id=\"timer\">60</span> seconds",
 '<button type="submit" class="verify-btn">Tasdiqlashni yakunlash</button>': '<button type="submit" class="verify-btn">Verify</button>',
 "                    SMS kodni qayta yuborish": "                    Resend SMS code",
 "← Ro‘yxatdan o‘tish sahifasiga qaytish": "← Back to sign up",
 "<strong>Eslatma:</strong> agar bu telefon raqam oldin ro‘yxatdan o‘tgan bo‘lsa,\n                tizim ro‘yxatdan o‘tish bosqichida\n                <strong>“Bu telefon raqam allaqachon ro‘yxatdan o‘tgan”</strong>\n                degan xabarni chiqaradi.":
   "<strong>Note:</strong> if this phone number is already registered,\n                the system shows\n                <strong>“This phone number is already registered”</strong>\n                during sign up.",
 "resendMessage.textContent = 'Iltimos, 6 xonali kodni to‘liq kiriting.';": "resendMessage.textContent = 'Please enter the full 6-digit code.';",
 "resendMessage.textContent = 'SMS qayta yuborilmoqda...';": "resendMessage.textContent = 'Resending SMS...';",
 'resendMessage.textContent = data.error || "SMS yuborishda xatolik yuz berdi.";': 'resendMessage.textContent = data.error || "An error occurred while sending the SMS.";',
 'resendMessage.textContent = "Server bilan bog‘lanishda xatolik yuz berdi.";': 'resendMessage.textContent = "An error occurred connecting to the server.";',
}
cnt = 0
for a, b in rep.items():
    if a in s:
        cnt += 1
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print("verify applied", cnt, "of", len(rep))
