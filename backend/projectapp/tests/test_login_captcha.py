"""Both real authentication entry points must reject CAPTCHA failures."""
import json

import pytest
from requests.exceptions import Timeout
from django.contrib.auth import SESSION_KEY

from accounts.models import VerificationCode

pytestmark = pytest.mark.django_db


def test_missing_token_rejects_login(login_surface, google_response):
    response = login_surface.post(token='')

    assert login_surface.error_code(response) == 'captcha_required'
    assert SESSION_KEY not in login_surface.client.session
    google_response.assert_not_called()


@pytest.mark.parametrize('provider_error', ['invalid-input-response', 'timeout-or-duplicate'])
def test_rejected_token_cannot_authenticate(login_surface, google_response, provider_error):
    google_response.return_value._content = json.dumps({
        'success': False, 'error-codes': [provider_error],
    }).encode()

    response = login_surface.post()

    assert login_surface.error_code(response) == 'captcha_invalid'
    assert SESSION_KEY not in login_surface.client.session
    assert not VerificationCode.objects.exists()


def test_wrong_hostname_rejects_login(login_surface, google_response):
    google_response.return_value._content = b'{"success": true, "hostname": "attacker.example"}'

    response = login_surface.post()

    assert login_surface.error_code(response) == 'captcha_invalid'
    assert SESSION_KEY not in login_surface.client.session


def test_timeout_blocks_authentication(login_surface, google_response):
    google_response.side_effect = Timeout('provider did not answer')

    response = login_surface.post()

    assert login_surface.error_code(response) == 'captcha_unavailable'
    assert SESSION_KEY not in login_surface.client.session
    assert not VerificationCode.objects.exists()


@pytest.mark.parametrize('setting', ['RECAPTCHA_SITE_KEY', 'RECAPTCHA_SECRET_KEY', 'RECAPTCHA_ALLOWED_HOSTNAMES'])
def test_incomplete_configuration_blocks_login(login_surface, captcha_settings, google_response, setting):
    setattr(captcha_settings, setting, '')

    response = login_surface.post()

    assert login_surface.error_code(response) == 'captcha_unavailable'
    assert SESSION_KEY not in login_surface.client.session
    google_response.assert_not_called()
