import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@test.com', email='admin@test.com', password='adminpass1',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@test.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def sample_client(admin_user):
    user = User.objects.create_user(
        username='existing@client.com', email='existing@client.com',
        password='temp1234', first_name='Luis', last_name='Pérez',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, company_name='ClientCorp',
        created_by=admin_user,
    )
    return user


@pytest.mark.django_db
class TestClientList:
    def test_list_clients_returns_only_clients(self, api_client, admin_headers, sample_client):
        resp = api_client.get('/api/accounts/clients/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['email'] == 'existing@client.com'
        assert data[0]['company_name'] == 'ClientCorp'

    def test_filter_onboarded_clients(self, api_client, admin_headers, sample_client):
        resp = api_client.get('/api/accounts/clients/?filter=onboarded', **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filter_pending_clients(self, api_client, admin_headers, sample_client):
        resp = api_client.get('/api/accounts/clients/?filter=pending', **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 0


@pytest.mark.django_db
class TestCreateClient:
    def test_create_client_success(self, api_client, admin_headers, mailoutbox):
        resp = api_client.post('/api/accounts/clients/', {
            'email': 'new@client.com',
            'first_name': 'New',
            'last_name': 'Client',
            'company_name': 'NewCorp',
        }, **admin_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['email'] == 'new@client.com'
        assert data['is_onboarded'] is False
        assert len(mailoutbox) == 1

    def test_create_duplicate_email_rejected(self, api_client, admin_headers, sample_client):
        resp = api_client.post('/api/accounts/clients/', {
            'email': 'existing@client.com',
            'first_name': 'Dup', 'last_name': 'User',
        }, **admin_headers)

        assert resp.status_code == 400


@pytest.mark.django_db
class TestClientDetail:
    def test_get_client_detail(self, api_client, admin_headers, sample_client):
        resp = api_client.get(f'/api/accounts/clients/{sample_client.id}/', **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['email'] == 'existing@client.com'

    def test_update_client(self, api_client, admin_headers, sample_client):
        resp = api_client.patch(
            f'/api/accounts/clients/{sample_client.id}/',
            {'company_name': 'UpdatedCorp', 'first_name': 'Updated'},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['company_name'] == 'UpdatedCorp'
        assert resp.json()['first_name'] == 'Updated'

    def test_deactivate_client(self, api_client, admin_headers, sample_client):
        resp = api_client.delete(f'/api/accounts/clients/{sample_client.id}/', **admin_headers)

        assert resp.status_code == 200
        sample_client.refresh_from_db()
        assert sample_client.is_active is False

    def test_get_nonexistent_client_returns_404(self, api_client, admin_headers):
        resp = api_client.get('/api/accounts/clients/99999/', **admin_headers)

        assert resp.status_code == 404


@pytest.mark.django_db
class TestResendInvite:
    def test_resend_invite_success(self, api_client, admin_headers, sample_client, mailoutbox):
        resp = api_client.post(
            f'/api/accounts/clients/{sample_client.id}/resend-invite/',
            **admin_headers,
        )

        assert resp.status_code == 200
        assert len(mailoutbox) == 1
        sample_client.refresh_from_db()
        assert sample_client.profile.is_onboarded is False
