"""Tests for linktree admin CRUD views, the public-by-handle endpoint and
the root /lk/<handle> clean-URL redirect."""
import pytest
from django.urls import reverse

from content.models import Linktree, LinktreeButton

pytestmark = pytest.mark.django_db


@pytest.fixture
def linktree(db):
    tree = Linktree.objects.create(handle='gustavo', name='Gustavo', display_name='Gustavo Pérez')
    LinktreeButton.objects.create(
        linktree=tree, tier='primary', action='linkedin',
        label='Conectemos en LinkedIn', href='https://linkedin.com/in/x',
    )
    return tree


class TestAdminListLinktrees:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-linktrees'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_rows(self, admin_client, linktree):
        response = admin_client.get(reverse('list-admin-linktrees'))
        assert response.status_code == 200
        assert response.data[0]['handle'] == 'gustavo'
        assert response.data[0]['buttons_count'] == 1


class TestAdminRetrieveLinktree:
    def test_returns_detail_with_buttons(self, admin_client, linktree):
        url = reverse('retrieve-admin-linktree', kwargs={'linktree_id': linktree.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert len(response.data['buttons']) == 1


class TestAdminCreateLinktree:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-linktree'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_with_normalized_handle(self, admin_client):
        response = admin_client.post(
            reverse('create-linktree'),
            {'handle': '@Nuevo.Handle', 'name': 'Nuevo'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['handle'] == 'nuevo.handle'

    def test_returns_400_without_name(self, admin_client):
        response = admin_client.post(
            reverse('create-linktree'), {'handle': 'x1x'}, format='json'
        )
        assert response.status_code == 400


class TestAdminUpdateLinktree:
    def test_updates_buttons_via_replace(self, admin_client, linktree):
        url = reverse('update-linktree', kwargs={'linktree_id': linktree.id})
        payload = {'buttons': [
            {'tier': 'primary', 'action': 'whatsapp', 'label': 'Escríbenos',
             'href': 'https://wa.me/5731'},
        ]}
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        assert [b['label'] for b in response.data['buttons']] == ['Escríbenos']

    def test_returns_400_on_cardinality_violation(self, admin_client, linktree):
        url = reverse('update-linktree', kwargs={'linktree_id': linktree.id})
        payload = {'buttons': [
            {'tier': 'primary', 'action': 'web', 'label': 'A', 'href': 'https://a.co'},
            {'tier': 'primary', 'action': 'web', 'label': 'B', 'href': 'https://b.co'},
        ]}
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 400


class TestAdminDeleteLinktree:
    def test_deletes_and_returns_204(self, admin_client, linktree):
        url = reverse('delete-linktree', kwargs={'linktree_id': linktree.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert not Linktree.objects.filter(pk=linktree.id).exists()


class TestPublicLinktree:
    def test_resolves_handle_with_at_prefix(self, api_client, linktree):
        url = reverse('public-linktree', kwargs={'handle': '@gustavo'})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['display_name'] == 'Gustavo Pérez'

    def test_returns_404_for_inactive_linktree(self, api_client, linktree):
        linktree.is_active = False
        linktree.save()
        url = reverse('public-linktree', kwargs={'handle': 'gustavo'})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_returns_404_for_unknown_handle(self, api_client):
        url = reverse('public-linktree', kwargs={'handle': 'nadie'})
        response = api_client.get(url)
        assert response.status_code == 404


class TestLinktreeShortRedirect:
    def test_redirects_to_locale_prefixed_page(self, api_client, linktree):
        response = api_client.get('/lk/@gustavo')
        assert response.status_code == 302
        assert response.url == '/es-co/lk/@gustavo'

    def test_accepts_handle_without_at(self, api_client, linktree):
        response = api_client.get('/lk/gustavo/')
        assert response.status_code == 302
        assert response.url == '/es-co/lk/@gustavo'

    def test_returns_404_for_unknown_handle(self, api_client):
        response = api_client.get('/lk/@nadie')
        assert response.status_code == 404
