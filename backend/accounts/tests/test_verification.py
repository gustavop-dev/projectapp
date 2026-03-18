import pytest
from django.contrib.auth import get_user_model
from freezegun import freeze_time
from rest_framework.test import APIClient

from accounts.models import UserProfile, VerificationCode

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pending_client_user():
    user = User.objects.create_user(
        username='pending@test.com',
        email='pending@test.com',
        password='temppass123',
        first_name='Pending',
        last_name='Client',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=False,
    )
    return user


def _login_for_verification(api_client):
    response = api_client.post('/api/accounts/login/', {
        'email': 'pending@test.com',
        'password': 'temppass123',
    })
    assert response.status_code == 200
    data = response.json()
    assert data['requires_verification'] is True
    return data['verification_token']


@pytest.mark.django_db
class TestVerificationCodeFlow:
    @freeze_time('2025-01-01 10:00:00')
    def test_verify_rejects_expired_code_for_pending_client(self, api_client, pending_client_user, mailoutbox):
        verification_token = _login_for_verification(api_client)

        assert len(mailoutbox) == 1
        otp = VerificationCode.objects.get(user=pending_client_user, is_used=False)

        with freeze_time('2025-01-01 10:11:00'):
            response = api_client.post(
                '/api/accounts/verify/',
                {'code': otp.code, 'new_password': 'MyNewSecurePass1!'},
                HTTP_AUTHORIZATION=f'Bearer {verification_token}',
            )

        assert response.status_code == 400
        assert 'expirado' in response.json()['detail'].lower()

    def test_verify_rejects_code_after_max_failed_attempts(self, api_client, pending_client_user, mailoutbox):
        verification_token = _login_for_verification(api_client)
        otp = VerificationCode.objects.get(user=pending_client_user, is_used=False)

        api_client.post(
            '/api/accounts/verify/',
            {'code': '000000', 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )
        api_client.post(
            '/api/accounts/verify/',
            {'code': '000000', 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )
        api_client.post(
            '/api/accounts/verify/',
            {'code': '000000', 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )
        api_client.post(
            '/api/accounts/verify/',
            {'code': '000000', 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )
        api_client.post(
            '/api/accounts/verify/',
            {'code': '000000', 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )

        response = api_client.post(
            '/api/accounts/verify/',
            {'code': otp.code, 'new_password': 'MyNewSecurePass1!'},
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )

        assert response.status_code == 400
        assert 'demasiados intentos' in response.json()['detail'].lower()

    def test_resend_code_replaces_previous_active_code_for_pending_client(self, api_client, pending_client_user, mailoutbox):
        verification_token = _login_for_verification(api_client)
        first_otp = VerificationCode.objects.get(user=pending_client_user, is_used=False)
        mailoutbox.clear()

        response = api_client.post(
            '/api/accounts/resend-code/',
            HTTP_AUTHORIZATION=f'Bearer {verification_token}',
        )

        assert response.status_code == 200
        assert len(mailoutbox) == 1
        first_otp.refresh_from_db()
        replacement_otp = VerificationCode.objects.get(user=pending_client_user, is_used=False)
        assert first_otp.is_used is True
        assert replacement_otp.id != first_otp.id
