"""LinkedIn publish language defaults: English first (US audience focus)."""
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import BlogPost
from content.services.blog_service import auto_publish_blog_to_linkedin

pytestmark = pytest.mark.django_db


def _post(**overrides):
    defaults = dict(
        title_es='Título ES',
        title_en='Title EN',
        slug='lang-default-post',
        excerpt_es='Extracto.',
        excerpt_en='Excerpt.',
        linkedin_summary_es='Resumen en español.',
        linkedin_summary_en='Summary in English.',
        is_published=True,
        published_at=timezone.now(),
    )
    defaults.update(overrides)
    return BlogPost.objects.create(**defaults)


class TestAutoPublishLanguagePreference:
    def test_prefers_english_when_both_summaries_exist(self):
        post = _post()
        with patch('content.services.linkedin_service.publish_blog_to_linkedin') as mock_publish:
            mock_publish.return_value = {'success': True, 'post_id': 'urn:li:share:1'}
            auto_publish_blog_to_linkedin(post)
        kwargs = mock_publish.call_args.kwargs
        assert kwargs['summary'] == 'Summary in English.'
        assert kwargs['title'] == 'Title EN'
        assert kwargs['description'] == 'Excerpt.'

    def test_falls_back_to_spanish_when_no_english_summary(self):
        post = _post(linkedin_summary_en='', slug='lang-fallback-post')
        with patch('content.services.linkedin_service.publish_blog_to_linkedin') as mock_publish:
            mock_publish.return_value = {'success': True, 'post_id': 'urn:li:share:2'}
            auto_publish_blog_to_linkedin(post)
        kwargs = mock_publish.call_args.kwargs
        assert kwargs['summary'] == 'Resumen en español.'
        assert kwargs['title'] == 'Título ES'
        assert kwargs['description'] == 'Extracto.'


class TestManualPublishDefaultLanguage:
    def test_publish_endpoint_defaults_to_english(self, admin_client):
        post = _post(slug='manual-default-post')
        url = reverse('publish-to-linkedin', kwargs={'post_id': post.id})
        with patch('content.views.linkedin.publish_blog_to_linkedin') as mock_publish:
            mock_publish.return_value = {'success': True, 'post_id': 'urn:li:share:3'}
            response = admin_client.post(url, {}, format='json')
        assert response.status_code == 200
        kwargs = mock_publish.call_args.kwargs
        assert kwargs['summary'] == 'Summary in English.'
        assert kwargs['title'] == 'Title EN'
