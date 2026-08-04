"""Tests for the public QR card redirect view (top-level /t/<uuid>/ route,
registered in projectapp/urls.py — NOT under /api/)."""
import pytest
from django.urls import reverse

from content.models import QRCard

pytestmark = pytest.mark.django_db


class TestQrCardRedirect:
    def test_returns_404_for_nonexistent_uuid(self, api_client):
        url = reverse('qr-card-redirect', kwargs={'card_id': '11111111-1111-1111-1111-111111111111'})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_redirects_to_destination_when_active_and_configured(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='https://example.com/landing', is_active=True)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 302
        assert response.url == 'https://example.com/landing'

    def test_returns_200_with_message_when_inactive(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='https://example.com/landing', is_active=False)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'no está disponible' in response.content.decode()

    def test_returns_200_with_message_when_no_destination_configured(self, api_client):
        card = QRCard.objects.create(name='X', destination_url='', is_active=True)
        url = reverse('qr-card-redirect', kwargs={'card_id': card.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'aún no ha sido configurado' in response.content.decode()
