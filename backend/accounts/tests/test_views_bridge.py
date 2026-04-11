import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import UserProfile

User = get_user_model()

BRIDGE_URL = '/api/accounts/session-token-bridge/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user():
    user = User.objects.create_user(
        username='staff@bridge.com', email='staff@bridge.com', password='staffpass1!',
        first_name='Staff', last_name='Bridge', is_staff=True,
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def non_staff_user():
    user = User.objects.create_user(
        username='regular@bridge.com', email='regular@bridge.com', password='pass1!',
        first_name='Regular', last_name='User', is_staff=False,
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return user


@pytest.fixture
def staff_no_profile():
    return User.objects.create_user(
        username='bare@bridge.com', email='bare@bridge.com', password='barepass1!',
        first_name='Bare', last_name='Staff', is_staff=True,
    )


@pytest.mark.django_db
class TestSessionTokenBridge:
    def test_staff_with_session_receives_jwt_tokens(self, api_client, staff_user):
        api_client.force_login(staff_user)

        response = api_client.post(BRIDGE_URL)

        assert response.status_code == 200
        data = response.json()
        assert 'tokens' in data
        assert 'access' in data['tokens']
        assert 'refresh' in data['tokens']
        assert 'user' in data
        assert data['user']['email'] == 'staff@bridge.com'
        assert data['user']['role'] == 'admin'

    def test_non_staff_user_gets_403(self, api_client, non_staff_user):
        api_client.force_login(non_staff_user)

        response = api_client.post(BRIDGE_URL)

        assert response.status_code == 403

    def test_unauthenticated_request_gets_401(self, api_client):
        response = api_client.post(BRIDGE_URL)

        assert response.status_code == 401

    def test_staff_without_profile_auto_creates_admin_profile(self, api_client, staff_no_profile):
        api_client.force_login(staff_no_profile)
        assert not UserProfile.objects.filter(user=staff_no_profile).exists()

        response = api_client.post(BRIDGE_URL)

        assert response.status_code == 200
        profile = UserProfile.objects.get(user=staff_no_profile)
        assert profile.role == UserProfile.ROLE_ADMIN
        assert profile.is_onboarded is True

        data = response.json()
        assert data['user']['role'] == 'admin'
