"""Auth tests for the accounting module gate.

Covers the extended check_admin_auth payload (is_superuser) and the
IsSuperUser permission class. Endpoint-level 403 coverage for the
accounting API lives here too (added with the views).
"""
import pytest

from content.permissions import IsSuperUser


@pytest.mark.django_db
class TestCheckAdminAuthPayload:
    def test_anonymous_is_rejected(self, api_client):
        response = api_client.get('/api/auth/check/')
        assert response.status_code in (401, 403)

    def test_non_staff_is_rejected(self, api_client, django_user_model):
        user = django_user_model.objects.create_user(
            username='plain', password='x',
        )
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/auth/check/')
        assert response.status_code == 403

    def test_staff_gets_is_superuser_false(self, admin_client):
        response = admin_client.get('/api/auth/check/')
        assert response.status_code == 200
        assert response.data['user']['is_staff'] is True
        assert response.data['user']['is_superuser'] is False

    def test_superuser_gets_is_superuser_true(self, super_client):
        response = super_client.get('/api/auth/check/')
        assert response.status_code == 200
        assert response.data['user']['is_superuser'] is True

    def test_payload_keeps_backward_compatible_fields(self, admin_client):
        response = admin_client.get('/api/auth/check/')
        assert set(response.data['user'].keys()) == {
            'username', 'is_staff', 'is_superuser',
        }


class TestIsSuperUserPermission:
    def _request_for(self, user):
        class _Request:
            pass

        request = _Request()
        request.user = user
        return request

    def test_denies_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        assert not IsSuperUser().has_permission(
            self._request_for(AnonymousUser()), view=None,
        )

    @pytest.mark.django_db
    def test_denies_staff_non_superuser(self, admin_user):
        assert not IsSuperUser().has_permission(
            self._request_for(admin_user), view=None,
        )

    @pytest.mark.django_db
    def test_allows_superuser(self, superuser):
        assert IsSuperUser().has_permission(
            self._request_for(superuser), view=None,
        )
