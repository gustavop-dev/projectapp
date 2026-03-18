import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def onboarded_client_user():
    user = User.objects.create_user(
        username='client@test.com', email='client@test.com', password='realpass123',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return user


@pytest.fixture
def non_onboarded_client_user():
    user = User.objects.create_user(
        username='new@test.com', email='new@test.com', password='temppass123',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=False)
    return user


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@test.com', email='admin@test.com', password='adminpass1',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.mark.django_db
class TestLoginOnboardedUser:
    def test_login_returns_jwt_tokens(self, api_client, onboarded_client_user):
        resp = api_client.post('/api/accounts/login/', {
            'email': 'client@test.com',
            'password': 'realpass123',
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data['requires_verification'] is False
        assert 'access' in data['tokens']
        assert 'refresh' in data['tokens']
        assert data['user']['email'] == 'client@test.com'
        assert data['user']['role'] == 'client'

    def test_login_admin_returns_jwt(self, api_client, admin_user):
        resp = api_client.post('/api/accounts/login/', {
            'email': 'admin@test.com',
            'password': 'adminpass1',
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data['requires_verification'] is False
        assert data['user']['role'] == 'admin'

    def test_login_wrong_password_rejected(self, api_client, onboarded_client_user):
        resp = api_client.post('/api/accounts/login/', {
            'email': 'client@test.com',
            'password': 'wrongpass',
        })

        assert resp.status_code == 401

    def test_login_nonexistent_email_rejected(self, api_client):
        resp = api_client.post('/api/accounts/login/', {
            'email': 'nobody@test.com',
            'password': 'whatever',
        })

        assert resp.status_code == 401

    def test_login_inactive_user_rejected(self, api_client, onboarded_client_user):
        onboarded_client_user.is_active = False
        onboarded_client_user.save()

        resp = api_client.post('/api/accounts/login/', {
            'email': 'client@test.com',
            'password': 'realpass123',
        })

        assert resp.status_code == 401


@pytest.mark.django_db
class TestLoginNonOnboardedUser:
    def test_login_triggers_verification(self, api_client, non_onboarded_client_user, mailoutbox):
        resp = api_client.post('/api/accounts/login/', {
            'email': 'new@test.com',
            'password': 'temppass123',
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data['requires_verification'] is True
        assert 'verification_token' in data
        assert data['email'] == 'new@test.com'
        assert len(mailoutbox) == 1

    def test_login_no_profile_rejected(self, api_client):
        User.objects.create_user(
            username='noprofile@test.com', email='noprofile@test.com', password='pass1234',
        )
        resp = api_client.post('/api/accounts/login/', {
            'email': 'noprofile@test.com',
            'password': 'pass1234',
        })

        assert resp.status_code == 403
