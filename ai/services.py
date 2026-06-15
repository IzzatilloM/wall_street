"""
AI service qatlami — Google Gemini (asosiy) yoki Anthropic Claude.

Barcha AI funksiyalar (churn bashorati, o'qituvchi hisoboti, kurs tavsiyasi)
shu yerdagi ask_ai() (eski nomi ask_claude) orqali chaqiriladi.

Provayder tanlash:
  - GEMINI_API_KEY sozlangan bo'lsa  → Gemini
  - aks holda ANTHROPIC_API_KEY bo'lsa → Claude
  - ikkalasi ham yo'q/ishlamasa       → chaqiruvchi funksiya lokal (offline)
                                         tahlilga tushadi

Har bir chaqiruv natijasi AILog ga yoziladi.
"""

import json
import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger('wallstreet')

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class AIServiceError(Exception):
    """AI service sozlanmagani yoki API xatosi."""


def _active_provider():
    """Qaysi provayder faol: 'gemini' | 'claude' | None."""
    if getattr(settings, 'GEMINI_API_KEY', ''):
        return 'gemini'
    if getattr(settings, 'ANTHROPIC_API_KEY', ''):
        return 'claude'
    return None


def _call_gemini(model, system_prompt, user_prompt, max_tokens):
    """
    Gemini generateContent REST chaqiruvi.

    Returns: (text, input_tokens, output_tokens)
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.4,
            # 2.5-flash da "thinking" ni o'chiramiz — aks holda thinking butun
            # token limitini yeb, javob bo'sh qaytishi mumkin. Bizning vazifalar
            # (qisqa JSON/matn) uchun thinking shart emas.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    try:
        resp = requests.post(
            GEMINI_ENDPOINT.format(model=model),
            params={"key": api_key},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise AIServiceError(f"Gemini bilan bog'lanishda xatolik: {exc}") from exc

    if resp.status_code != 200:
        try:
            err = resp.json().get('error', {}).get('message', resp.text)
        except ValueError:
            err = resp.text[:300]
        raise AIServiceError(f"Gemini API xatosi ({resp.status_code}): {err}")

    data = resp.json()

    block = (data.get('promptFeedback') or {}).get('blockReason')
    if block:
        raise AIServiceError(f"Gemini so'rovni bloklladi: {block}")

    text = ''
    candidates = data.get('candidates') or []
    if candidates:
        parts = (candidates[0].get('content') or {}).get('parts') or []
        text = "".join(p.get('text', '') for p in parts).strip()

    if not text:
        raise AIServiceError("Gemini bo'sh javob qaytardi.")

    usage = data.get('usageMetadata') or {}
    return text, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)


def _call_anthropic(model, system_prompt, user_prompt, max_tokens):
    """Anthropic Claude chaqiruvi. Returns: (text, input_tokens, output_tokens)"""
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise AIServiceError(
            "'anthropic' paketi o'rnatilmagan. O'rnating: pip install anthropic"
        ) from exc

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise AIServiceError("ANTHROPIC_API_KEY topilmadi.")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    return text, response.usage.input_tokens, response.usage.output_tokens


def ask_ai(feature, system_prompt, user_prompt,
           related_object='', max_tokens=1024, user=None):
    """
    Faol AI provayderga (Gemini yoki Claude) so'rov yuboradi va AILog ga yozadi.

    Returns:
        (success: bool, text: str) — muvaffaqiyatda AI javobi,
        xatolikda foydalanuvchiga ko'rsatsa bo'ladigan xabar.
    """
    from .models import AILog

    provider = _active_provider()
    if provider == 'gemini':
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
    else:
        model_name = getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-6')

    log = AILog(
        feature=feature,
        related_object=related_object,
        model_name=model_name,
        prompt=user_prompt,
        created_by=user if (user is not None and user.is_authenticated) else None,
    )

    try:
        if provider == 'gemini':
            text, in_tok, out_tok = _call_gemini(
                model_name, system_prompt, user_prompt, max_tokens)
        elif provider == 'claude':
            text, in_tok, out_tok = _call_anthropic(
                model_name, system_prompt, user_prompt, max_tokens)
        else:
            raise AIServiceError(
                "AI sozlanmagan! .env ga GEMINI_API_KEY (yoki ANTHROPIC_API_KEY) qo'shing."
            )

        log.response      = text
        log.success       = True
        log.input_tokens  = in_tok
        log.output_tokens = out_tok
        return True, text

    except AIServiceError as exc:
        # Kutilgan xatolik (kalit/kredit/bo'sh javob) — lokal tahlilga tushiladi.
        log.error = str(exc)
        logger.warning("AI service (%s): %s", feature, exc)
        return False, str(exc)

    except Exception as exc:  # kutilmagan xatolar
        log.error = str(exc)
        logger.exception("AI chaqiruvida kutilmagan xatolik (%s)", feature)
        return False, f"AI bilan bog'lanishda xatolik: {exc}"

    finally:
        try:
            log.save()
        except Exception:  # log yozilmasa ham asosiy oqim buzilmasin
            logger.exception("AILog saqlashda xatolik")


# Eski nom bilan moslik — students/instructors/enrollments views shu nomdan
# foydalanadi (`from ai.services import ask_claude`).
ask_claude = ask_ai


def extract_json(text):
    """
    AI javobidan JSON obyektni ajratib oladi.
    Kod bloklari (```json ... ```) yoki oddiy matn ichidagi {...} ni topadi.
    """
    if not text:
        return None

    # ```json ... ``` bloki bo'lsa — ichini olamiz
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else None

    if candidate is None:
        # Birinchi { dan oxirgi } gacha
        start, end = text.find('{'), text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start:end + 1]

    try:
        return json.loads(candidate)
    except (ValueError, TypeError):
        return None
