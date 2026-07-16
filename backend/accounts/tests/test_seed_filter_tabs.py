"""
Tests para el seeding de pestañas de filtros default
(`accounts.services.saved_filter_tab_service` + auto-seed del GET).

Cubre idempotencia, no-clobber, upsert con force, tope por vista y el
auto-seed del endpoint de listado.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import SavedFilterTab, UserProfile
from accounts.services import saved_filter_tab_service
from accounts.services.saved_filter_tab_service import seed_default_tabs

User = get_user_model()

pytestmark = pytest.mark.django_db

SAMPLE_REGISTRY = {
    'client': [
        {'name': 'VIP', 'filters': {'acceptedMin': 1}},
        {'name': 'Fríos', 'filters': {'lastStatuses': ['sent']}},
    ],
}


@pytest.fixture(autouse=True)
def _sample_registry(monkeypatch):
    monkeypatch.setattr(
        saved_filter_tab_service, 'DEFAULT_FILTER_TABS', SAMPLE_REGISTRY,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_a(db):
    user = User.objects.create_user(
        username='seed-admin@test.com', email='seed-admin@test.com',
        password='staffpass1!', first_name='Seed', last_name='Admin',
        is_staff=True,
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True,
    )
    return user


@pytest.fixture
def admin_a_headers(api_client, admin_a):
    resp = api_client.post(
        '/api/accounts/login/',
        {'email': admin_a.email, 'password': 'staffpass1!'},
        format='json',
    )
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


class TestSeedDefaultTabs:
    def test_seed_creates_tabs_with_name_filters_and_order(self, admin_a):
        created, updated = seed_default_tabs(admin_a, 'client')

        assert (created, updated) == (2, 0)
        tabs = list(
            SavedFilterTab.objects.filter(user=admin_a, view='client').order_by('order'),
        )
        assert [(t.name, t.filters, t.order) for t in tabs] == [
            ('VIP', {'acceptedMin': 1}, 0),
            ('Fríos', {'lastStatuses': ['sent']}, 1),
        ]

    def test_second_seed_is_idempotent(self, admin_a):
        seed_default_tabs(admin_a, 'client')
        created, updated = seed_default_tabs(admin_a, 'client')

        assert (created, updated) == (0, 0)
        assert SavedFilterTab.objects.filter(user=admin_a, view='client').count() == 2

    def test_seed_does_not_clobber_existing_custom_tabs(self, admin_a):
        SavedFilterTab.objects.create(
            user=admin_a, view='client', name='Mío', filters={'acceptedMin': 5},
        )

        created, updated = seed_default_tabs(admin_a, 'client')

        assert (created, updated) == (0, 0)
        tabs = SavedFilterTab.objects.filter(user=admin_a, view='client')
        assert tabs.count() == 1
        assert tabs.first().filters == {'acceptedMin': 5}

    def test_force_upserts_by_name_and_preserves_extra_tabs(self, admin_a):
        SavedFilterTab.objects.create(
            user=admin_a, view='client', name='VIP', filters={'stale': True},
        )
        SavedFilterTab.objects.create(
            user=admin_a, view='client', name='Extra', filters={'acceptedMax': 9},
        )

        created, updated = seed_default_tabs(admin_a, 'client', force=True)

        assert (created, updated) == (1, 1)
        tabs = {
            t.name: t.filters
            for t in SavedFilterTab.objects.filter(user=admin_a, view='client')
        }
        assert tabs == {
            'VIP': {'acceptedMin': 1},
            'Fríos': {'lastStatuses': ['sent']},
            'Extra': {'acceptedMax': 9},
        }

    def test_seed_respects_max_tabs_per_view(self, admin_a, monkeypatch):
        big_registry = {
            'client': [
                {'name': f'Tab {i}', 'filters': {'acceptedMin': i}}
                for i in range(SavedFilterTab.MAX_TABS_PER_VIEW + 5)
            ],
        }
        monkeypatch.setattr(
            saved_filter_tab_service, 'DEFAULT_FILTER_TABS', big_registry,
        )

        created, updated = seed_default_tabs(admin_a, 'client')

        assert created == SavedFilterTab.MAX_TABS_PER_VIEW
        assert updated == 0

    def test_view_without_registry_entry_is_noop(self, admin_a):
        created, updated = seed_default_tabs(admin_a, 'proposal')

        assert (created, updated) == (0, 0)
        assert not SavedFilterTab.objects.filter(user=admin_a).exists()


class TestViewMapDefaultRegistry:
    """The real registry (not the monkeypatched sample) ships view_map tabs."""

    def test_view_map_registry_ships_expected_tabs(self):
        from accounts.default_filter_tabs import DEFAULT_FILTER_TABS

        assert DEFAULT_FILTER_TABS['view_map'] == [
            {'name': 'Admin', 'filters': {'audiences': ['admin']}},
            {'name': 'Público', 'filters': {'audiences': ['public']}},
            {'name': 'Cliente', 'filters': {'audiences': ['client']}},
            {'name': 'Dashboards', 'filters': {'viewTypes': ['dashboard']}},
            {'name': 'Configuración', 'filters': {'viewTypes': ['config']}},
        ]

    def test_view_map_is_a_valid_saved_filter_tab_view(self):
        assert 'view_map' in {choice for choice, _ in SavedFilterTab.VIEW_CHOICES}


class TestAutoSeedOnGet:
    def test_get_with_view_auto_seeds_and_returns_defaults(
        self, api_client, admin_a, admin_a_headers,
    ):
        response = api_client.get(
            '/api/accounts/saved-filter-tabs/?view=client', **admin_a_headers,
        )

        assert response.status_code == 200
        names = [tab['name'] for tab in response.json()]
        assert names == ['VIP', 'Fríos']

    def test_get_without_view_does_not_seed(
        self, api_client, admin_a, admin_a_headers,
    ):
        response = api_client.get(
            '/api/accounts/saved-filter-tabs/', **admin_a_headers,
        )

        assert response.status_code == 200
        assert response.json() == []
        assert not SavedFilterTab.objects.filter(user=admin_a).exists()
