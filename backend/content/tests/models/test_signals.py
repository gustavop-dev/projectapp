"""Tests for content/signals.py.

Covers: _delete_file() utility and post_delete signal handlers for
BlogPost, PortfolioWork, and IssuerProfile.
"""
from unittest.mock import MagicMock, patch

import pytest

from content.models.blog_post import BlogPost
from content.models.issuer_profile import IssuerProfile
from content.models.portfolio_works import PortfolioWork
from content.signals import _delete_file

pytestmark = pytest.mark.django_db


# ── _delete_file utility ───────────────────────────────────────────────────────

class TestDeleteFileUtility:
    def test_calls_storage_delete_with_field_name(self):
        field = MagicMock()
        field.name = 'images/cover.jpg'
        _delete_file(field)
        field.storage.delete.assert_called_once_with('images/cover.jpg')
        assert field.storage.delete.call_count == 1

    def test_does_not_call_delete_when_field_name_is_empty(self):
        field = MagicMock()
        field.name = ''
        _delete_file(field)
        field.storage.delete.assert_not_called()
        assert field.storage.delete.call_count == 0

    def test_does_not_call_delete_when_field_name_is_none(self):
        field = MagicMock()
        field.name = None
        _delete_file(field)
        field.storage.delete.assert_not_called()
        assert field.storage.delete.call_count == 0

    def test_does_not_raise_when_storage_delete_raises(self):
        field = MagicMock()
        field.name = 'images/cover.jpg'
        field.storage.delete.side_effect = OSError('disk error')
        _delete_file(field)
        field.storage.delete.assert_called_once()
        assert field.storage.delete.call_count == 1

    def test_does_not_raise_when_field_is_falsy(self):
        result = _delete_file(None)
        assert result is None


# ── BlogPost signal ────────────────────────────────────────────────────────────

class TestDeleteBlogPostFiles:
    def test_calls_delete_file_with_cover_image_on_delete(self):
        post = BlogPost.objects.create(
            title_es='Señales test',
            title_en='Signal test',
            excerpt_es='Extracto.',
            excerpt_en='Excerpt.',
            content_es='<p>ES</p>',
            content_en='<p>EN</p>',
            is_published=False,
        )
        with patch('content.signals._delete_file') as mock_fn:
            cover = post.cover_image
            post.delete()
            mock_fn.assert_called_once_with(cover)
            assert mock_fn.call_count == 1


# ── PortfolioWork signal ───────────────────────────────────────────────────────

class TestDeletePortfolioWorkFiles:
    def test_calls_delete_file_with_cover_image_on_delete(self):
        work = PortfolioWork.objects.create(
            title_en='Signal Work',
            title_es='Trabajo señal',
            project_url='https://example.com',
            category_title_en='Web',
            category_title_es='Web',
        )
        with patch('content.signals._delete_file') as mock_fn:
            cover = work.cover_image
            work.delete()
            mock_fn.assert_called_once_with(cover)
            assert mock_fn.call_count == 1


# ── IssuerProfile signal ───────────────────────────────────────────────────────

class TestDeleteIssuerProfileFiles:
    def test_calls_delete_file_with_logo_on_delete(self):
        profile = IssuerProfile.objects.create(name='Acme Issuer')
        with patch('content.signals._delete_file') as mock_fn:
            logo = profile.logo
            profile.delete()
            mock_fn.assert_called_once_with(logo)
            assert mock_fn.call_count == 1
