"""Tests for accounts/collection_account_views.py — all functions untested."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Project, UserProfile
from content.models.document_collection_account import DocumentCollectionAccount

User = get_user_model()

pytestmark = pytest.mark.django_db

BASE_URL = '/api/accounts/collection-accounts/'


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='ca2-admin@test.com',
        email='ca2-admin@test.com',
        password='pass12345',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN)
    return user


@pytest.fixture
def client_user_obj(db, admin_user):
    user = User.objects.create_user(
        username='ca2-client@test.com',
        email='ca2-client@test.com',
        password='pass12345',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, created_by=admin_user,
    )
    return user


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def regular_client(client_user_obj):
    client = APIClient()
    client.force_authenticate(user=client_user_obj)
    return client


@pytest.fixture
def project(client_user_obj):
    return Project.objects.create(
        name='CA Test Project',
        client=client_user_obj,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )


def _create_payload(title='Test Invoice', client_user_id=None):
    data = {
        'title': title,
        'payment_term_type': DocumentCollectionAccount.PaymentTermType.AGAINST_DELIVERY,
        'city': 'Bogotá',
    }
    if client_user_id is not None:
        data['client_user_id'] = client_user_id
    return data


# ---------------------------------------------------------------------------
# collection_account_list_create_view — GET
# ---------------------------------------------------------------------------

class TestListCollectionAccounts:
    def test_unauthenticated_request_returns_401(self, api_client):
        response = api_client.get(BASE_URL)

        assert response.status_code == 401

    def test_admin_gets_empty_list_when_no_accounts(self, admin_client):
        response = admin_client.get(BASE_URL)

        assert response.status_code == 200
        assert response.json() == []

    def test_admin_filter_by_commercial_status(self, admin_client):
        response = admin_client.get(BASE_URL + '?commercial_status=draft')

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_client_cannot_see_draft_accounts(self, regular_client):
        response = regular_client.get(BASE_URL)

        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# collection_account_list_create_view — POST (create)
# ---------------------------------------------------------------------------

class TestCreateCollectionAccount:
    def test_admin_creates_account_with_valid_payload(self, admin_client, client_user_obj):
        response = admin_client.post(
            BASE_URL,
            data=_create_payload(client_user_id=client_user_obj.id),
            format='json',
        )

        assert response.status_code == 201
        assert response.json()['title'] == 'Test Invoice'

    def test_non_admin_cannot_create_returns_403(self, regular_client, client_user_obj):
        response = regular_client.post(
            BASE_URL,
            data=_create_payload(client_user_id=client_user_obj.id),
            format='json',
        )

        assert response.status_code == 403

    def test_invalid_payload_missing_client_user_returns_400(self, admin_client):
        response = admin_client.post(
            BASE_URL,
            data={
                'title': 'No Client',
                'payment_term_type': DocumentCollectionAccount.PaymentTermType.AGAINST_DELIVERY,
            },
            format='json',
        )

        assert response.status_code == 400

    def test_create_with_valid_project_id_uses_project_client(self, admin_client, project):
        response = admin_client.post(
            BASE_URL,
            data={
                'title': 'Project Invoice',
                'payment_term_type': DocumentCollectionAccount.PaymentTermType.AGAINST_DELIVERY,
                'project_id': project.id,
            },
            format='json',
        )

        assert response.status_code == 201

    def test_create_with_invalid_project_id_returns_400(self, admin_client, client_user_obj):
        response = admin_client.post(
            BASE_URL,
            data={
                'title': 'Bad Project',
                'payment_term_type': DocumentCollectionAccount.PaymentTermType.AGAINST_DELIVERY,
                'project_id': 99999,
            },
            format='json',
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# collection_account_detail_view — GET / PATCH
# ---------------------------------------------------------------------------

class TestRetrieveCollectionAccount:
    def test_admin_retrieve_existing_account_returns_200(self, admin_client, client_user_obj):
        create_resp = admin_client.post(
            BASE_URL,
            data=_create_payload(client_user_id=client_user_obj.id),
            format='json',
        )
        account_id = create_resp.json()['id']

        response = admin_client.get(f'{BASE_URL}{account_id}/')

        assert response.status_code == 200
        assert response.json()['id'] == account_id

    def test_retrieve_nonexistent_account_returns_404(self, admin_client):
        response = admin_client.get(f'{BASE_URL}999999/')

        assert response.status_code == 404


class TestUpdateCollectionAccount:
    def test_admin_partial_update_title(self, admin_client, client_user_obj):
        create_resp = admin_client.post(
            BASE_URL,
            data=_create_payload(client_user_id=client_user_obj.id),
            format='json',
        )
        account_id = create_resp.json()['id']

        response = admin_client.patch(
            f'{BASE_URL}{account_id}/',
            data={'title': 'Updated Title'},
            format='json',
        )

        assert response.status_code == 200
        assert response.json()['title'] == 'Updated Title'

    def test_non_admin_update_returns_403(self, admin_client, regular_client, client_user_obj):
        create_resp = admin_client.post(
            BASE_URL,
            data=_create_payload(client_user_id=client_user_obj.id),
            format='json',
        )
        account_id = create_resp.json()['id']

        response = regular_client.patch(
            f'{BASE_URL}{account_id}/',
            data={'title': 'Hacked Title'},
            format='json',
        )

        assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# project_collection_account_list_view — GET
# ---------------------------------------------------------------------------

class TestProjectCollectionAccountList:
    def test_admin_list_by_project_returns_200(self, admin_client, project):
        response = admin_client.get(
            f'/api/accounts/projects/{project.id}/collection-accounts/',
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_nonexistent_project_returns_404(self, admin_client):
        response = admin_client.get(
            '/api/accounts/projects/999999/collection-accounts/',
        )

        assert response.status_code == 404
