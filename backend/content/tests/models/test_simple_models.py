"""
Tests for Design, Model3D, and PortfolioWork models.

Covers: __str__, bilingual fields, basic creation.
"""
import pytest

from content.models import Design, Model3D, PortfolioWork


pytestmark = pytest.mark.django_db


class TestDesign:
    def test_str_returns_english_title(self, design):
        assert str(design) == 'Modern Dashboard'

    def test_bilingual_fields(self, design):
        assert design.title_en == 'Modern Dashboard'
        assert design.title_es == 'Dashboard Moderno'
        assert design.category_title_en == 'Web Design'
        assert design.category_title_es == 'Diseño Web'


class TestModel3D:
    def test_str_returns_english_title(self, model_3d):
        assert str(model_3d) == 'Product Viewer'

    def test_bilingual_fields(self, model_3d):
        assert model_3d.title_en == 'Product Viewer'
        assert model_3d.title_es == 'Visor de Producto'
        assert model_3d.category_title_en == '3D Animation'
        assert model_3d.category_title_es == 'Animación 3D'


class TestPortfolioWork:
    def test_str_returns_english_title(self, portfolio_work):
        assert str(portfolio_work) == 'Client Portal'

    def test_project_url_stored(self, portfolio_work):
        assert portfolio_work.project_url == 'https://example.com/client-portal'

    def test_bilingual_fields(self, portfolio_work):
        assert portfolio_work.title_en == 'Client Portal'
        assert portfolio_work.title_es == 'Portal de Cliente'
