"""Tests for the platform password recovery flow."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from django.core import mail

from accounts.models import VerificationCode
from accounts.services.tokens import (
    PASSWORD_RESET_REQUEST_PURPOSE,
    PASSWORD_RESET_VERIFIED_PURPOSE,
    decode_password_reset_token,
    get_decoy_password_reset_request_token,
    get_password_reset_request_token,
    get_password_reset_verified_token,
)
from accounts.services.verification import create_and_send_otp

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def reset_user(db):
    return User.objects.create_user(
        username='reset@example.com',
        email='reset@example.com',
        password='OldPass123!',
    )


def test_request_token_contains_user_id_and_purpose(reset_user):
    raw = get_password_reset_request_token(reset_user)
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_REQUEST_PURPOSE
    assert int(decoded['user_id']) == reset_user.pk


def test_verified_token_contains_user_id_and_purpose(reset_user):
    raw = get_password_reset_verified_token(reset_user)
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_VERIFIED_PURPOSE
    assert int(decoded['user_id']) == reset_user.pk


def test_decoy_token_has_no_user_id_but_correct_purpose():
    raw = get_decoy_password_reset_request_token()
    decoded = AccessToken(raw)
    assert decoded['purpose'] == PASSWORD_RESET_REQUEST_PURPOSE
    assert decoded.payload.get('user_id') is None


def test_decoder_rejects_wrong_purpose(reset_user):
    raw = get_password_reset_request_token(reset_user)
    with pytest.raises(TokenError):
        decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_VERIFIED_PURPOSE)


def test_decoder_returns_payload_when_purpose_matches(reset_user):
    raw = get_password_reset_request_token(reset_user)
    payload = decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_REQUEST_PURPOSE)
    assert int(payload['user_id']) == reset_user.pk


def test_request_token_expires_after_10_minutes(reset_user):
    with freeze_time('2026-05-16 10:00:00'):
        raw = get_password_reset_request_token(reset_user)
    with freeze_time('2026-05-16 10:11:00'):
        with pytest.raises(TokenError):
            decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_REQUEST_PURPOSE)


def test_verified_token_expires_after_5_minutes(reset_user):
    with freeze_time('2026-05-16 10:00:00'):
        raw = get_password_reset_verified_token(reset_user)
    with freeze_time('2026-05-16 10:06:00'):
        with pytest.raises(TokenError):
            decode_password_reset_token(raw, expected_purpose=PASSWORD_RESET_VERIFIED_PURPOSE)


# ==========================================================================
# verification.create_and_send_otp template routing
# ==========================================================================


def test_create_and_send_otp_uses_password_reset_template_for_reset_purpose(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    create_and_send_otp(reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET)
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    body_html = sent.alternatives[0][0] if sent.alternatives else ''
    body_text = sent.body
    assert 'restablec' in body_text.lower() or 'restablec' in body_html.lower()
    assert reset_user.email in sent.to


def test_create_and_send_otp_default_purpose_still_uses_onboarding_template(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    create_and_send_otp(reset_user)  # defaults to PURPOSE_ONBOARDING
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    body_html = sent.alternatives[0][0] if sent.alternatives else ''
    # The onboarding email body should NOT contain password-reset copy.
    assert 'restablecer' not in sent.body.lower()
    assert 'restablecer' not in body_html.lower()


# ==========================================================================
# password_reset service — request/verify/confirm
# ==========================================================================


from accounts.services import password_reset as pr_service  # noqa: E402
from accounts.services.password_reset import (  # noqa: E402
    COOLDOWN_SECONDS,
    PasswordResetError,
    confirm_password_reset,
    request_password_reset,
    verify_reset_code,
)


def test_request_with_existing_email_creates_code_and_sends_email(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    token = request_password_reset(reset_user.email)
    assert token  # non-empty string
    assert len(mail.outbox) == 1
    assert VerificationCode.objects.filter(
        user=reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False,
    ).count() == 1


def test_request_with_nonexistent_email_returns_decoy_token(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    token = request_password_reset('ghost@example.com')
    assert token
    decoded = AccessToken(token)
    assert decoded.payload.get('user_id') is None
    assert len(mail.outbox) == 0


def test_request_cooldown_skips_resend(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_password_reset(reset_user.email)
    request_password_reset(reset_user.email)
    assert len(mail.outbox) == 1
    # Even on the second call we still hand back a valid token.
    second = request_password_reset(reset_user.email)
    assert int(AccessToken(second)['user_id']) == reset_user.pk


def test_request_cooldown_lapsed_resends(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    with freeze_time('2026-05-16 10:00:00'):
        request_password_reset(reset_user.email)
    with freeze_time('2026-05-16 10:01:30'):
        request_password_reset(reset_user.email)
    assert len(mail.outbox) == 2


def test_verify_with_valid_code_returns_verified_token(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    code = VerificationCode.objects.filter(
        user=reset_user, purpose=VerificationCode.PURPOSE_PASSWORD_RESET, is_used=False,
    ).latest('created_at').code
    verified_token = verify_reset_code(request_token, code)
    assert AccessToken(verified_token)['purpose'] == 'password_reset_verified'
    assert int(AccessToken(verified_token)['user_id']) == reset_user.pk


def test_verify_with_wrong_code_decrements_attempts(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(request_token, '000000')
    assert exc.value.code == 'invalid_code'
    assert exc.value.extra.get('attempts_left') == 4


def test_verify_with_wrong_code_5_times_returns_too_many_attempts(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    for _ in range(4):
        with pytest.raises(PasswordResetError):
            verify_reset_code(request_token, '000000')
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(request_token, '000000')
    assert exc.value.code == 'too_many_attempts'


def test_verify_with_expired_code_returns_expiry_error(reset_user, settings):
    """At +11min both the OTP (10-min EXPIRY) and the request token (10-min
    lifetime) have expired. The decoder rejects the token first → service
    raises `invalid_or_expired_token`. If lifetimes ever diverge so the
    request token still validates, the code-level checks would surface
    `code_expired` instead — accept both."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    with freeze_time('2026-05-16 10:00:00'):
        request_token = request_password_reset(reset_user.email)
        real_code = VerificationCode.objects.latest('created_at').code
    with freeze_time('2026-05-16 10:11:00'):
        with pytest.raises(PasswordResetError) as exc:
            verify_reset_code(request_token, real_code)
        assert exc.value.code in {'code_expired', 'invalid_or_expired_token'}


