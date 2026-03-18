import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import UserProfile
from accounts.permissions import IsAdminRole, IsClientRole, IsOnboarded

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='client@test.com',
        email='client@test.com',
        password='realpass123',
        first_name='Client',
        last_name='User',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        company_name='Client Corp',
        phone='+57 300 000 0000',
    )
    return user


def _client_headers(api_client):
    response = api_client.post('/api/accounts/login/', {
        'email': 'client@test.com',
        'password': 'realpass123',
    })
    assert response.status_code == 200
    token = response.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_headers(api_client, client_user):
    return _client_headers(api_client)


@pytest.mark.django_db
class TestAdminClientPermissions:
    def test_list_clients_rejects_request_without_authentication(self, api_client):
        response = api_client.get('/api/accounts/clients/')

        assert response.status_code == 401

    def test_list_clients_rejects_request_for_client_role(self, api_client, client_headers):
        response = api_client.get('/api/accounts/clients/', **client_headers)

        assert response.status_code == 403

    def test_create_client_rejects_request_for_client_role(self, api_client, client_headers):
        response = api_client.post('/api/accounts/clients/', {
            'email': 'new@client.com',
            'first_name': 'New',
            'last_name': 'Client',
            'company_name': 'New Corp',
        }, **client_headers)

        assert response.status_code == 403


@pytest.mark.django_db
class TestProfilePermissions:
    def test_me_rejects_request_without_authentication(self, api_client):
        response = api_client.get('/api/accounts/me/')

        assert response.status_code == 401

    def test_me_returns_profile_for_authenticated_client(self, api_client, client_headers):
        response = api_client.get('/api/accounts/me/', **client_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'client@test.com'
        assert data['role'] == 'client'
        assert data['company_name'] == 'Client Corp'

    def test_me_updates_profile_for_authenticated_client(self, api_client, client_headers, client_user):
        response = api_client.patch(
            '/api/accounts/me/',
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'company_name': 'Updated Corp',
                'phone': '+57 311 111 1111',
            },
            format='json',
            **client_headers,
        )

        assert response.status_code == 200
        client_user.refresh_from_db()
        client_user.profile.refresh_from_db()
        assert client_user.first_name == 'Updated'
        assert client_user.last_name == 'Name'
        assert client_user.profile.company_name == 'Updated Corp'
        assert client_user.profile.phone == '+57 311 111 1111'


# =========================================================================
# Permission class unit tests
# =========================================================================

class _FakeRequest:
    """Lightweight request stub for permission unit tests."""
    def __init__(self, user=None):
        self.user = user


@pytest.mark.django_db
class TestIsAdminRolePermission:
    def test_grants_access_to_admin(self):
        user = User.objects.create_user(
            username='padm@t.com', email='padm@t.com', password='p',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN)

        perm = IsAdminRole()

        assert perm.has_permission(_FakeRequest(user), None) is True

    def test_denies_access_to_client(self):
        user = User.objects.create_user(
            username='pcli@t.com', email='pcli@t.com', password='p',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        perm = IsAdminRole()

        assert perm.has_permission(_FakeRequest(user), None) is False

    def test_denies_access_to_user_without_profile(self):
        user = User.objects.create_user(
            username='pnone@t.com', email='pnone@t.com', password='p',
        )

        perm = IsAdminRole()

        assert perm.has_permission(_FakeRequest(user), None) is False

    def test_denies_access_to_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        perm = IsAdminRole()

        assert perm.has_permission(_FakeRequest(AnonymousUser()), None) is False


@pytest.mark.django_db
class TestIsClientRolePermission:
    def test_grants_access_to_client(self):
        user = User.objects.create_user(
            username='pcr@t.com', email='pcr@t.com', password='p',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        perm = IsClientRole()

        assert perm.has_permission(_FakeRequest(user), None) is True

    def test_denies_access_to_admin(self):
        user = User.objects.create_user(
            username='pcra@t.com', email='pcra@t.com', password='p',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN)

        perm = IsClientRole()

        assert perm.has_permission(_FakeRequest(user), None) is False

    def test_denies_access_to_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        perm = IsClientRole()

        assert perm.has_permission(_FakeRequest(AnonymousUser()), None) is False


@pytest.mark.django_db
class TestIsOnboardedPermission:
    def test_grants_access_to_onboarded_user(self):
        user = User.objects.create_user(
            username='pon@t.com', email='pon@t.com', password='p',
        )
        UserProfile.objects.create(user=user, is_onboarded=True)

        perm = IsOnboarded()

        assert perm.has_permission(_FakeRequest(user), None) is True

    def test_denies_access_to_non_onboarded_user(self):
        user = User.objects.create_user(
            username='poff@t.com', email='poff@t.com', password='p',
        )
        UserProfile.objects.create(user=user, is_onboarded=False)

        perm = IsOnboarded()

        assert perm.has_permission(_FakeRequest(user), None) is False

    def test_denies_access_to_user_without_profile(self):
        user = User.objects.create_user(
            username='ponp@t.com', email='ponp@t.com', password='p',
        )

        perm = IsOnboarded()

        assert perm.has_permission(_FakeRequest(user), None) is False
