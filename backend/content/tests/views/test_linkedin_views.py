"""Tests for LinkedIn integration views.

Covers: OAuth auth URL, callback with state validation, connection status,
and rate-limited publish endpoint.
"""
from datetime import datetime, timedelta
from datetime import timezone as dt_tz
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import BlogPost
from content.serializers.blog import BLOG_JSON_TEMPLATE

pytestmark = pytest.mark.django_db

FROZEN_NOW = datetime(2026, 4, 4, 12, 0, 0, tzinfo=dt_tz.utc)


@pytest.fixture
def blog_post_with_summary(db):
    """A published blog post with LinkedIn summary fields populated."""
    return BlogPost.objects.create(
        title_es='Post de prueba',
        title_en='Test post',
        slug='test-linkedin-post',
        excerpt_es='Extracto.',
        excerpt_en='Excerpt.',
        linkedin_summary_es='Resumen para LinkedIn en español.',
        linkedin_summary_en='LinkedIn summary in English.',
        is_published=True,
        published_at=timezone.now(),
    )


@pytest.fixture
def blog_post_no_summary(db):
    """A published blog post without LinkedIn summary."""
    return BlogPost.objects.create(
        title_es='Post sin resumen',
        title_en='Post without summary',
        slug='no-summary-post',
        excerpt_es='Extracto.',
        excerpt_en='Excerpt.',
        is_published=True,
        published_at=timezone.now(),
    )


# ---------------------------------------------------------------------------
# TestLinkedinAuthUrl
# ---------------------------------------------------------------------------

class TestLinkedinAuthUrl:

    def test_returns_authorization_url_for_admin(self, admin_client):
        response = admin_client.get(reverse('linkedin-auth-url'))
        assert response.status_code == 200
        assert 'authorization_url' in response.data
        assert 'state' in response.data
        assert 'linkedin.com/oauth' in response.data['authorization_url']

    def test_stores_state_in_cache(self, admin_client):
        response = admin_client.get(reverse('linkedin-auth-url'))
        state = response.data['state']
        assert cache.get(f'linkedin_oauth_state:{state}') is True

    def test_rejects_unauthenticated_user(self, api_client):
        response = api_client.get(reverse('linkedin-auth-url'))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# TestLinkedinCallback
# ---------------------------------------------------------------------------

