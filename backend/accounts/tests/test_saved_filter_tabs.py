"""
Tests para los endpoints de pestañas de filtros guardados del panel
(`/api/accounts/saved-filter-tabs/`).

Cubre CRUD, validación del límite por vista, aislamiento entre usuarios
y rechazo de no-admin.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import SavedFilterTab, UserProfile
from accounts.services import saved_filter_tab_service

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _blank_default_filter_tabs(monkeypatch):
    """Keep legacy CRUD behavior deterministic: GET auto-seeds from the
    registry, so these tests run against an empty one.

    Both registries are blanked. A GET also materialises one placeholder row
    per builtin quick-filter, and that is just as much of a surprise row for
    a test that counts what a view gives back."""
    monkeypatch.setattr(saved_filter_tab_service, 'DEFAULT_FILTER_TABS', {})
    monkeypatch.setattr(saved_filter_tab_service, 'BUILTIN_FILTER_TABS', {})


@pytest.fixture
def api_client():
    return APIClient()


def _make_staff_admin(email, password='staffpass1!'):
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name='Staff', last_name='Admin', is_staff=True,
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True,
    )
    return user


def _auth_headers(api_client, email, password='staffpass1!'):
    resp = api_client.post(
        '/api/accounts/login/',
        {'email': email, 'password': password},
        format='json',
    )
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def admin_a(db):
    return _make_staff_admin('sft-admin-a@test.com')


@pytest.fixture
def admin_a_headers(api_client, admin_a):
    return _auth_headers(api_client, admin_a.email)


@pytest.fixture
def admin_b(db):
    return _make_staff_admin('sft-admin-b@test.com')


@pytest.fixture
def admin_b_headers(api_client, admin_b):
    return _auth_headers(api_client, admin_b.email)


@pytest.fixture
def client_user(db):
    user = User.objects.create_user(
        username='sft-client@test.com', email='sft-client@test.com',
        password='clientpass1!',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    return _auth_headers(api_client, client_user.email, password='clientpass1!')


# ---------------------------------------------------------------------------
# GET — listing
# ---------------------------------------------------------------------------

def test_get_empty_returns_empty_list(api_client, admin_a_headers):
    resp = api_client.get('/api/accounts/saved-filter-tabs/', **admin_a_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_filters_by_view(api_client, admin_a, admin_a_headers):
    SavedFilterTab.objects.create(user=admin_a, view='proposal', name='P1', filters={'a': 1})
    SavedFilterTab.objects.create(user=admin_a, view='client', name='C1', filters={'b': 2})

    resp = api_client.get('/api/accounts/saved-filter-tabs/?view=proposal', **admin_a_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]['view'] == 'proposal'
    assert data[0]['name'] == 'P1'


# ---------------------------------------------------------------------------
# POST — create
# ---------------------------------------------------------------------------

def test_post_accepts_the_accounting_cards_view(api_client, admin_a, admin_a_headers):
    """Cards saves custom tabs like every accounting view; the choice was
    missing from VIEW_CHOICES and every save attempt on that page 400ed."""
    payload = {
        'view': 'accounting_cards', 'name': 'Solo 0064',
        'filters': {'cardName': ['T.C 0064']},
    }
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/', payload, format='json', **admin_a_headers,
    )
    assert resp.status_code == 201
    assert resp.json()['view'] == 'accounting_cards'


def test_post_creates_tab(api_client, admin_a, admin_a_headers):
    payload = {'view': 'proposal', 'name': 'Activos', 'filters': {'statuses': ['active']}}
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/', payload, format='json', **admin_a_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body['id'] > 0
    assert body['view'] == 'proposal'
    assert body['name'] == 'Activos'
    assert body['filters'] == {'statuses': ['active']}
    assert SavedFilterTab.objects.filter(user=admin_a, name='Activos').exists()


def test_post_invalid_view_returns_400(api_client, admin_a_headers):
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {'view': 'bogus', 'name': 'X', 'filters': {}},
        format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 400
    assert 'view' in resp.json()


def test_post_enforces_max_tabs_per_view(api_client, admin_a, admin_a_headers):
    for i in range(SavedFilterTab.MAX_TABS_PER_VIEW):
        SavedFilterTab.objects.create(
            user=admin_a, view='proposal', name=f'tab{i}', filters={},
        )
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {'view': 'proposal', 'name': 'overflow', 'filters': {}},
        format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 400
    assert 'view' in resp.json()
    # Otra vista no se ve afectada por el límite de proposal.
    resp2 = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {'view': 'client', 'name': 'ok', 'filters': {}},
        format='json',
        **admin_a_headers,
    )
    assert resp2.status_code == 201


# ---------------------------------------------------------------------------
# PATCH — update
# ---------------------------------------------------------------------------

def test_patch_updates_fields(api_client, admin_a, admin_a_headers):
    tab = SavedFilterTab.objects.create(
        user=admin_a, view='proposal', name='Old', filters={'x': 1}, order=0,
    )
    resp = api_client.patch(
        f'/api/accounts/saved-filter-tabs/{tab.id}/',
        {'name': 'New', 'filters': {'x': 2}, 'order': 5},
        format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['name'] == 'New'
    assert body['filters'] == {'x': 2}
    assert body['order'] == 5


def test_patch_not_owner_returns_404(api_client, admin_b, admin_a_headers):
    other_tab = SavedFilterTab.objects.create(
        user=admin_b, view='proposal', name='B-tab', filters={},
    )
    resp = api_client.patch(
        f'/api/accounts/saved-filter-tabs/{other_tab.id}/',
        {'name': 'hijack'},
        format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def test_delete_removes_tab(api_client, admin_a, admin_a_headers):
    tab = SavedFilterTab.objects.create(
        user=admin_a, view='proposal', name='Del', filters={},
    )
    resp = api_client.delete(
        f'/api/accounts/saved-filter-tabs/{tab.id}/', **admin_a_headers,
    )
    assert resp.status_code == 204
    assert not SavedFilterTab.objects.filter(id=tab.id).exists()


def test_delete_not_owner_returns_404(api_client, admin_b, admin_a_headers):
    other_tab = SavedFilterTab.objects.create(
        user=admin_b, view='proposal', name='B-tab', filters={},
    )
    resp = api_client.delete(
        f'/api/accounts/saved-filter-tabs/{other_tab.id}/', **admin_a_headers,
    )
    assert resp.status_code == 404
    assert SavedFilterTab.objects.filter(id=other_tab.id).exists()


# ---------------------------------------------------------------------------
# Aislamiento y permisos
# ---------------------------------------------------------------------------

def test_get_lists_only_own_tabs(api_client, admin_a, admin_b, admin_a_headers):
    SavedFilterTab.objects.create(user=admin_a, view='proposal', name='mine', filters={})
    SavedFilterTab.objects.create(user=admin_b, view='proposal', name='theirs', filters={})

    resp = api_client.get('/api/accounts/saved-filter-tabs/', **admin_a_headers)
    assert resp.status_code == 200
    names = [tab['name'] for tab in resp.json()]
    assert names == ['mine']


def test_non_admin_client_is_forbidden(api_client, client_headers):
    resp = api_client.get('/api/accounts/saved-filter-tabs/', **client_headers)
    assert resp.status_code == 403


def test_anonymous_is_unauthorized(api_client):
    resp = api_client.get('/api/accounts/saved-filter-tabs/')
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# POST reset/ — restore a view's default tabs
# ---------------------------------------------------------------------------

RESET_URL = '/api/accounts/saved-filter-tabs/reset/'


@pytest.fixture
def _accounting_registry(monkeypatch):
    """Small controlled registry (overrides the blank autouse one)."""
    registry = {
        'accounting_income': [
            {'name': 'Esperados', 'filters': {'kind': 'expected'}},
            {'name': 'Líquidos', 'filters': {'kind': 'liquid'}},
        ],
    }
    monkeypatch.setattr(
        saved_filter_tab_service, 'DEFAULT_FILTER_TABS', registry,
    )
    return registry


def test_reset_restores_factory_tabs_and_keeps_the_custom_ones(
    api_client, admin_a, admin_a_headers, _accounting_registry,
):
    custom = SavedFilterTab.objects.create(
        user=admin_a, view='accounting_income', name='Custom',
        filters={'kind': 'liquid'},
    )
    seeded = SavedFilterTab.objects.create(
        user=admin_a, view='accounting_income', name='Esperados',
        filters={'kind': 'tampered'}, is_seeded=True,
    )

    resp = api_client.post(
        RESET_URL, {'view': 'accounting_income'}, format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    names = [tab['name'] for tab in resp.json()]
    assert 'Custom' in names
    assert {'Esperados', 'Líquidos'} <= set(names)
    custom.refresh_from_db()
    assert custom.filters == {'kind': 'liquid'}
    # The seeded row is rebuilt from the registry, so the edited filters go.
    assert not SavedFilterTab.objects.filter(pk=seeded.pk).exists()
    assert SavedFilterTab.objects.get(
        user=admin_a, view='accounting_income', name='Esperados',
    ).filters == {'kind': 'expected'}


def test_reset_leaves_a_user_tab_named_like_a_factory_one_alone(
    api_client, admin_a, admin_a_headers, _accounting_registry,
):
    """A name collision must not cost the user their filters.

    Reset restores the factory tab beside theirs rather than overwriting it;
    two rows share the name until the operator renames one, which is visible
    and undoable, unlike silently losing a saved cut.
    """
    mine = SavedFilterTab.objects.create(
        user=admin_a, view='accounting_income', name='Esperados',
        filters={'partner': 'carlos'},
    )

    resp = api_client.post(
        RESET_URL, {'view': 'accounting_income'}, format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    mine.refresh_from_db()
    assert mine.filters == {'partner': 'carlos'}
    assert mine.is_seeded is False
    assert SavedFilterTab.objects.filter(
        user=admin_a, view='accounting_income', name='Esperados',
    ).count() == 2


def test_reset_invalid_view_returns_400(api_client, admin_a_headers):
    resp = api_client.post(
        RESET_URL, {'view': 'nope'}, format='json', **admin_a_headers,
    )
    assert resp.status_code == 400


def test_reset_only_affects_the_caller(
    api_client, admin_a, admin_b, admin_a_headers, _accounting_registry,
):
    other_tab = SavedFilterTab.objects.create(
        user=admin_b, view='accounting_income', name='De B', filters={},
    )
    api_client.post(
        RESET_URL, {'view': 'accounting_income'}, format='json',
        **admin_a_headers,
    )
    assert SavedFilterTab.objects.filter(pk=other_tab.pk).exists()


def test_reset_view_without_defaults_keeps_the_user_tab(
    api_client, admin_a, admin_a_headers, _accounting_registry,
):
    """Nothing to restore is not a licence to wipe what the user saved."""
    SavedFilterTab.objects.create(
        user=admin_a, view='accounting_history', name='Vieja', filters={},
    )
    resp = api_client.post(
        RESET_URL, {'view': 'accounting_history'}, format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 200
    assert [tab['name'] for tab in resp.json()] == ['Vieja']


def test_real_registry_covers_accounting_views():
    from accounts.default_filter_tabs import DEFAULT_FILTER_TABS

    expected_views = [
        'accounting_income', 'accounting_expense', 'accounting_hosting',
        'accounting_pocket', 'accounting_recurring', 'accounting_ads',
        'accounting_history_sends', 'accounting_history_changes',
    ]
    for view in expected_views:
        tabs = DEFAULT_FILTER_TABS.get(view)
        assert tabs, f'registry sin defaults para {view}'
        assert len(tabs) <= SavedFilterTab.MAX_TABS_PER_VIEW
        names = [tab['name'] for tab in tabs]
        assert len(names) == len(set(names))


def test_post_defaults_base_filters_to_filters(api_client, admin_a, admin_a_headers):
    payload = {
        'view': 'proposal', 'name': 'Con base implícita',
        'filters': {'statuses': ['active']},
    }
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/', payload, format='json', **admin_a_headers,
    )
    assert resp.status_code == 201
    assert resp.json()['base_filters'] == {'statuses': ['active']}
    tab = SavedFilterTab.objects.get(user=admin_a, name='Con base implícita')
    assert tab.base_filters == {'statuses': ['active']}


def test_post_accepts_explicit_base_filters(api_client, admin_a, admin_a_headers):
    payload = {
        'view': 'proposal', 'name': 'Con base explícita',
        'filters': {'statuses': ['active']},
        'base_filters': {'statuses': ['draft']},
    }
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/', payload, format='json', **admin_a_headers,
    )
    assert resp.status_code == 201
    assert resp.json()['base_filters'] == {'statuses': ['draft']}


def test_patch_base_filters_rebases_without_touching_filters(
    api_client, admin_a, admin_a_headers,
):
    tab = SavedFilterTab.objects.create(
        user=admin_a, view='proposal', name='Mi tab',
        filters={'statuses': ['sent']},
        base_filters={'statuses': ['draft']},
        order=0,
    )
    resp = api_client.patch(
        f'/api/accounts/saved-filter-tabs/{tab.id}/',
        {'base_filters': {'statuses': ['sent']}},
        format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 200
    tab.refresh_from_db()
    assert tab.base_filters == {'statuses': ['sent']}
    assert tab.filters == {'statuses': ['sent']}


# ---------------------------------------------------------------------------
# Strip administration: order and visibility
# ---------------------------------------------------------------------------

REORDER_URL = '/api/accounts/saved-filter-tabs/reorder/'


def test_reorder_applies_the_given_sequence(
    api_client, admin_a, admin_a_headers,
):
    first, second, third = [
        SavedFilterTab.objects.create(
            user=admin_a, view='proposal', name=name, filters={}, order=idx,
        )
        for idx, name in enumerate(['Uno', 'Dos', 'Tres'])
    ]

    resp = api_client.post(
        REORDER_URL,
        {'view': 'proposal', 'ids': [third.id, first.id, second.id]},
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    assert [tab['name'] for tab in resp.json()] == ['Tres', 'Uno', 'Dos']


def test_reorder_ignores_tabs_of_another_user(
    api_client, admin_a, admin_b, admin_a_headers,
):
    mine = SavedFilterTab.objects.create(
        user=admin_a, view='proposal', name='Mía', filters={}, order=5,
    )
    theirs = SavedFilterTab.objects.create(
        user=admin_b, view='proposal', name='Suya', filters={}, order=9,
    )

    resp = api_client.post(
        REORDER_URL,
        {'view': 'proposal', 'ids': [theirs.id, mine.id]},
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    theirs.refresh_from_db()
    assert theirs.order == 9
    mine.refresh_from_db()
    assert mine.order == 1


def test_reorder_rejects_a_non_list_of_ids(
    api_client, admin_a, admin_a_headers,
):
    resp = api_client.post(
        REORDER_URL, {'view': 'proposal', 'ids': 'nope'}, format='json',
        **admin_a_headers,
    )
    assert resp.status_code == 400


def test_hiding_a_tab_keeps_it_stored(api_client, admin_a, admin_a_headers):
    tab = SavedFilterTab.objects.create(
        user=admin_a, view='proposal', name='De temporada',
        filters={'statuses': ['sent']},
    )

    resp = api_client.patch(
        f'/api/accounts/saved-filter-tabs/{tab.id}/',
        {'is_hidden': True}, format='json', **admin_a_headers,
    )

    assert resp.status_code == 200
    tab.refresh_from_db()
    assert tab.is_hidden is True
    assert tab.filters == {'statuses': ['sent']}


def test_is_seeded_cannot_be_claimed_from_the_panel(
    api_client, admin_a, admin_a_headers,
):
    """Otherwise a user's tab could pass as a factory one and be wiped by
    the next reset."""
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {
            'view': 'proposal', 'name': 'Impostora', 'filters': {},
            'is_seeded': True,
        },
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 201
    assert SavedFilterTab.objects.get(id=resp.json()['id']).is_seeded is False


def test_history_subtabs_are_separate_views(
    api_client, admin_a, admin_a_headers,
):
    """A cut saved over the send log must not surface in the change log."""
    SavedFilterTab.objects.create(
        user=admin_a, view=SavedFilterTab.VIEW_ACCOUNTING_HISTORY_SENDS,
        name='Fallidos de hoy', filters={'status': ['failed']},
    )

    resp = api_client.get(
        '/api/accounts/saved-filter-tabs/'
        f'?view={SavedFilterTab.VIEW_ACCOUNTING_HISTORY_CHANGES}',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    assert [tab['name'] for tab in resp.json()] == []


# ---------------------------------------------------------------------------
# Builtin placeholders: the rows that let a code-level quick-filter be
# dragged and hidden like any other chip, without ever storing its filters.
# ---------------------------------------------------------------------------

COLLECTIONS = SavedFilterTab.VIEW_ACCOUNTING_COLLECTIONS


@pytest.fixture
def _builtin_registry(monkeypatch):
    """Controlled builtin registry (overrides the blank autouse one)."""
    registry = {
        'accounting_income': [
            {'key': 'expected-pending', 'name': 'Solo esperados'},
            {'key': 'lost', 'name': 'Perdidos'},
        ],
        # A view with builtins and NO seeded defaults — the shape that used
        # to fall through the early return in seed_default_tabs.
        COLLECTIONS: [
            {'key': 'open', 'name': 'Por cobrar'},
            {'key': 'overdue', 'name': 'Vencidas'},
        ],
    }
    monkeypatch.setattr(
        saved_filter_tab_service, 'BUILTIN_FILTER_TABS', registry,
    )
    return registry


def _get_view(api_client, headers, view):
    return api_client.get(
        f'/api/accounts/saved-filter-tabs/?view={view}', **headers,
    )


def test_get_seeds_a_placeholder_per_builtin_carrying_no_filters(
    api_client, admin_a, admin_a_headers, _builtin_registry,
):
    resp = _get_view(api_client, admin_a_headers, COLLECTIONS)

    assert resp.status_code == 200
    rows = resp.json()
    assert [r['builtin_key'] for r in rows] == ['open', 'overdue']
    assert [r['order'] for r in rows] == [0, 1]
    # The whole point: the definition stays in the frontend, so a date-based
    # builtin cannot freeze on the day it was seeded.
    assert all(r['filters'] == {} for r in rows)


def test_get_seeds_builtins_for_a_view_without_factory_defaults(
    api_client, admin_a, admin_a_headers, _builtin_registry,
):
    """Cuentas de cobro has builtins but no seeded tabs at all."""
    _get_view(api_client, admin_a_headers, COLLECTIONS)

    assert SavedFilterTab.objects.filter(
        user=admin_a, view=COLLECTIONS,
    ).exclude(builtin_key='').count() == 2


def test_seeding_builtins_is_idempotent_and_keeps_a_moved_order(
    api_client, admin_a, admin_a_headers, _builtin_registry,
):
    _get_view(api_client, admin_a_headers, COLLECTIONS)
    moved = SavedFilterTab.objects.get(
        user=admin_a, view=COLLECTIONS, builtin_key='overdue',
    )
    moved.order = 7
    moved.save(update_fields=['order'])

    _get_view(api_client, admin_a_headers, COLLECTIONS)

    assert SavedFilterTab.objects.filter(
        user=admin_a, view=COLLECTIONS,
    ).count() == 2
    moved.refresh_from_db()
    assert moved.order == 7


def test_factory_tabs_still_seed_when_builtins_already_hold_rows(
    api_client, admin_a, admin_a_headers, _builtin_registry,
    _accounting_registry,
):
    """The placeholders must not read as "this user already has tabs here"."""
    resp = _get_view(api_client, admin_a_headers, 'accounting_income')

    names = [r['name'] for r in resp.json()]
    assert names == ['Solo esperados', 'Perdidos', 'Esperados', 'Líquidos']


def test_reorder_moves_a_builtin_among_the_saved_ones(
    api_client, admin_a, admin_a_headers, _builtin_registry,
    _accounting_registry,
):
    """Punto 4 de la ficha: los de fábrica se reordenan junto a los propios."""
    _get_view(api_client, admin_a_headers, 'accounting_income')
    by_label = {
        row.builtin_key or row.name: row.id
        for row in SavedFilterTab.objects.filter(
            user=admin_a, view='accounting_income',
        )
    }

    resp = api_client.post(
        REORDER_URL,
        {
            'view': 'accounting_income',
            'ids': [
                by_label['Líquidos'], by_label['lost'],
                by_label['expected-pending'], by_label['Esperados'],
            ],
        },
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 200
    assert [r['name'] for r in resp.json()] == [
        'Líquidos', 'Perdidos', 'Solo esperados', 'Esperados',
    ]


def test_reset_returns_the_builtins_to_the_factory_order_and_unhides_them(
    api_client, admin_a, admin_a_headers, _builtin_registry,
):
    _get_view(api_client, admin_a_headers, COLLECTIONS)
    mine = SavedFilterTab.objects.create(
        user=admin_a, view=COLLECTIONS, name='Mía', filters={}, order=9,
    )
    moved = SavedFilterTab.objects.get(
        user=admin_a, view=COLLECTIONS, builtin_key='overdue',
    )
    moved.order = 0
    moved.is_hidden = True
    moved.save(update_fields=['order', 'is_hidden'])

    resp = api_client.post(
        RESET_URL, {'view': COLLECTIONS}, format='json', **admin_a_headers,
    )

    assert resp.status_code == 200
    rebuilt = SavedFilterTab.objects.get(
        user=admin_a, view=COLLECTIONS, builtin_key='overdue',
    )
    assert (rebuilt.order, rebuilt.is_hidden) == (1, False)
    # The user's own tab is theirs and outlives the reset.
    assert SavedFilterTab.objects.filter(id=mine.id).exists()


def test_placeholders_do_not_eat_slots_from_the_twelve_tab_cap(
    api_client, admin_a, admin_a_headers, _builtin_registry,
):
    _get_view(api_client, admin_a_headers, COLLECTIONS)
    for idx in range(SavedFilterTab.MAX_TABS_PER_VIEW - 1):
        SavedFilterTab.objects.create(
            user=admin_a, view=COLLECTIONS, name=f'Propia {idx}', filters={},
        )

    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {'view': COLLECTIONS, 'name': 'La duodécima', 'filters': {}},
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 201


def test_builtin_key_cannot_be_claimed_through_the_panel(
    api_client, admin_a, admin_a_headers,
):
    """Otherwise a real tab could pose as a placeholder and lose its filters."""
    resp = api_client.post(
        '/api/accounts/saved-filter-tabs/',
        {
            'view': 'proposal', 'name': 'Impostora',
            'filters': {'statuses': ['sent']}, 'builtin_key': 'lost',
        },
        format='json',
        **admin_a_headers,
    )

    assert resp.status_code == 201
    assert SavedFilterTab.objects.get(id=resp.json()['id']).builtin_key == ''


def test_builtin_registry_keys_exist_in_the_frontend_sources():
    """The backend only knows a builtin by its key; the filters stay in the
    frontend. A renamed `id` there would leave the placeholder orphaned — the
    chip would quietly stop being draggable — so pin the keys to their source.
    """
    from pathlib import Path

    from accounts.default_filter_tabs import BUILTIN_FILTER_TABS

    frontend = Path(__file__).resolve().parents[3] / 'frontend'
    sources = {
        'accounting_income': 'pages/panel/accounting/incomes.vue',
        'accounting_hosting': 'pages/panel/accounting/hostings.vue',
        'accounting_collections': 'pages/panel/accounting/collections.vue',
        'accounting_history_sends': 'constants/historyFilters.js',
        'accounting_history_changes': 'constants/historyFilters.js',
        'client': 'constants/clientFilters.js',
    }
    assert set(sources) == set(BUILTIN_FILTER_TABS), (
        'every view with builtins needs its frontend source listed here'
    )

    missing = []
    for view, relative in sources.items():
        text = (frontend / relative).read_text(encoding='utf-8')
        for spec in BUILTIN_FILTER_TABS[view]:
            if f"'{spec['key']}'" not in text:
                missing.append(f'{view}:{spec["key"]} not in {relative}')
    assert missing == []


def test_builtin_registry_keys_are_unique_per_view():
    """A duplicate key would give one chip two placeholders and two orders."""
    from accounts.default_filter_tabs import BUILTIN_FILTER_TABS

    for view, specs in BUILTIN_FILTER_TABS.items():
        keys = [spec['key'] for spec in specs]
        assert len(keys) == len(set(keys)), f'duplicate builtin key in {view}'
