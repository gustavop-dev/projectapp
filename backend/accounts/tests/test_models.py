import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time

from accounts.models import UserProfile, VerificationCode

User = get_user_model()


@pytest.mark.django_db
class TestUserProfile:
    def test_create_admin_profile(self):
        user = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass1234')
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)

        assert profile.is_admin is True
        assert profile.is_client is False
        assert profile.is_onboarded is True
        assert str(profile) == 'admin@test.com (Admin)'

    def test_create_client_profile(self):
        user = User.objects.create_user(username='client@test.com', email='client@test.com', password='pass1234')
        profile = UserProfile.objects.create(
            user=user, role=UserProfile.ROLE_CLIENT,
            company_name='Acme Corp', phone='+57 300 111 2222',
        )

        assert profile.is_client is True
        assert profile.is_admin is False
        assert profile.is_onboarded is False
        assert profile.company_name == 'Acme Corp'

    def test_profile_default_role_is_client(self):
        user = User.objects.create_user(username='new@test.com', email='new@test.com', password='pass1234')
        profile = UserProfile.objects.create(user=user)

        assert profile.role == UserProfile.ROLE_CLIENT

    def test_created_by_tracks_admin(self):
        admin_user = User.objects.create_user(username='admin@t.com', email='admin@t.com', password='p')
        client_user = User.objects.create_user(username='client@t.com', email='client@t.com', password='p')
        profile = UserProfile.objects.create(user=client_user, created_by=admin_user)

        assert profile.created_by == admin_user


@pytest.mark.django_db
class TestVerificationCode:
    def _make_user(self, email='user@test.com'):
        return User.objects.create_user(username=email, email=email, password='pass1234')

    def test_generate_code_returns_six_digits(self):
        code = VerificationCode.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_create_for_user_invalidates_previous(self):
        user = self._make_user()
        first = VerificationCode.create_for_user(user)
        second = VerificationCode.create_for_user(user)

        first.refresh_from_db()
        assert first.is_used is True
        assert second.is_used is False
        assert second.is_valid is True

    def test_is_valid_when_fresh(self):
        user = self._make_user()
        otp = VerificationCode.create_for_user(user)

        assert otp.is_valid is True
        assert otp.is_expired is False

    @freeze_time("2025-01-01 12:00:00")
    def test_is_expired_after_expiry(self):
        user = self._make_user()
        otp = VerificationCode.create_for_user(user)

        with freeze_time("2025-01-01 12:11:00"):
            assert otp.is_expired is True
            assert otp.is_valid is False

    def test_max_attempts_reached(self):
        user = self._make_user()
        otp = VerificationCode.create_for_user(user)
        otp.attempts = VerificationCode.MAX_ATTEMPTS
        otp.save()

        assert otp.is_valid is False

    def test_mark_used(self):
        user = self._make_user()
        otp = VerificationCode.create_for_user(user)
        otp.mark_used()

        assert otp.is_used is True
        assert otp.is_valid is False

    def test_increment_attempts(self):
        user = self._make_user()
        otp = VerificationCode.create_for_user(user)
        otp.increment_attempts()

        assert otp.attempts == 1
