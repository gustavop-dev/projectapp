from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from accounts.models import VerificationCode


def create_and_send_otp(user, purpose=VerificationCode.PURPOSE_ONBOARDING):
    """Create a new OTP for the user and send it via email."""
    otp = VerificationCode.create_for_user(user, purpose=purpose)

    subject = 'Tu código de verificación — ProjectApp'
    html_message = render_to_string('emails/verification_code.html', {
        'user': user,
        'code': otp.code,
        'expiry_minutes': VerificationCode.EXPIRY_MINUTES,
    })

    send_mail(
        subject=subject,
        message=f'Tu código de verificación es: {otp.code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return otp


def validate_otp(user, code, purpose=VerificationCode.PURPOSE_ONBOARDING):
    """
    Validate an OTP code for the given user.
    Returns (success: bool, error_message: str | None).
    """
    latest = (
        VerificationCode.objects
        .filter(user=user, purpose=purpose, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not latest:
        return False, 'No hay código de verificación activo. Solicita uno nuevo.'

    if latest.is_expired:
        return False, 'El código ha expirado. Solicita uno nuevo.'

    if latest.attempts >= VerificationCode.MAX_ATTEMPTS:
        return False, 'Demasiados intentos fallidos. Solicita un nuevo código.'

    if latest.code != code:
        latest.increment_attempts()
        remaining = VerificationCode.MAX_ATTEMPTS - latest.attempts
        return False, f'Código incorrecto. Te quedan {remaining} intentos.'

    latest.mark_used()
    return True, None
