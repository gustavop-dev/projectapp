"""
Tests for Item, Category, and Product models.

Covers: relationships, __str__, bilingual fields, M2M associations.
"""
import pytest
from decimal import Decimal

from content.models import Item, Category, Product


pytestmark = pytest.mark.django_db


class TestItem:
    def test_str_returns_english_name(self, item):
        assert str(item) == 'Responsive Design'

    def test_create_item_with_bilingual_names(self, db):
        i = Item.objects.create(name_en='SEO', name_es='SEO')
        assert i.name_en == 'SEO'
        assert i.name_es == 'SEO'


class TestCategory:
    def test_str_returns_english_name(self, category):
        assert str(category) == 'Web Development'

    def test_category_has_items(self, category, item):
        assert item in category.items.all()

    def test_item_reverse_relation(self, category, item):
        assert category in item.categories.all()


class TestProduct:
    def test_str_returns_english_title(self, product):
        assert str(product) == 'E-Commerce Platform'

    def test_product_has_categories(self, product, category):
        assert category in product.categories.all()

    def test_product_price_stored_correctly(self, product):
        assert product.price == Decimal('4999.99')

    def test_mobile_app_price_nullable(self, db):
        prod = Product.objects.create(
            title_en='Basic Site',
            title_es='Sitio Básico',
            description_en='Simple site.',
            description_es='Sitio simple.',
            price=Decimal('999.99'),
            development_time_en='2 weeks',
            development_time_es='2 semanas',
        )
        assert prod.mobile_app_price is None
