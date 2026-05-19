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

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