class TestLinkedinCallback:

    @patch('content.views.linkedin.get_connection_status', return_value={'connected': True})
    @patch('content.views.linkedin.exchange_code_for_token', return_value={'access_token': 'tok'})
    def test_successful_callback_with_valid_state(self, mock_exchange, mock_status, admin_client):
        # Pre-set state in cache
        cache.set('linkedin_oauth_state:valid-state-123', True, timeout=600)

        response = admin_client.post(
            reverse('linkedin-callback'),
            {'code': 'auth-code-abc', 'state': 'valid-state-123'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        # State should be consumed
        assert cache.get('linkedin_oauth_state:valid-state-123') is None

    def test_rejects_missing_state(self, admin_client):
        response = admin_client.post(
            reverse('linkedin-callback'),
            {'code': 'auth-code'},
            format='json',
        )
        assert response.status_code == 400
        assert 'state' in response.data['error'].lower()

    def test_rejects_invalid_state(self, admin_client):
        response = admin_client.post(
            reverse('linkedin-callback'),
            {'code': 'auth-code', 'state': 'invalid-state-xyz'},
            format='json',
        )
        assert response.status_code == 400
        assert 'expired' in response.data['error'].lower() or 'invalid' in response.data['error'].lower()

    @patch('content.views.linkedin.exchange_code_for_token', side_effect=ValueError('exchange failed'))
    def test_returns_400_on_exchange_failure(self, mock_exchange, admin_client):
        cache.set('linkedin_oauth_state:fail-state', True, timeout=600)
        response = admin_client.post(
            reverse('linkedin-callback'),
            {'code': 'bad-code', 'state': 'fail-state'},
            format='json',
        )
        assert response.status_code == 400
        assert 'exchange failed' in response.data['error']


# ---------------------------------------------------------------------------
# TestLinkedinStatus
# ---------------------------------------------------------------------------

class TestLinkedinStatus:

    @patch('content.views.linkedin.get_connection_status', return_value={'connected': True, 'profile_name': 'Admin'})
    def test_returns_status_for_admin(self, mock_status, admin_client):
        response = admin_client.get(reverse('linkedin-status'))
        assert response.status_code == 200
        assert response.data['connected'] is True

    def test_rejects_unauthenticated(self, api_client):
        response = api_client.get(reverse('linkedin-status'))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# TestPublishToLinkedin
# ---------------------------------------------------------------------------

class TestPublishToLinkedin:

    @patch('content.views.linkedin.publish_blog_to_linkedin', return_value={
        'success': True, 'post_id': 'urn:li:share:999', 'message': 'OK',
    })
    def test_publishes_successfully(self, mock_publish, admin_client, blog_post_with_summary):
        url = reverse('publish-to-linkedin', kwargs={'post_id': blog_post_with_summary.id})
        response = admin_client.post(url, {'lang': 'es'}, format='json')
        assert response.status_code == 200
        assert response.data['success'] is True

        blog_post_with_summary.refresh_from_db()
        assert blog_post_with_summary.linkedin_post_id == 'urn:li:share:999'
        assert blog_post_with_summary.linkedin_published_at is not None

    def test_returns_404_for_nonexistent_post(self, admin_client):
        url = reverse('publish-to-linkedin', kwargs={'post_id': 99999})
        response = admin_client.post(url, {'lang': 'es'}, format='json')
        assert response.status_code == 404

    def test_returns_400_for_empty_summary(self, admin_client, blog_post_no_summary):
        url = reverse('publish-to-linkedin', kwargs={'post_id': blog_post_no_summary.id})
        response = admin_client.post(url, {'lang': 'es'}, format='json')
        assert response.status_code == 400
        assert 'empty' in response.data['error'].lower()

    @freeze_time(FROZEN_NOW)
    @patch('content.views.linkedin.publish_blog_to_linkedin')
    def test_rate_limits_duplicate_publish(self, mock_publish, admin_client, blog_post_with_summary):
        # Simulate a recent publish (5 minutes ago)
        blog_post_with_summary.linkedin_published_at = FROZEN_NOW - timedelta(minutes=5)
        blog_post_with_summary.save()

        url = reverse('publish-to-linkedin', kwargs={'post_id': blog_post_with_summary.id})
        response = admin_client.post(url, {'lang': 'es'}, format='json')
        assert response.status_code == 429
        assert 'recently' in response.data['error'].lower() or 'wait' in response.data['error'].lower()
        mock_publish.assert_not_called()

    @freeze_time(FROZEN_NOW)
    @patch('content.views.linkedin.publish_blog_to_linkedin', return_value={
        'success': True, 'post_id': 'urn:li:share:new', 'message': 'OK',
    })
    def test_allows_publish_after_cooldown(self, mock_publish, admin_client, blog_post_with_summary):
        # Simulate a publish 15 minutes ago (past cooldown)
        blog_post_with_summary.linkedin_published_at = FROZEN_NOW - timedelta(minutes=15)
        blog_post_with_summary.save()

        url = reverse('publish-to-linkedin', kwargs={'post_id': blog_post_with_summary.id})
        response = admin_client.post(url, {'lang': 'es'}, format='json')
        assert response.status_code == 200
        assert response.data['success'] is True


# ---------------------------------------------------------------------------
# TestAutoPublishOnBlogCreate
# ---------------------------------------------------------------------------

class TestAutoPublishOnBlogCreate:

    @patch('content.views.blog._auto_publish_to_linkedin')
    def test_calls_auto_publish_when_created_published_with_summary(self, mock_auto, admin_client):
        payload = {
            'title_es': 'Auto post',
            'title_en': 'Auto post EN',
            'excerpt_es': 'Extracto.',
            'excerpt_en': 'Excerpt.',
            'content_json_es': BLOG_JSON_TEMPLATE,
            'is_published': True,
            'linkedin_summary_es': 'Resumen para LinkedIn.',
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json',
        )
        assert response.status_code == 201
        mock_auto.assert_called_once()

    @patch('content.views.blog._auto_publish_to_linkedin')
    def test_calls_auto_publish_for_draft_but_returns_early(self, mock_auto, admin_client):
        payload = {
            'title_es': 'Draft post',
            'title_en': 'Draft EN',
            'excerpt_es': 'Extracto.',
            'excerpt_en': 'Excerpt.',
            'content_json_es': BLOG_JSON_TEMPLATE,
            'is_published': False,
            'linkedin_summary_es': 'Resumen.',
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json',
        )
        assert response.status_code == 201
        mock_auto.assert_called_once()
