"""Communications panel preference endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import CommunicationPanelPreference, UserProfile


pytestmark = pytest.mark.django_db

PREFERENCES_URL = '/api/accounts/panel-preferences/communications/'
RESET_URL = '/api/accounts/panel-preferences/communications/reset/'


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


def expected_defaults(**overrides):
    return {
        **CommunicationPanelPreference.defaults(),
        'legacy_import_allowed': False,
        **overrides,
    }


def test_get_returns_defaults_for_a_new_account():
    admin = make_admin('communications-default@test.com')

    response = authenticated_client(admin).get(PREFERENCES_URL)

    assert response.status_code == 200
    assert response.json() == expected_defaults(legacy_import_allowed=True)


def test_second_get_disables_legacy_import():
    admin = make_admin('communications-existing@test.com')
    client = authenticated_client(admin)
    client.get(PREFERENCES_URL)

    response = client.get(PREFERENCES_URL)

    assert response.status_code == 200
    assert response.json()['legacy_import_allowed'] is False


def test_patch_persists_a_partial_preference():
    admin = make_admin('communications-patch@test.com')
    client = authenticated_client(admin)

    response = client.patch(
        PREFERENCES_URL,
        {'navigation_mode': 'client', 'page_size': 50},
        format='json',
    )

    assert response.status_code == 200
    assert response.json() == expected_defaults(
        navigation_mode='client', page_size=50,
    )
    preference = CommunicationPanelPreference.objects.get(user=admin)
    assert preference.navigation_mode == 'client'
    assert preference.page_size == 50


@pytest.mark.parametrize(
    ('payload', 'field'),
    [
        ({'navigation_mode': 'folder'}, 'navigation_mode'),
        ({'thread_order': 'priority'}, 'thread_order'),
        ({'page_size': 100}, 'page_size'),
        ({'default_channel': 'sms'}, 'default_channel'),
        ({'navigation_width': 401}, 'navigation_width'),
    ],
)
def test_patch_rejects_an_invalid_preference(payload, field):
    admin = make_admin(f'communications-invalid-{field}@test.com')

    response = authenticated_client(admin).patch(
        PREFERENCES_URL,
        payload,
        format='json',
    )

    assert response.status_code == 400
    assert field in response.json()


def test_preferences_are_isolated_by_account():
    first = make_admin('communications-first@test.com')
    second = make_admin('communications-second@test.com')
    authenticated_client(first).patch(
        PREFERENCES_URL,
        {'default_channel': 'email'},
        format='json',
    )

    response = authenticated_client(second).get(PREFERENCES_URL)

    assert response.json()['default_channel'] == 'whatsapp'


def test_reset_restores_every_default():
    admin = make_admin('communications-reset@test.com')
    client = authenticated_client(admin)
    client.patch(
        PREFERENCES_URL,
        {
            'navigation_mode': 'client',
            'thread_order': 'title',
            'page_size': 10,
            'default_channel': 'email',
            'show_manual_help': False,
            'navigation_width': 400,
        },
        format='json',
    )

    response = client.post(RESET_URL, {}, format='json')

    assert response.status_code == 200
    assert response.json() == expected_defaults()


def test_preferences_require_a_staff_account():
    user = get_user_model().objects.create_user(
        username='communications-client@test.com',
        email='communications-client@test.com',
        password='clientpass1!',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

    response = authenticated_client(user).get(PREFERENCES_URL)

    assert response.status_code == 403
