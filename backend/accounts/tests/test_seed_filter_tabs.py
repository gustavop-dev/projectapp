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

    def test_force_upserts_the_seeded_tabs_and_preserves_extra_ones(
        self, admin_a,
    ):
        stale = SavedFilterTab.objects.create(
            user=admin_a, view='client', name='VIP', filters={'stale': True},
            is_seeded=True,
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
        stale.refresh_from_db()
        assert stale.is_seeded is True

    def test_force_does_not_rewrite_a_user_tab_sharing_a_factory_name(
        self, admin_a,
    ):
        """Only the seeded rows are upserted.

        Matching by name alone would let re-seeding silently replace the cut
        a user saved just because they picked the same word for it.
        """
        mine = SavedFilterTab.objects.create(
            user=admin_a, view='client', name='VIP', filters={'acceptedMax': 3},
        )

        created, updated = seed_default_tabs(admin_a, 'client', force=True)

        assert (created, updated) == (2, 0)
        mine.refresh_from_db()
        assert mine.filters == {'acceptedMax': 3}
        assert mine.is_seeded is False

    def test_seed_populates_base_filters_as_restore_point(self, admin_a):
        seed_default_tabs(admin_a, 'client')

        bases = {
            t.name: t.base_filters
            for t in SavedFilterTab.objects.filter(user=admin_a, view='client')
        }
        assert bases == {
            'VIP': {'acceptedMin': 1},
            'Fríos': {'lastStatuses': ['sent']},
        }

    def test_force_reseed_restores_base_after_drift(self, admin_a):
        seed_default_tabs(admin_a, 'client')
        drifted = SavedFilterTab.objects.get(
            user=admin_a, view='client', name='VIP',
        )
        drifted.filters = {'acceptedMin': 99}
        drifted.base_filters = {'acceptedMin': 99}
        drifted.save()

        created, updated = seed_default_tabs(admin_a, 'client', force=True)

        assert (created, updated) == (0, 1)
        drifted.refresh_from_db()
        assert drifted.filters == {'acceptedMin': 1}
        assert drifted.base_filters == {'acceptedMin': 1}

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
    """The expected-income tab is what the operator triages by.

    Its name is pinned because migrations 0041 and 0043 match existing rows by
    name; renaming it here without a matching migration would orphan the old
    tab on every account that already has one.
    """

    def test_income_registry_ships_the_all_expected_tab_first(self):
        from accounts.default_filter_tabs import DEFAULT_FILTER_TABS

        assert DEFAULT_FILTER_TABS['accounting_income'][0] == {
            'name': 'Todos los esperados', 'filters': {'kind': 'expected'},
        }

    def test_income_registry_no_longer_seeds_the_builtin_cut(self):
        """"Solo esperados" is a builtin tab in incomes.vue now.

        Seeding it as well would render two identically named tabs, and a
        saved one would be silently rewritten by any filter tweak — which the
        landing tab must never be.
        """
        from accounts.default_filter_tabs import DEFAULT_FILTER_TABS

        names = [spec['name'] for spec in DEFAULT_FILTER_TABS['accounting_income']]
        assert 'Solo esperados' not in names


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


class TestBaseFiltersBackfillMigration:
    """Migration 0042 gives pre-existing tabs their restore point.

    Rows created before the field existed carry ``base_filters={}``; the
    backfill must recover the registry definition for seeded names even when
    the live filters drifted (the panel auto-saves onto the active tab), and
    fall back to the tab's own filters for custom names.
    """

    @staticmethod
    def _migration():
        from importlib import import_module

        return import_module(
            'accounts.migrations.0042_savedfiltertab_base_filters',
        )

    def test_backfill_recovers_registry_definition_for_seeded_names(self, admin_a):
        from django.apps import apps

        drifted = SavedFilterTab.objects.create(
            user=admin_a, view='accounting_income', name='Todos los esperados',
            filters={'kind': 'expected', 'paymentStatus': 'pending'},
        )

        self._migration().backfill_base_filters(apps, None)

        drifted.refresh_from_db()
        assert drifted.base_filters == {'kind': 'expected'}

    def test_backfill_copies_own_filters_for_custom_names(self, admin_a):
        from django.apps import apps

        custom = SavedFilterTab.objects.create(
            user=admin_a, view='accounting_income', name='Mi vista',
            filters={'partner': 'gustavo'}, order=1,
        )

        self._migration().backfill_base_filters(apps, None)

        custom.refresh_from_db()
        assert custom.base_filters == {'partner': 'gustavo'}


class TestDropOnlyExpectedTabMigration:
    """Migration 0043 retires the saved "Solo esperados" of existing users.

    It became a builtin tab in the frontend; leaving the seeded row in place
    would show the same name twice on every account created before the change.
    """

    @staticmethod
    def _migration():
        from importlib import import_module

        return import_module(
            'accounts.migrations.0043_drop_solo_esperados_tab',
        )

    @staticmethod
    def _seeded_tabs(user):
        for order, (name, filters) in enumerate((
            ('Todos los esperados', {'kind': 'expected'}),
            ('Solo esperados', {'kind': 'expected', 'paymentStatus': 'pending'}),
            ('Líquidos', {'kind': 'liquid'}),
            ('Gustavo', {'partner': 'gustavo'}),
        )):
            SavedFilterTab.objects.create(
                user=user, view='accounting_income', name=name,
                filters=filters, base_filters=filters, order=order,
            )

    def _tabs_in_order(self, user):
        return list(
            SavedFilterTab.objects.filter(
                user=user, view='accounting_income',
            ).order_by('order', 'created_at').values_list('name', 'order')
        )

    def test_forward_removes_the_tab_and_closes_the_order_gap(self, admin_a):
        from django.apps import apps

        self._seeded_tabs(admin_a)

        self._migration().drop_only_expected_tab(apps, None)

        assert self._tabs_in_order(admin_a) == [
            ('Todos los esperados', 0), ('Líquidos', 1), ('Gustavo', 2),
        ]

    def test_forward_is_idempotent(self, admin_a):
        from django.apps import apps

        self._seeded_tabs(admin_a)
        migration = self._migration()

        migration.drop_only_expected_tab(apps, None)
        migration.drop_only_expected_tab(apps, None)

        assert self._tabs_in_order(admin_a) == [
            ('Todos los esperados', 0), ('Líquidos', 1), ('Gustavo', 2),
        ]

    def test_forward_leaves_other_views_alone(self, admin_a):
        from django.apps import apps

        kept = SavedFilterTab.objects.create(
            user=admin_a, view='accounting_expense', name='Solo esperados',
            filters={'ledger': 'company'}, order=0,
        )

        self._migration().drop_only_expected_tab(apps, None)

        assert SavedFilterTab.objects.filter(pk=kept.pk).exists()

    def test_reverse_restores_the_tab_right_after_its_anchor(self, admin_a):
        from django.apps import apps

        self._seeded_tabs(admin_a)
        migration = self._migration()

        migration.drop_only_expected_tab(apps, None)
        migration.restore_only_expected_tab(apps, None)

        assert self._tabs_in_order(admin_a) == [
            ('Todos los esperados', 0), ('Solo esperados', 1),
            ('Líquidos', 2), ('Gustavo', 3),
        ]
        restored = SavedFilterTab.objects.get(
            user=admin_a, view='accounting_income', name='Solo esperados',
        )
        assert restored.filters == {'kind': 'expected', 'paymentStatus': 'pending'}
        assert restored.base_filters == restored.filters
