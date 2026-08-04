"""Tests for QRCard admin CRUD views (the public redirect view is tested
in test_qr_card_redirect.py, since it lives outside /api/)."""
import pytest
from django.urls import reverse

from content.models import QRCard

pytestmark = pytest.mark.django_db


@pytest.fixture
def qr_card(db):
    return QRCard.objects.create(name='Tarjeta evento X', destination_url='https://example.com')


class TestAdminListQrCards:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-qr-cards'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_all_cards(self, admin_client, qr_card):
        response = admin_client.get(reverse('list-admin-qr-cards'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Tarjeta evento X'


class TestAdminCreateQrCard:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-qr-card'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_card_returns_201(self, admin_client):
        payload = {'name': 'Tarjeta nueva'}
        response = admin_client.post(reverse('create-qr-card'), payload, format='json')
        assert response.status_code == 201
        assert QRCard.objects.count() == 1
        assert response.data['is_active'] is True

    def test_returns_400_without_name(self, admin_client):
        response = admin_client.post(reverse('create-qr-card'), {}, format='json')
        assert response.status_code == 400


class TestAdminUpdateQrCard:
    def test_returns_401_for_unauthenticated(self, api_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = api_client.patch(url, {}, format='json')
        assert response.status_code in (401, 403)

    def test_updates_destination_url(self, admin_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.patch(url, {'destination_url': 'https://new-destination.com'}, format='json')
        assert response.status_code == 200
        qr_card.refresh_from_db()
        assert qr_card.destination_url == 'https://new-destination.com'

    def test_toggles_is_active(self, admin_client, qr_card):
        url = reverse('update-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.patch(url, {'is_active': False}, format='json')
        assert response.status_code == 200
        qr_card.refresh_from_db()
        assert qr_card.is_active is False

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('update-qr-card', kwargs={'card_id': '11111111-1111-1111-1111-111111111111'})
        response = admin_client.patch(url, {'name': 'X'}, format='json')
        assert response.status_code == 404


class TestAdminDeleteQrCard:
    def test_returns_401_for_unauthenticated(self, api_client, qr_card):
        url = reverse('delete-qr-card', kwargs={'card_id': qr_card.id})
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_deletes_card_returns_204(self, admin_client, qr_card):
        url = reverse('delete-qr-card', kwargs={'card_id': qr_card.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert QRCard.objects.count() == 0
