"""Tests for the "Log in as this user" (impersonation) feature.

Covers the shared service (accounts/services/impersonation.py), the panel DRF
endpoint, and the Django admin button/view.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from rest_framework.test import APIClient

from accounts.models import UserProfile
from accounts.services.impersonation import (
    ImpersonationError,
    build_impersonation_redirect_url,
    consume_exchange_code,
    create_exchange_code,
    impersonate,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser(db):
    user = User.objects.create_superuser(
        username='root@test.com', email='root@test.com', password='rootpass1!',
        first_name='Root', last_name='Admin',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def staff_admin(db):
    user = User.objects.create_user(
        username='staff@test.com', email='staff@test.com', password='staffpass1!',
        is_staff=True,
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def client_user(db, superuser):
    user = User.objects.create_user(
        username='client@test.com', email='client@test.com', password='clientpass1!',
        first_name='Client', last_name='User',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True, profile_completed=True,
        created_by=superuser,
    )
    return user


def _bearer(api_client, email, password):
    resp = api_client.post(
        '/api/accounts/login/', {'email': email, 'password': password}, format='json',
    )
    return {'HTTP_AUTHORIZATION': f"Bearer {resp.json()['tokens']['access']}"}


# ---------------------------------------------------------------------------
# Service rules
# ---------------------------------------------------------------------------

def test_impersonate_happy_path_returns_tokens(superuser, client_user):
    tokens = impersonate(superuser, client_user)
    assert tokens['access']
    assert tokens['refresh']


def test_impersonate_rejects_non_superuser_actor(staff_admin, client_user):
    with pytest.raises(ImpersonationError) as exc:
        impersonate(staff_admin, client_user)
    assert exc.value.status_code == 403


def test_impersonate_rejects_inactive_superuser_actor(superuser, client_user):
    superuser.is_active = False
    with pytest.raises(ImpersonationError) as exc:
        impersonate(superuser, client_user)
    assert exc.value.status_code == 403


def test_impersonate_rejects_other_superuser_target(superuser, db):
    other = User.objects.create_superuser(
        username='root2@test.com', email='root2@test.com', password='x',
    )
    UserProfile.objects.create(user=other, role=UserProfile.ROLE_ADMIN)
    with pytest.raises(ImpersonationError) as exc:
        impersonate(superuser, other)
    assert exc.value.status_code == 403


def test_impersonate_allows_self_superuser(superuser):
    tokens = impersonate(superuser, superuser)
    assert tokens['access']


def test_impersonate_rejects_inactive_target(superuser, client_user):
    client_user.is_active = False
    client_user.save(update_fields=['is_active'])
    with pytest.raises(ImpersonationError) as exc:
        impersonate(superuser, client_user)
    assert exc.value.status_code == 400


def test_impersonate_rejects_target_without_profile(superuser, db):
    no_profile = User.objects.create_user(
        username='noprofile@test.com', email='noprofile@test.com', password='x',
    )
    with pytest.raises(ImpersonationError) as exc:
        impersonate(superuser, no_profile)
    assert exc.value.status_code == 400


def test_build_redirect_url_carries_only_code(superuser, client_user):
    tokens = impersonate(superuser, client_user)
    code = create_exchange_code(tokens)
    url = build_impersonation_redirect_url(code, redirect_path='/platform')
    assert '/platform/admin-login?' in url
    assert f'code={code}' in url
    assert 'access=' not in url and 'refresh=' not in url
    assert 'redirect=%2Fplatform' in url


# ---------------------------------------------------------------------------
# Exchange code (single-use, short-lived)
# ---------------------------------------------------------------------------

def test_exchange_code_round_trip(superuser, client_user):
    tokens = impersonate(superuser, client_user)
    code = create_exchange_code(tokens)
    assert consume_exchange_code(code) == tokens


def test_exchange_code_is_single_use(superuser, client_user):
    code = create_exchange_code(impersonate(superuser, client_user))
    assert consume_exchange_code(code) is not None
    assert consume_exchange_code(code) is None


def test_consume_unknown_code_returns_none():
    assert consume_exchange_code('does-not-exist') is None


def test_consume_empty_code_returns_none():
    assert consume_exchange_code('') is None


# ---------------------------------------------------------------------------
# Panel DRF endpoint
# ---------------------------------------------------------------------------

def test_endpoint_superuser_gets_redirect_url(api_client, superuser, client_user):
    headers = _bearer(api_client, 'root@test.com', 'rootpass1!')
    resp = api_client.post(
        f'/api/accounts/admins/{client_user.id}/login-as/', **headers,
    )
    assert resp.status_code == 200
    redirect_url = resp.json()['redirect_url']
    assert '/platform/admin-login?' in redirect_url
    assert 'code=' in redirect_url
    assert 'access=' not in redirect_url


def test_endpoint_non_superuser_forbidden(api_client, staff_admin, client_user):
    headers = _bearer(api_client, 'staff@test.com', 'staffpass1!')
    resp = api_client.post(
        f'/api/accounts/admins/{client_user.id}/login-as/', **headers,
    )
    assert resp.status_code == 403


def test_endpoint_target_not_found(api_client, superuser):
    headers = _bearer(api_client, 'root@test.com', 'rootpass1!')
    resp = api_client.post('/api/accounts/admins/999999/login-as/', **headers)
    assert resp.status_code == 404


def test_endpoint_requires_auth(api_client, client_user):
    resp = api_client.post(f'/api/accounts/admins/{client_user.id}/login-as/')
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Exchange endpoint (public; the code is the bearer of trust)
# ---------------------------------------------------------------------------

def test_exchange_endpoint_swaps_code_for_tokens(api_client, superuser, client_user):
    code = create_exchange_code(impersonate(superuser, client_user))
    resp = api_client.post(
        '/api/accounts/impersonation/exchange/', {'code': code}, format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['access'] and resp.json()['refresh']


def test_exchange_endpoint_rejects_invalid_code(api_client):
    resp = api_client.post(
        '/api/accounts/impersonation/exchange/', {'code': 'nope'}, format='json',
    )
    assert resp.status_code == 400


def test_exchange_endpoint_code_cannot_be_reused(api_client, superuser, client_user):
    code = create_exchange_code(impersonate(superuser, client_user))
    first = api_client.post(
        '/api/accounts/impersonation/exchange/', {'code': code}, format='json',
    )
    second = api_client.post(
        '/api/accounts/impersonation/exchange/', {'code': code}, format='json',
    )
    assert first.status_code == 200
    assert second.status_code == 400


def test_login_as_then_exchange_end_to_end(api_client, superuser, client_user):
    headers = _bearer(api_client, 'root@test.com', 'rootpass1!')
    login_as = api_client.post(
        f'/api/accounts/admins/{client_user.id}/login-as/', **headers,
    )
    redirect_url = login_as.json()['redirect_url']
    code = redirect_url.split('code=')[1].split('&')[0]
    exchange = api_client.post(
        '/api/accounts/impersonation/exchange/', {'code': code}, format='json',
    )
    assert exchange.status_code == 200
    assert exchange.json()['access']


# ---------------------------------------------------------------------------
# Django admin
# ---------------------------------------------------------------------------

def _admin_instance():
    from content.admin import ProjectAppUserAdmin, admin_site
    return ProjectAppUserAdmin(User, admin_site)


def _request_with_messages(method, path, user):
    factory = RequestFactory()
    request = getattr(factory, method)(path)
    request.user = user
    SessionMiddleware(lambda r: None).process_request(request)
    MessageMiddleware(lambda r: None).process_request(request)
    return request


def test_admin_impersonate_link_renders_button(client_user):
    admin = _admin_instance()
    html = admin.impersonate_link(client_user)
    assert 'Log in as this user' in html
    assert f'/{client_user.id}/login_as/' in html


def test_admin_impersonate_link_blank_for_unsaved():
    admin = _admin_instance()
    assert admin.impersonate_link(User()) == '—'


def test_admin_login_as_view_success_redirects_to_frontend(superuser, client_user):
    admin = _admin_instance()
    request = _request_with_messages('post', '/admin/', superuser)
    response = admin.login_as_user_view(request, client_user.id)
    assert response.status_code == 302
    assert '/platform/admin-login?' in response['Location']
    assert 'code=' in response['Location']
    assert 'access=' not in response['Location']


def test_admin_login_as_view_failure_redirects_to_change(superuser, db):
    other = User.objects.create_superuser(
        username='root3@test.com', email='root3@test.com', password='x',
    )
    UserProfile.objects.create(user=other, role=UserProfile.ROLE_ADMIN)
    admin = _admin_instance()
    request = _request_with_messages('post', '/admin/', superuser)
    response = admin.login_as_user_view(request, other.id)
    assert response.status_code == 302
    assert 'admin-login' not in response['Location']
