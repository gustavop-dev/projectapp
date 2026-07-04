"""Expiry warning service: threshold, dedup via cache, recipients."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone

from content.models import LinkedInToken
from content.services.linkedin_expiry_service import check_linkedin_token_expiry

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def staff_user():
    return get_user_model().objects.create_user(
        username='admin_expiry', password='x', is_staff=True,
        email='admin@projectapp.co',
    )


def _token_expiring_in(days):
    token = LinkedInToken.load()
    token.access_token_encrypted = 'x'  # non-empty → "connected" for this check
    token.expires_at = timezone.now() + timedelta(days=days)
    token.save()
    return token


def test_not_connected_returns_early(staff_user):
    assert check_linkedin_token_expiry() == 'not_connected'
    assert len(mail.outbox) == 0


def test_far_from_expiry_is_ok(staff_user):
    _token_expiring_in(30)
    assert check_linkedin_token_expiry() == 'ok'
    assert len(mail.outbox) == 0


def test_warns_once_within_seven_days(staff_user):
    _token_expiring_in(5)
    assert check_linkedin_token_expiry() == 'warned'
    assert len(mail.outbox) == 1
    assert 'admin@projectapp.co' in mail.outbox[0].to
    assert check_linkedin_token_expiry() == 'already_warned'
    assert len(mail.outbox) == 1


def test_no_staff_recipients_skips_email():
    _token_expiring_in(5)
    result = check_linkedin_token_expiry()
    assert result in ('warned', 'already_warned')
    assert len(mail.outbox) == 0
