"""Impersonation ("Log in as this user") service.

Centralizes the rules and token minting shared by the Django admin button and
the panel DRF endpoint, so both surfaces enforce the exact same policy.
"""
from urllib.parse import urlencode

from django.conf import settings

from accounts.services.tokens import get_tokens_for_user


class ImpersonationError(Exception):
    """Business rule violation while trying to impersonate a user.

    ``status_code`` lets the DRF endpoint return the right HTTP status; the
    Django admin surfaces ``message`` as a flash error regardless.
    """

    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def impersonate(actor, target):
    """Validate the policy and mint JWT tokens for ``target``.

    Rules (mirror of the fleet base implementation):
    - only active superusers may impersonate,
    - cannot impersonate another superuser (self is allowed),
    - cannot impersonate an inactive user,
    - target must have a platform profile, otherwise the resulting session
      would be unusable on ``/platform/``.

    :returns: ``{'access': ..., 'refresh': ...}``
    :raises ImpersonationError: when any rule is violated.
    """
    if not (actor and actor.is_active and actor.is_superuser):
        raise ImpersonationError(
            'Solo los superusuarios activos pueden iniciar sesión como otro usuario.',
            status_code=403,
        )

    if target.is_superuser and target.pk != actor.pk:
        raise ImpersonationError(
            'No puedes iniciar sesión como otro superusuario.',
            status_code=403,
        )

    if not target.is_active:
        raise ImpersonationError('Este usuario está inactivo.', status_code=400)

    if getattr(target, 'profile', None) is None:
        raise ImpersonationError(
            'Este usuario no tiene un perfil de plataforma.',
            status_code=400,
        )

    return get_tokens_for_user(target)


def build_impersonation_redirect_url(tokens, redirect_path='/platform'):
    """Build the absolute frontend callback URL that consumes the tokens.

    The i18n strategy is ``prefix``, so the locale segment is always present.
    """
    base = settings.FRONTEND_BASE_URL.rstrip('/')
    locale = getattr(settings, 'FRONTEND_DEFAULT_LOCALE', 'en-us')
    query = urlencode({
        'access': tokens['access'],
        'refresh': tokens['refresh'],
        'redirect': redirect_path,
    })
    return f'{base}/{locale}/platform/admin-login?{query}'
