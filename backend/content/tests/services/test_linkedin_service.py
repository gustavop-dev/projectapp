"""Tests for LinkedIn OAuth service.

Covers: token exchange, encrypted storage, auto-refresh, publish,
connection status, and encryption round-trip.
"""
from datetime import datetime, timedelta, timezone as dt_tz
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from freezegun import freeze_time

from content.models import LinkedInToken
from content.services import linkedin_service

pytestmark = pytest.mark.django_db

FROZEN_NOW = datetime(2026, 4, 4, 12, 0, 0, tzinfo=dt_tz.utc)

LINKEDIN_SETTINGS = {
    'LINKEDIN_CLIENT_ID': 'test-client-id',
    'LINKEDIN_CLIENT_SECRET': 'test-client-secret',
    'LINKEDIN_REDIRECT_URI': 'https://example.com/callback',
    'LINKEDIN_ENCRYPTION_KEY': '',
}


@pytest.fixture
def fernet_key():
    """Generate a valid Fernet key for tests."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


@pytest.fixture
def token_with_access(fernet_key):
    """A LinkedInToken with a valid access token."""
    with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
        token = LinkedInToken.load()
        token.set_access_token('test-access-token-123')
        token.expires_at = FROZEN_NOW + timedelta(days=30)
        token.obtained_at = FROZEN_NOW
        token.member_sub = 'abc123'
        token.profile_name = 'Test User'
        token.profile_email = 'test@example.com'
        token.save()
        return token


@pytest.fixture
def token_with_refresh(fernet_key):
    """A LinkedInToken with both access and refresh tokens (access expired)."""
    with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
        token = LinkedInToken.load()
        token.set_access_token('expired-access-token')
        token.set_refresh_token('valid-refresh-token')
        token.expires_at = FROZEN_NOW - timedelta(hours=1)
        token.refresh_token_expires_at = FROZEN_NOW + timedelta(days=30)
        token.obtained_at = FROZEN_NOW - timedelta(days=30)
        token.member_sub = 'abc123'
        token.profile_name = 'Test User'
        token.save()
        return token


# ---------------------------------------------------------------------------
# TestExchangeCodeForToken
# ---------------------------------------------------------------------------

class TestExchangeCodeForToken:

    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    @patch('content.services.linkedin_service._cache_profile_info')
    def test_saves_encrypted_token_on_success(self, mock_cache, mock_post, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'access_token': 'new-access-token',
                'expires_in': 5_184_000,
                'refresh_token': 'new-refresh-token',
            }
            mock_post.return_value = mock_resp

            result = linkedin_service.exchange_code_for_token('auth-code-123')

            assert result['access_token'] == 'new-access-token'
            mock_post.assert_called_once()
            mock_cache.assert_called_once()
            token = LinkedInToken.load()
            assert token.get_access_token() == 'new-access-token'
            assert token.get_refresh_token() == 'new-refresh-token'
            assert token.expires_at is not None

    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    @patch('content.services.linkedin_service._cache_profile_info')
    def test_computes_expires_at_from_response(self, mock_cache, mock_post, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'access_token': 'tok',
                'expires_in': 3600,
            }
            mock_post.return_value = mock_resp

            linkedin_service.exchange_code_for_token('code')

            mock_post.assert_called_once()
            token = LinkedInToken.load()
            assert token.expires_at is not None
            delta = token.expires_at - token.obtained_at
            assert 3590 < delta.total_seconds() < 3610

    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    def test_raises_value_error_on_api_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = 'invalid_grant'
        mock_post.return_value = mock_resp

        with pytest.raises(ValueError, match='token exchange failed') as exc_info:
            linkedin_service.exchange_code_for_token('bad-code')

        assert 'token exchange failed' in str(exc_info.value)
        mock_post.assert_called_once()

    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    @patch('content.services.linkedin_service._cache_profile_info')
    def test_handles_missing_refresh_token(self, mock_cache, mock_post, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'access_token': 'access-only',
                'expires_in': 5_184_000,
            }
            mock_post.return_value = mock_resp

            linkedin_service.exchange_code_for_token('code')

            mock_post.assert_called_once()
            token = LinkedInToken.load()
            assert token.get_access_token() == 'access-only'
            assert token.get_refresh_token() is None


# ---------------------------------------------------------------------------
# TestGetAccessToken
# ---------------------------------------------------------------------------

class TestGetAccessToken:

    @freeze_time(FROZEN_NOW)
    def test_returns_token_when_valid(self, fernet_key, token_with_access):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            result = linkedin_service.get_access_token()
            assert result == 'test-access-token-123'

    def test_returns_none_when_no_token(self, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            result = linkedin_service.get_access_token()
            assert result is None

    @freeze_time(FROZEN_NOW)
    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    def test_refreshes_expired_token(self, mock_post, fernet_key, token_with_refresh):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'access_token': 'refreshed-access-token',
                'expires_in': 5_184_000,
            }
            mock_post.return_value = mock_resp

            result = linkedin_service.get_access_token()
            assert result == 'refreshed-access-token'

            mock_post.assert_called_once()
            token = LinkedInToken.load()
            assert token.get_access_token() == 'refreshed-access-token'

    @freeze_time(FROZEN_NOW)
    def test_clears_token_when_refresh_also_expired(self, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            token = LinkedInToken.load()
            token.set_access_token('expired')
            token.set_refresh_token('also-expired')
            token.expires_at = FROZEN_NOW - timedelta(hours=1)
            token.refresh_token_expires_at = FROZEN_NOW - timedelta(days=1)
            token.save()

            result = linkedin_service.get_access_token()
            assert result is None

            token.refresh_from_db()
            assert token.get_access_token() is None


# ---------------------------------------------------------------------------
# TestRefreshAccessToken
# ---------------------------------------------------------------------------

class TestRefreshAccessToken:

    @freeze_time(FROZEN_NOW)
    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    def test_successful_refresh_updates_token(self, mock_post, fernet_key, token_with_refresh):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'access_token': 'new-from-refresh',
                'expires_in': 5_184_000,
            }
            mock_post.return_value = mock_resp

            result = linkedin_service._refresh_access_token()
            assert result == 'new-from-refresh'
            mock_post.assert_called_once()

    @freeze_time(FROZEN_NOW)
    @override_settings(**LINKEDIN_SETTINGS)
    @patch('content.services.linkedin_service.requests.post')
    def test_failed_refresh_clears_token(self, mock_post, fernet_key, token_with_refresh):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = 'invalid_token'
            mock_post.return_value = mock_resp

            result = linkedin_service._refresh_access_token()
            assert result is None

            mock_post.assert_called_once()
            token = LinkedInToken.load()
            assert token.get_access_token() is None


# ---------------------------------------------------------------------------
# TestPublishBlogToLinkedin
# ---------------------------------------------------------------------------

class TestPublishBlogToLinkedin:

    @freeze_time(FROZEN_NOW)
    @patch('content.services.linkedin_service._upload_image_to_linkedin', return_value='urn:li:image:C4E10test')
    @patch('content.services.linkedin_service.requests.post')
    @patch('content.services.linkedin_service.get_member_urn', return_value='urn:li:person:abc')
    @patch('content.services.linkedin_service.get_access_token', return_value='valid-token')
    def test_successful_publish_returns_post_id(self, mock_token, mock_urn, mock_post, mock_upload):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {'x-restli-id': 'urn:li:share:123456'}
        mock_post.return_value = mock_resp

        result = linkedin_service.publish_blog_to_linkedin(
            summary='Test summary',
            blog_url='https://projectapp.co/blog/test',
            title='Test Post',
            cover_image_url='https://images.unsplash.com/photo-test',
        )

        assert result['success'] is True
        assert result['post_id'] == 'urn:li:share:123456'
        mock_upload.assert_called_once_with('https://images.unsplash.com/photo-test')
        mock_post.assert_called_once()
        # Verify the thumbnail is the image URN, not the raw URL
        call_payload = mock_post.call_args[1]['json']
        assert call_payload['content']['article']['thumbnail'] == 'urn:li:image:C4E10test'

    @patch('content.services.linkedin_service.get_access_token', return_value=None)
    def test_raises_when_not_connected(self, mock_token):
        with pytest.raises(ValueError, match='not connected') as exc_info:
            linkedin_service.publish_blog_to_linkedin(
                summary='Test', blog_url='https://x.co', title='T',
            )

        assert 'not connected' in str(exc_info.value)
        mock_token.assert_called_once()

    @patch('content.services.linkedin_service.requests.post')
    @patch('content.services.linkedin_service.get_member_urn', return_value='urn:li:person:abc')
    @patch('content.services.linkedin_service.get_access_token', return_value='valid-token')
    def test_returns_failure_on_api_error(self, mock_token, mock_urn, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = 'Forbidden'
        mock_resp.headers = {}
        mock_post.return_value = mock_resp

        result = linkedin_service.publish_blog_to_linkedin(
            summary='Test', blog_url='https://x.co', title='T',
        )
        assert result['success'] is False
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# TestGetConnectionStatus
# ---------------------------------------------------------------------------

class TestGetConnectionStatus:

    @freeze_time(FROZEN_NOW)
    def test_returns_connected_with_cached_profile(self, fernet_key, token_with_access):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            result = linkedin_service.get_connection_status()
            assert result['connected'] is True
            assert result['profile_name'] == 'Test User'

    def test_returns_disconnected_when_no_token(self, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            result = linkedin_service.get_connection_status()
            assert result['connected'] is False

    @freeze_time(FROZEN_NOW)
    @patch('content.services.linkedin_service._fetch_profile_from_api', return_value=None)
    def test_clears_token_on_invalid_profile(self, mock_fetch, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            token = LinkedInToken.load()
            token.set_access_token('some-token')
            token.expires_at = FROZEN_NOW + timedelta(days=30)
            token.profile_name = ''
            token.save()

            result = linkedin_service.get_connection_status()
            assert result['connected'] is False

            mock_fetch.assert_called_once()
            token.refresh_from_db()
            assert token.get_access_token() is None


# ---------------------------------------------------------------------------
# TestEncryptionHelpers
# ---------------------------------------------------------------------------

class TestEncryptionHelpers:

    def test_round_trip_encryption(self, fernet_key):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=fernet_key):
            token = LinkedInToken.load()
            token.set_access_token('super-secret-token')
            token.save()

            token.refresh_from_db()
            assert token.get_access_token() == 'super-secret-token'

    def test_returns_none_with_empty_encryption_key(self):
        with override_settings(LINKEDIN_ENCRYPTION_KEY=''):
            token = LinkedInToken.load()
            token.access_token_encrypted = 'some-encrypted-data'
            token.save()

            assert token.get_access_token() is None
