"""Tests for QRCard serializers."""
import pytest

from content.models import QRCard
from content.serializers.qr_cards import (
    QRCardListSerializer,
    QRCardCreateUpdateSerializer,
)

pytestmark = pytest.mark.django_db


class TestQRCardListSerializer:
    def test_serializes_expected_fields(self):
        card = QRCard.objects.create(name='Tarjeta evento X', destination_url='https://example.com')
        data = QRCardListSerializer(card).data
        assert data['name'] == 'Tarjeta evento X'
        assert data['destination_url'] == 'https://example.com'
        assert data['is_active'] is True
        assert 'id' in data
        assert 'created_at' in data


class TestQRCardCreateUpdateSerializer:
    def test_valid_with_only_name(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'Tarjeta evento X'})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_without_name(self):
        serializer = QRCardCreateUpdateSerializer(data={'destination_url': 'https://example.com'})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_invalid_with_malformed_destination_url(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'X', 'destination_url': 'not-a-url'})
        assert not serializer.is_valid()
        assert 'destination_url' in serializer.errors

    def test_valid_with_empty_destination_url(self):
        serializer = QRCardCreateUpdateSerializer(data={'name': 'X', 'destination_url': ''})
        assert serializer.is_valid(), serializer.errors
