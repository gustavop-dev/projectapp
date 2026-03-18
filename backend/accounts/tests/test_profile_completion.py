import io

import pytest
from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def onboarded_client():
    user = User.objects.create_user(
        username='onboarded@test.com',
        email='onboarded@test.com',
        password='securepass1',
        first_name='Ana',
        last_name='García',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=False,
    )
    return user


@pytest.fixture
def client_headers(api_client, onboarded_client):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'onboarded@test.com',
        'password': 'securepass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


def _make_test_image():
    img = Image.new('RGB', (200, 200), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    buf.name = 'avatar.jpg'
    return buf


@pytest.mark.django_db
class TestCompleteProfile:
    def test_complete_profile_sets_profile_completed_flag(self, api_client, client_headers, onboarded_client):
        resp = api_client.post(
            '/api/accounts/me/complete-profile/',
            {
                'company_name': 'TestCorp',
                'phone': '+57 300 111 2222',
                'cedula': '1234567890',
                'date_of_birth': '1990-05-15',
                'gender': 'female',
                'education_level': 'universitario',
            },
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data['profile_completed'] is True
        assert data['company_name'] == 'TestCorp'
        assert data['cedula'] == '1234567890'
        assert data['gender'] == 'female'
        assert data['education_level'] == 'universitario'

    def test_complete_profile_rejects_missing_required_field(self, api_client, client_headers):
        resp = api_client.post(
            '/api/accounts/me/complete-profile/',
            {
                'company_name': 'TestCorp',
                'phone': '+57 300 111 2222',
            },
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 400

    def test_complete_profile_rejects_second_submission(self, api_client, client_headers, onboarded_client):
        payload = {
            'company_name': 'TestCorp',
            'phone': '+57 300 111 2222',
            'cedula': '1234567890',
            'date_of_birth': '1990-05-15',
            'gender': 'male',
            'education_level': 'tecnico',
        }
        api_client.post('/api/accounts/me/complete-profile/', payload, format='multipart', **client_headers)

        resp = api_client.post('/api/accounts/me/complete-profile/', payload, format='multipart', **client_headers)

        assert resp.status_code == 400

    def test_complete_profile_accepts_avatar_upload(self, api_client, client_headers, onboarded_client):
        avatar = _make_test_image()
        resp = api_client.post(
            '/api/accounts/me/complete-profile/',
            {
                'company_name': 'AvatarCorp',
                'phone': '+57 300 111 3333',
                'cedula': '9876543210',
                'date_of_birth': '1988-12-01',
                'gender': 'male',
                'education_level': 'posgrado',
                'avatar': avatar,
            },
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data['avatar_display_url'] != ''
        onboarded_client.profile.refresh_from_db()
        assert onboarded_client.profile.avatar is not None

    def test_complete_profile_updates_user_first_and_last_name(self, api_client, client_headers, onboarded_client):
        api_client.post(
            '/api/accounts/me/complete-profile/',
            {
                'company_name': 'NameCorp',
                'phone': '+57 300 111 4444',
                'cedula': '1111111111',
                'date_of_birth': '1995-03-20',
                'gender': 'other',
                'education_level': 'secundaria',
                'first_name': 'NuevoNombre',
                'last_name': 'NuevoApellido',
            },
            format='multipart',
            **client_headers,
        )

        onboarded_client.refresh_from_db()
        assert onboarded_client.first_name == 'NuevoNombre'
        assert onboarded_client.last_name == 'NuevoApellido'

    def test_complete_profile_rejects_unauthenticated_request(self, api_client):
        resp = api_client.post('/api/accounts/me/complete-profile/', {
            'company_name': 'X', 'phone': '1', 'cedula': '1',
            'date_of_birth': '1990-01-01', 'gender': 'male', 'education_level': 'otro',
        })

        assert resp.status_code == 401


@pytest.mark.django_db
class TestProfileNewFields:
    def test_me_returns_new_profile_fields(self, api_client, client_headers, onboarded_client):
        profile = onboarded_client.profile
        profile.cedula = '5555555555'
        profile.gender = 'female'
        profile.education_level = 'universitario'
        profile.save()

        resp = api_client.get('/api/accounts/me/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['cedula'] == '5555555555'
        assert data['gender'] == 'female'
        assert data['education_level'] == 'universitario'
        assert 'profile_completed' in data

    def test_me_patch_updates_new_fields(self, api_client, client_headers, onboarded_client):
        resp = api_client.patch(
            '/api/accounts/me/',
            {
                'cedula': '9999999999',
                'gender': 'prefer_not_to_say',
                'education_level': 'posgrado',
                'date_of_birth': '1985-07-10',
            },
            format='json',
            **client_headers,
        )

        assert resp.status_code == 200
        onboarded_client.profile.refresh_from_db()
        assert onboarded_client.profile.cedula == '9999999999'
        assert onboarded_client.profile.gender == 'prefer_not_to_say'
