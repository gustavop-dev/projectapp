"""Tests for the project access feature (URLs + admin credentials)."""

import os

# Must be set before any import touches accounts.services.credential_cipher,
# whose Fernet key is cached via lru_cache on first call.
os.environ.setdefault('PROJECT_ACCESS_CIPHER_KEY', 'uFJ2bxSRv2V4OLA4y-BxJcTYL8QxIrRiG4rZa_3BaiI=')

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Project, UserProfile
from accounts.services import credential_cipher
from accounts.services.credential_cipher import decrypt_password, encrypt_password

User = get_user_model()


@pytest.fixture(autouse=True)
def _reset_cipher_cache():
    credential_cipher._get_cipher.cache_clear()
    yield
    credential_cipher._get_cipher.cache_clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin-access@proj.com', email='admin-access@proj.com', password='adminpass1',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN,
        is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin-access@proj.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client-access@proj.com', email='client-access@proj.com', password='clientpass1',
        first_name='Ana', last_name='Pérez',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='AnaCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client-access@proj.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project_with_access(client_user):
    return Project.objects.create(
        name='Site GIM',
        client=client_user,
        status=Project.STATUS_ACTIVE,
        production_url='https://gim.example.com',
        staging_url='https://staging.gim.example.com',
        admin_url='https://gim.example.com/admin',
        repository_url='https://github.com/example/gim',
        admin_username='root',
        admin_password_encrypted=encrypt_password('s3cret-pass'),
    )


class TestCredentialCipher:
    def test_encrypt_decrypt_round_trip_returns_original(self):
        token = encrypt_password('hunter2')
        assert token != 'hunter2'
        assert decrypt_password(token) == 'hunter2'

    def test_encrypt_empty_returns_empty_string(self):
        assert encrypt_password('') == ''

    def test_decrypt_invalid_token_returns_empty_string(self):
        assert decrypt_password('not-a-valid-token') == ''


@pytest.mark.django_db
class TestProjectAccessList:
    URL = '/api/accounts/projects/access/'

    def test_admin_sees_access_list_with_decrypted_password(
        self, api_client, admin_headers, project_with_access,
    ):
        resp = api_client.get(self.URL, **admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        entry = data[0]
        assert entry['id'] == project_with_access.id
        assert entry['production_url'] == 'https://gim.example.com'
        assert entry['admin_username'] == 'root'
        assert entry['admin_password'] == 's3cret-pass'

    def test_client_cannot_access_list(self, api_client, client_headers, project_with_access):
        resp = api_client.get(self.URL, **client_headers)
        assert resp.status_code == 403

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401

    def test_archived_projects_are_excluded(
        self, api_client, admin_headers, project_with_access,
    ):
        project_with_access.status = Project.STATUS_ARCHIVED
        project_with_access.save(update_fields=['status'])
        resp = api_client.get(self.URL, **admin_headers)
        assert resp.json() == []


@pytest.mark.django_db
class TestProjectUpdateWritesEncryptedCredentials:
    def test_admin_update_encrypts_password_before_storing(
        self, api_client, admin_headers, project_with_access,
    ):
        resp = api_client.patch(
            f'/api/accounts/projects/{project_with_access.id}/',
            data={
                'production_url': 'https://new.example.com',
                'admin_username': 'newroot',
                'admin_password': 'newpass1',
            },
            format='json',
            **admin_headers,
        )
        assert resp.status_code == 200
        project_with_access.refresh_from_db()
        assert project_with_access.production_url == 'https://new.example.com'
        assert project_with_access.admin_username == 'newroot'
        assert project_with_access.admin_password_encrypted != 'newpass1'
        assert decrypt_password(project_with_access.admin_password_encrypted) == 'newpass1'
