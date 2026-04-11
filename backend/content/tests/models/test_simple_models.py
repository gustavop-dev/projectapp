"""Tests for PortfolioWork model.

Covers: __str__, bilingual fields, basic creation.
"""
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from content.models import PortfolioWork

pytestmark = pytest.mark.django_db


class TestPortfolioWork:
    def test_str_returns_english_title(self, portfolio_work):
        assert str(portfolio_work) == 'Client Portal'
        assert portfolio_work.title_en in str(portfolio_work)

    def test_project_url_stored(self, portfolio_work):
        assert portfolio_work.project_url == 'https://example.com/client-portal'
        assert portfolio_work.project_url.startswith('https://')

    def test_bilingual_fields(self, portfolio_work):
        assert portfolio_work.title_en == 'Client Portal'
        assert portfolio_work.title_es == 'Portal de Cliente'

    def test_slug_collision_appends_counter(self, db):
        """When two works share the same title the second gets a suffixed slug."""
        pw1 = PortfolioWork.objects.create(
            title_en='Same Title', title_es='Mismo Titulo',
            project_url='https://example.com/a',
        )
        pw2 = PortfolioWork.objects.create(
            title_en='Same Title', title_es='Mismo Titulo',
            project_url='https://example.com/b',
        )
        assert pw1.slug == 'mismo-titulo'
        assert pw2.slug == 'mismo-titulo-1'

    def test_save_preserves_existing_slug(self, db):
        """Providing a slug bypasses auto-generation."""
        portfolio_work = PortfolioWork.objects.create(
            title_en='Same Title',
            title_es='Mismo Titulo',
            slug='manual-slug',
            project_url='https://example.com/manual',
        )
        assert portfolio_work.slug == 'manual-slug'

    def test_delete_removes_cover_image(self, db, tmp_path, monkeypatch):
        """Verify cover image file is removed from disk on delete."""
        monkeypatch.setattr('django.conf.settings.MEDIA_ROOT', str(tmp_path))
        cover = SimpleUploadedFile('cover.png', b'\x89PNG\r\n', content_type='image/png')
        pw = PortfolioWork.objects.create(
            title_en='Del', title_es='Del',
            project_url='https://example.com',
            category_title_en='Cat', category_title_es='Cat',
            cover_image=cover,
        )
        cover_path = pw.cover_image.path
        assert os.path.isfile(cover_path)
        pw.delete()
        assert not os.path.isfile(cover_path)

    def test_delete_without_cover_image_succeeds(self, db):
        """Deleting a record without a cover image skips file removal."""
        portfolio_work = PortfolioWork.objects.create(
            title_en='No Cover',
            title_es='Sin Cover',
            project_url='https://example.com/no-cover',
        )
        portfolio_work.delete()
        assert PortfolioWork.objects.filter(pk=portfolio_work.pk).exists() is False