def test_verify_with_decoy_token_returns_invalid_code():
    decoy = get_decoy_password_reset_request_token()
    with pytest.raises(PasswordResetError) as exc:
        verify_reset_code(decoy, '123456')
    assert exc.value.code == 'invalid_code'


def test_confirm_with_valid_token_sets_new_password_and_returns_tokens(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    payload = confirm_password_reset(verified_token, 'NewStrongPass456!')
    reset_user.refresh_from_db()
    assert reset_user.check_password('NewStrongPass456!')
    assert 'access' in payload and 'refresh' in payload


def test_confirm_with_weak_password_returns_validation_errors(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    with pytest.raises(PasswordResetError) as exc:
        confirm_password_reset(verified_token, '12345')
    assert exc.value.code == 'weak_password'
    assert exc.value.extra.get('errors')


def test_confirm_rejects_request_token_used_as_verified(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    request_token = request_password_reset(reset_user.email)
    with pytest.raises(PasswordResetError) as exc:
        confirm_password_reset(request_token, 'NewStrongPass456!')
    assert exc.value.code == 'invalid_or_expired_token'
    assert exc.value.http_status == 401


def test_confirm_sends_confirmation_email_to_user(reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    request_token = request_password_reset(reset_user.email)
    real_code = VerificationCode.objects.latest('created_at').code
    verified_token = verify_reset_code(request_token, real_code)
    confirm_password_reset(verified_token, 'NewStrongPass456!')
    confirmation_emails = [m for m in mail.outbox if 'restableci' in m.subject.lower()]
    assert len(confirmation_emails) == 1
    assert confirmation_emails[0].to == [reset_user.email]


# ==========================================================================
# HTTP-level integration tests (views + routes)
# ==========================================================================


from rest_framework.test import APIClient  # noqa: E402


@pytest.fixture
def api_client():
    return APIClient()


def test_request_view_returns_token_for_existing_email(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['reset_request_token']
    assert len(mail.outbox) == 1


def test_request_view_returns_decoy_token_for_unknown_email(api_client, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': 'ghost@example.com'}, format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['reset_request_token']
    assert len(mail.outbox) == 0


def test_request_view_rejects_malformed_email(api_client):
    resp = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': 'not-an-email'}, format='json',
    )
    assert resp.status_code == 400


def test_verify_view_happy_path(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    assert r2.status_code == 200
    assert r2.json()['reset_verified_token']


def test_verify_view_wrong_code_surfaces_attempts_left(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': '000000'}, format='json',
    )
    assert r2.status_code == 400
    body = r2.json()
    assert body['detail'] == 'invalid_code'
    assert body['attempts_left'] == 4


def test_confirm_view_completes_flow_and_returns_session(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    verified_token = r2.json()['reset_verified_token']
    r3 = api_client.post(
        '/api/accounts/password-reset/confirm/',
        {'reset_verified_token': verified_token, 'new_password': 'NewStrongPass456!'}, format='json',
    )
    assert r3.status_code == 200
    body = r3.json()
    assert 'access' in body and 'refresh' in body
    reset_user.refresh_from_db()
    assert reset_user.check_password('NewStrongPass456!')


def test_confirm_view_weak_password_returns_errors(api_client, reset_user, settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []
    r1 = api_client.post(
        '/api/accounts/password-reset/request/',
        {'email': reset_user.email}, format='json',
    )
    request_token = r1.json()['reset_request_token']
    code = VerificationCode.objects.latest('created_at').code
    r2 = api_client.post(
        '/api/accounts/password-reset/verify-code/',
        {'reset_request_token': request_token, 'code': code}, format='json',
    )
    verified_token = r2.json()['reset_verified_token']
    r3 = api_client.post(
        '/api/accounts/password-reset/confirm/',
        {'reset_verified_token': verified_token, 'new_password': '12345678'}, format='json',
    )
    # 8-char all-numeric password: passes serializer min_length but should fail
    # Django's NumericPasswordValidator inside the service.
    assert r3.status_code == 400
    body = r3.json()
    assert body['detail'] == 'weak_password'
    assert isinstance(body['errors'], list) and body['errors']
