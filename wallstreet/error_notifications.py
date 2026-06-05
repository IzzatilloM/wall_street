"""
Centralised developer error notifications.

Whenever something goes wrong anywhere in the system, use ``notify_developer``
to email the configured developer inbox (``settings.DEVELOPER_EMAIL``).

Unhandled request exceptions are already routed to the developer through the
``django.request`` logger configured in ``settings.LOGGING``. This helper is for
*handled* errors (try/except blocks) where we still want a heads-up but don't
want to crash the user's request.
"""

import logging
import traceback

from django.conf import settings
from django.core.mail import mail_admins

logger = logging.getLogger('wallstreet')


def notify_developer(subject, message='', request=None, exc=None):
    """Email the developer about a problem. Never raises.

    Args:
        subject:  short summary line.
        message:  extra context / description.
        request:  optional HttpRequest, adds URL + user info.
        exc:      optional Exception, adds the traceback.
    """
    parts = []
    if message:
        parts.append(str(message))

    if request is not None:
        try:
            user = getattr(request, 'user', None)
            who = getattr(user, 'username', 'anonymous') if user else 'anonymous'
            parts.append(f"\nURL: {request.build_absolute_uri()}")
            parts.append(f"Method: {request.method}")
            parts.append(f"User: {who}")
        except Exception:  # pragma: no cover - defensive
            pass

    if exc is not None:
        parts.append("\nTraceback:\n" + ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ))

    body = '\n'.join(parts) or 'No additional details.'
    full_subject = f"[Wall Street] {subject}"

    try:
        # mail_admins respects settings.ADMINS (the developer) and SERVER_EMAIL.
        mail_admins(full_subject, body, fail_silently=True)
    except Exception:  # pragma: no cover - never break the caller
        pass

    # Also record locally so it shows up in console / logs.
    logger.error("notify_developer: %s\n%s", subject, body)


class DeveloperErrorEmailMiddleware:
    """Emails the developer on any unhandled view exception.

    Django's ``django.request`` logger already mails admins on 500s, but that
    only fires after the response is built. This middleware guarantees a
    notification with request context for *every* uncaught exception, including
    while ``DEBUG=True`` (when the technical 500 page is shown instead).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        notify_developer(
            subject=f"Unhandled error: {type(exception).__name__}",
            message=str(exception),
            request=request,
            exc=exception,
        )
        # Return None so Django continues its normal error handling.
        return None
