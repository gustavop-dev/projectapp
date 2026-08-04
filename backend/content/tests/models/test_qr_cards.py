"""Tests for the QRCard model."""
import pytest

from content.models import QRCard

pytestmark = pytest.mark.django_db


class TestQRCardModel:
    def test_id_is_auto_generated(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.id is not None

    def test_ids_are_unique_across_cards(self):
        card_a = QRCard.objects.create(name='Tarjeta A')
        card_b = QRCard.objects.create(name='Tarjeta B')
        assert card_a.id != card_b.id

    def test_is_active_defaults_to_true(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.is_active is True

    def test_destination_url_defaults_to_empty_string(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert card.destination_url == ''

    def test_str_includes_name_and_id(self):
        card = QRCard.objects.create(name='Tarjeta evento X')
        assert 'Tarjeta evento X' in str(card)
        assert str(card.id) in str(card)
