"""CAPTCHA preserves native auth, redirects and first-login onboarding."""
from requests.exceptions import Timeout
import pytest
from django.contrib.auth import SESSION_KEY
from django.test import Client

from accounts.models import VerificationCode

pytestmark = pytest.mark.django_db


def test_panel_login_creates_staff_session(client, captcha_user, google_response):
    response = client.post('/admin/login/', {
        'username': captcha_user.username, 'password': 'Test-login-password-1',
        'g-recaptcha-response': 'valid-token', 'next': '/es-co/panel/projects',
    })

    assert response.status_code == 302
    assert response.url == '/es-co/panel/projects'
    assert client.session[SESSION_KEY] == str(captcha_user.pk)


@pytest.mark.parametrize('role', ['admin', 'client'])
def test_platform_login_returns_jwt(client, captcha_user, google_response, role):
    captcha_user.profile.role = role
    captcha_user.profile.save()

    response = client.post('/api/accounts/login/', {
        'email': captcha_user.email, 'password': 'Test-login-password-1', 'recaptcha_token': 'valid-token',
    })

    assert response.status_code == 200
    assert response.json()['tokens']['access']
    assert response.json()['user']['role'] == role
    assert SESSION_KEY not in client.session


def test_first_login_requires_captcha_before_sending_otp(client, captcha_user, google_response, mailoutbox):
    captcha_user.profile.is_onboarded = False
    captcha_user.profile.save()
    google_response.side_effect = Timeout()

    response = client.post('/api/accounts/login/', {
        'email': captcha_user.email, 'password': 'Test-login-password-1', 'recaptcha_token': 'valid-token',
    })

    assert response.status_code == 503
    assert not VerificationCode.objects.exists()
    assert not mailoutbox
    assert 'tokens' not in response.json()


def test_verified_first_login_sends_otp(client, captcha_user, google_response, mailoutbox):
    captcha_user.profile.is_onboarded = False
    captcha_user.profile.save()

    response = client.post('/api/accounts/login/', {
        'email': captcha_user.email, 'password': 'Test-login-password-1', 'recaptcha_token': 'valid-token',
    })

    assert response.status_code == 200
    assert response.json()['requires_verification'] is True
    assert len(mailoutbox) == 1
    assert 'tokens' not in response.json()


def test_captcha_does_not_grant_staff_permissions(client, captcha_user, google_response):
    captcha_user.is_staff = False
    captcha_user.save()

    response = client.post('/admin/login/', {
        'username': captcha_user.username, 'password': 'Test-login-password-1',
        'g-recaptcha-response': 'valid-token',
    })

    assert response.status_code == 200
    assert response.context['form'].non_field_errors().as_data()[0].code == 'invalid_login'
    assert SESSION_KEY not in client.session


def test_panel_login_still_requires_csrf(captcha_user, google_response):
    client = Client(enforce_csrf_checks=True)

    response = client.post('/admin/login/', {
        'username': captcha_user.username, 'password': 'Test-login-password-1',
        'g-recaptcha-response': 'valid-token',
    })

    assert response.status_code == 403
    google_response.assert_not_called()


def test_platform_rejects_bad_credentials_after_captcha(client, captcha_user, google_response):
    response = client.post('/api/accounts/login/', {
        'email': captcha_user.email, 'password': 'wrong', 'recaptcha_token': 'valid-token',
    })

    assert response.status_code == 401
    assert 'tokens' not in response.json()


def test_panel_cannot_redirect_to_external_site(client, captcha_user, google_response, settings):
    settings.LOGIN_REDIRECT_URL = '/panel/'
    response = client.post('/admin/login/', {
        'username': captcha_user.username, 'password': 'Test-login-password-1',
        'g-recaptcha-response': 'valid-token', 'next': 'https://attacker.example/',
    })

    assert response.status_code == 302
    assert response.url == '/panel/'
