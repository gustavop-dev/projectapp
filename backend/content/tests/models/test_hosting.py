"""
Tests for the Hosting model.

Covers: __str__, bilingual fields, pricing fields.
"""
import pytest
from decimal import Decimal

from content.models import Hosting


pytestmark = pytest.mark.django_db


class TestHosting:
    def test_str_returns_english_title(self, hosting):
        assert str(hosting) == 'Professional Plan'

    def test_pricing_fields_stored_correctly(self, hosting):
        assert hosting.semi_annually_price == Decimal('149.99')
        assert hosting.annual_price == Decimal('249.99')

    def test_bilingual_fields(self, hosting):
        assert hosting.title_en == 'Professional Plan'
        assert hosting.title_es == 'Plan Profesional'
        assert hosting.description_en == 'Best for growing businesses.'
        assert hosting.description_es == 'Ideal para negocios en crecimiento.'

    def test_spec_fields_populated(self, hosting):
        assert hosting.cpu_cores_en == '4 vCPUs'
        assert hosting.ram_en == '8 GB'
        assert hosting.storage_en == '100 GB SSD'
        assert hosting.bandwidth_en == 'Unlimited'
