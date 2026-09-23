"""Shared, fail-closed reCAPTCHA boundary for session and JWT logins."""

import logging
import re

import requests
from django.conf import settings
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)
VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
TOKEN_MAX_LENGTH = 4096


class CaptchaError(Exception):
    def __init__(self, code, message, status=400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def captcha_enabled():
    # Missing keys must never turn protection off. Only explicit local/test
    # configuration can disable it; settings_prod also pins it on.
    return settings.RECAPTCHA_ENABLED or settings.IS_PRODUCTION


def captcha_configuration_errors():
    errors = []
    if not settings.RECAPTCHA_SITE_KEY or not settings.RECAPTCHA_SECRET_KEY:
        errors.append('RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY are required.')
    hosts = settings.RECAPTCHA_ALLOWED_HOSTNAMES
    if not hosts or any(
        not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', host) for host in hosts
    ):
        errors.append('RECAPTCHA_ALLOWED_HOSTNAMES requires exact lowercase hostnames, without ports or wildcards.')
    return errors


def _unavailable(reason):
    # Do not include the exception, payload or response: they may hold secrets.
    logger.warning('CAPTCHA verification unavailable: %s', reason)
    return CaptchaError(
        'captcha_unavailable',
        _('No pudimos verificar el captcha. Reintenta en unos momentos.'),
        status=503,
    )


def verify_captcha(token):
    """Validate once per attempt, before any authentication side effects."""
    if not captcha_enabled():
        return
    if captcha_configuration_errors():
        raise _unavailable('configuration')
    if not isinstance(token, str) or not token.strip():
        raise CaptchaError('captcha_required', _('Completa el captcha para continuar.'))
    if len(token) > TOKEN_MAX_LENGTH:
        raise CaptchaError('captcha_invalid', _('Verificación de captcha fallida. Intenta de nuevo.'))

    try:
        response = requests.post(
            VERIFY_URL,
            data={'secret': settings.RECAPTCHA_SECRET_KEY, 'response': token},
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        raise _unavailable('provider_response') from None

    if not isinstance(result, dict) or not isinstance(result.get('success'), bool):
        raise _unavailable('malformed_response')
    errors = result.get('error-codes', [])
    if not isinstance(errors, list):
        raise _unavailable('malformed_error_codes')
    if any(code in errors for code in ('missing-input-secret', 'invalid-input-secret', 'bad-request')):
        raise _unavailable('provider_configuration')
    if result['success'] is not True or result.get('hostname') not in settings.RECAPTCHA_ALLOWED_HOSTNAMES:
        raise CaptchaError('captcha_invalid', _('Verificación de captcha fallida. Intenta de nuevo.'))
