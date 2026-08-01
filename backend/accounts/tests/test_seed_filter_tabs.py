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


class TestAccountingIncomeDefaultRegistry:
    """The two expected-income tabs are what the operator triages by.

    Their names are pinned because migration 0041 renames existing rows by
    name; renaming them here without a matching migration would orphan the
    old tab on every account that already has one.
    """

    def test_income_registry_ships_both_expected_tabs(self):
        from accounts.default_filter_tabs import DEFAULT_FILTER_TABS

        assert DEFAULT_FILTER_TABS['accounting_income'][:2] == [
            {'name': 'Todos los esperados', 'filters': {'kind': 'expected'}},
            {
                'name': 'Solo esperados',
                'filters': {'kind': 'expected', 'paymentStatus': 'pending'},
            },
        ]


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


class TestIncomeExpectedTabMigration:
    """Migration 0041 splits the legacy "Esperados" tab of existing users.

    Editing the registry alone never reaches them: `seed_default_tabs` is a
    no-op once a user has any tab for the view, and `force=True` upserts by
    name — it would add the two new tabs and leave the old one orphaned.
    """

    @staticmethod
    def _migration():
        from importlib import import_module

        return import_module(
            'accounts.migrations.0041_income_expected_filter_tabs',
        )

    @staticmethod
    def _legacy_tabs(user):
        for order, (name, filters) in enumerate((
            ('Esperados', {'kind': 'expected'}),
            ('Líquidos', {'kind': 'liquid'}),
            ('Gustavo', {'partner': 'gustavo'}),
        )):
            SavedFilterTab.objects.create(
                user=user, view='accounting_income', name=name,
                filters=filters, order=order,
            )

    def _names_in_order(self, user):
        return list(
            SavedFilterTab.objects.filter(
                user=user, view='accounting_income',
            ).order_by('order', 'created_at').values_list('name', flat=True)
        )

    def test_forward_renames_and_inserts_the_new_tab_right_after(self, admin_a):
        from django.apps import apps

        self._legacy_tabs(admin_a)

        self._migration().split_expected_tab(apps, None)

        assert self._names_in_order(admin_a) == [
            'Todos los esperados', 'Solo esperados', 'Líquidos', 'Gustavo',
        ]
        new_tab = SavedFilterTab.objects.get(
            user=admin_a, name='Solo esperados',
        )
        assert new_tab.filters == {'kind': 'expected', 'paymentStatus': 'pending'}

    def test_forward_is_idempotent(self, admin_a):
        from django.apps import apps

        self._legacy_tabs(admin_a)
        migration = self._migration()

        migration.split_expected_tab(apps, None)
        migration.split_expected_tab(apps, None)

        assert self._names_in_order(admin_a) == [
            'Todos los esperados', 'Solo esperados', 'Líquidos', 'Gustavo',
        ]

    def test_forward_leaves_custom_tabs_alone(self, admin_a):
        from django.apps import apps

        self._legacy_tabs(admin_a)
        SavedFilterTab.objects.create(
            user=admin_a, view='accounting_income', name='Kore',
            filters={'search': 'kore'}, order=3,
        )

        self._migration().split_expected_tab(apps, None)

        assert self._names_in_order(admin_a)[-1] == 'Kore'

    def test_reverse_restores_the_legacy_layout(self, admin_a):
        from django.apps import apps

        self._legacy_tabs(admin_a)
        migration = self._migration()

        migration.split_expected_tab(apps, None)
        migration.merge_expected_tab(apps, None)

        assert self._names_in_order(admin_a) == [
            'Esperados', 'Líquidos', 'Gustavo',
        ]
        assert list(
            SavedFilterTab.objects.filter(
                user=admin_a, view='accounting_income',
            ).order_by('order').values_list('order', flat=True)
        ) == [0, 1, 2]
