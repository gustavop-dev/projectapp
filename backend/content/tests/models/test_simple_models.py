"""Tests for Design, Model3D, and PortfolioWork models.

Covers: __str__, bilingual fields, basic creation.
"""
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from content.models import Design, Model3D, PortfolioWork

pytestmark = pytest.mark.django_db


class TestDesign:
    def test_str_returns_english_title(self, design):
        assert str(design) == 'Modern Dashboard'
        assert design.title_en in str(design)

    def test_bilingual_fields(self, design):
        assert design.title_en == 'Modern Dashboard'
        assert design.title_es == 'Dashboard Moderno'
        assert design.category_title_en == 'Web Design'
        assert design.category_title_es == 'Diseño Web'

    def test_delete_removes_image_files(self, db, tmp_path, monkeypatch):
        """Verify both cover and detail image files are removed on delete."""
        monkeypatch.setattr('django.conf.settings.MEDIA_ROOT', str(tmp_path))
        cover = SimpleUploadedFile('cover.png', b'\x89PNG\r\n', content_type='image/png')
        detail = SimpleUploadedFile('detail.png', b'\x89PNG\r\n', content_type='image/png')
        d = Design.objects.create(
            title_en='Del', title_es='Del',
            category_title_en='Cat', category_title_es='Cat',
            cover_image=cover, detail_image=detail,
        )
        cover_path = d.cover_image.path
        detail_path = d.detail_image.path
        assert os.path.isfile(cover_path)
        assert os.path.isfile(detail_path)
        d.delete()
        assert not os.path.isfile(cover_path)
        assert not os.path.isfile(detail_path)


class TestModel3D:
    def test_str_returns_english_title(self, model_3d):
        assert str(model_3d) == 'Product Viewer'
        assert model_3d.title_en in str(model_3d)

    def test_bilingual_fields(self, model_3d):
        assert model_3d.title_en == 'Product Viewer'
        assert model_3d.title_es == 'Visor de Producto'
        assert model_3d.category_title_en == '3D Animation'
        assert model_3d.category_title_es == 'Animación 3D'

    def test_delete_removes_image_and_file(self, db, tmp_path, monkeypatch):
        """Verify both image and 3D model file are removed on delete."""
        monkeypatch.setattr('django.conf.settings.MEDIA_ROOT', str(tmp_path))
        img = SimpleUploadedFile('img.png', b'\x89PNG\r\n', content_type='image/png')
        model_file = SimpleUploadedFile('model.glb', b'glTF', content_type='application/octet-stream')
        m = Model3D.objects.create(
            title_en='Del', title_es='Del',
            category_title_en='Cat', category_title_es='Cat',
            image=img, file=model_file,
        )
        img_path = m.image.path
        file_path = m.file.path
        assert os.path.isfile(img_path)
        assert os.path.isfile(file_path)
        m.delete()
        assert not os.path.isfile(img_path)
        assert not os.path.isfile(file_path)


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
