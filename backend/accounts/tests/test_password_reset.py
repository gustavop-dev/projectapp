"""Tests for the platform password recovery flow."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.services.tokens import (
    PASSWORD_RESET_REQUEST_PURPOSE,
    PASSWORD_RESET_VERIFIED_PURPOSE,
    decode_password_reset_token,
    get_decoy_password_reset_request_token,
    get_password_reset_request_token,
    get_password_reset_verified_token,
)

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
