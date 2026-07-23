"""Model-level tests for the encrypted LinkedInToken singleton."""
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from django.utils import timezone
from freezegun import freeze_time

from content.models import LinkedInToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def fernet_key(settings):
    key = Fernet.generate_key().decode()
    settings.LINKEDIN_ENCRYPTION_KEY = key
    return key


def test_str_reflects_the_connection_state(fernet_key):
    token = LinkedInToken.load()
    assert str(token) == 'LinkedInToken (connected=False)'
    token.set_access_token('secreto')
    assert str(token) == 'LinkedInToken (connected=True)'


def test_access_token_round_trip(fernet_key):
    token = LinkedInToken.load()
    token.set_access_token('acceso-123')
    assert token.access_token_encrypted != 'acceso-123'
    assert token.get_access_token() == 'acceso-123'


def test_refresh_token_round_trip(fernet_key):
    token = LinkedInToken.load()
    token.set_refresh_token('refresco-456')
    assert token.get_refresh_token() == 'refresco-456'


def test_set_access_token_requires_a_configured_key(settings):
    settings.LINKEDIN_ENCRYPTION_KEY = ''
    token = LinkedInToken.load()
    with pytest.raises(ValueError, match='LINKEDIN_ENCRYPTION_KEY'):
        token.set_access_token('secreto')
    assert token.access_token_encrypted == ''


def test_set_refresh_token_rejects_an_invalid_key(settings):
    settings.LINKEDIN_ENCRYPTION_KEY = 'clave-no-fernet'
    token = LinkedInToken.load()
    with pytest.raises(ValueError, match='LINKEDIN_ENCRYPTION_KEY'):
        token.set_refresh_token('refresco')
    assert token.refresh_token_encrypted == ''


def test_get_access_token_none_without_key(fernet_key, settings):
    token = LinkedInToken.load()
    token.set_access_token('secreto')
    settings.LINKEDIN_ENCRYPTION_KEY = ''
    assert token.get_access_token() is None


def test_get_access_token_none_for_undecryptable_ciphertext(fernet_key, settings):
    token = LinkedInToken.load()
    token.set_access_token('secreto')
    settings.LINKEDIN_ENCRYPTION_KEY = Fernet.generate_key().decode()
    assert token.get_access_token() is None


def test_get_refresh_token_none_when_nothing_stored(fernet_key):
    token = LinkedInToken.load()
    assert token.get_refresh_token() is None


@freeze_time('2026-01-15 12:00:00')
def test_is_expired_true_without_date_and_false_in_the_future(fernet_key):
    token = LinkedInToken.load()
    assert token.is_expired is True
    token.expires_at = timezone.now() + timedelta(days=30)
    assert token.is_expired is False


@freeze_time('2026-01-15 12:00:00')
def test_is_refresh_expired_true_without_date_and_false_in_the_future(fernet_key):
    token = LinkedInToken.load()
    assert token.is_refresh_expired is True
    token.refresh_token_expires_at = timezone.now() + timedelta(days=365)
    assert token.is_refresh_expired is False


@freeze_time('2026-01-15 12:00:00')
def test_clear_wipes_every_stored_field(fernet_key):
    token = LinkedInToken.load()
    token.set_access_token('a')
    token.set_refresh_token('b')
    token.expires_at = timezone.now()
    token.profile_name = 'Gustavo'
    token.clear()
    assert token.access_token_encrypted == ''
    assert token.refresh_token_encrypted == ''
    assert token.expires_at is None
    assert token.profile_name == ''
