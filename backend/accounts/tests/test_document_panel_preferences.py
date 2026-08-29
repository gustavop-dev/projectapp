"""Document-manager navigation preference endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import UserProfile


pytestmark = pytest.mark.django_db

PREFERENCES_URL = '/api/accounts/panel-preferences/documents/'


def make_admin(email):
    user = get_user_model().objects.create_user(
        username=email,
        email=email,
        password='staffpass1!',
        is_staff=True,
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN)
    return user


def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_get_returns_project_as_the_default_mode():
    admin = make_admin('documents-default@test.com')

    response = authenticated_client(admin).get(PREFERENCES_URL)

    assert response.status_code == 200
    assert response.json() == {'navigation_mode': 'project'}


def test_patch_persists_client_mode_for_the_account():
    admin = make_admin('documents-client@test.com')
    client = authenticated_client(admin)

    response = client.patch(
        PREFERENCES_URL,
        {'navigation_mode': 'client'},
        format='json',
    )

    assert response.status_code == 200
    assert response.json() == {'navigation_mode': 'client'}
    admin.profile.refresh_from_db()
    assert admin.profile.document_navigation_mode == 'client'
    assert client.get(PREFERENCES_URL).json() == {'navigation_mode': 'client'}


def test_patch_rejects_an_unknown_mode_without_changing_the_preference():
    admin = make_admin('documents-invalid@test.com')

    response = authenticated_client(admin).patch(
        PREFERENCES_URL,
        {'navigation_mode': 'folder'},
        format='json',
    )

    assert response.status_code == 400
    admin.profile.refresh_from_db()
    assert admin.profile.document_navigation_mode == 'project'


def test_preferences_require_a_staff_account():
    user = get_user_model().objects.create_user(
        username='documents-client-user@test.com',
        email='documents-client-user@test.com',
        password='clientpass1!',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

    response = authenticated_client(user).get(PREFERENCES_URL)

    assert response.status_code == 403
