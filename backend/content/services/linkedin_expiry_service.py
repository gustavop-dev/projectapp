"""
Daily check that warns staff by email when the LinkedIn access token is
about to expire (<=7 days). LinkedIn issues no refresh tokens to non-MDP
apps, so the operator must reconnect manually every ~60 days; this makes
that proactive instead of discovering it via a failed publish.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

WARN_THRESHOLD_DAYS = 7
_CACHE_TIMEOUT = 60 * 60 * 24 * 10  # 10 days — outlives the warning window


def check_linkedin_token_expiry() -> str:
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    if not token.access_token_encrypted or not token.expires_at:
        return 'not_connected'

    remaining = token.expires_at - timezone.now()
    if remaining.days >= WARN_THRESHOLD_DAYS:
        return 'ok'

    cache_key = f'linkedin_expiry_warned:{token.expires_at.date().isoformat()}'
    if cache.get(cache_key):
        return 'already_warned'
    cache.set(cache_key, True, timeout=_CACHE_TIMEOUT)

    recipients = list(
        get_user_model().objects.filter(is_staff=True, is_active=True)
        .exclude(email='').values_list('email', flat=True)
    )
    if not recipients:
        logger.warning('LinkedIn token expiry warning due but no staff recipients.')
        return 'warned'

    expiry_str = timezone.localtime(token.expires_at).strftime('%d/%m/%Y')
    body = (
        f'La conexión con LinkedIn expira el {expiry_str}.\n\n'
        'Para renovarla entra a /panel/linkedin y usa "Reconectar" '
        '(toma menos de un minuto). Los posts programados después de esa '
        'fecha fallarán si el token no se renueva.'
    )
    email = EmailMultiAlternatives(
        subject='LinkedIn: la conexión expira pronto',
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.send(fail_silently=True)
    logger.info('LinkedIn expiry warning sent to %s', ', '.join(recipients))
    return 'warned'
