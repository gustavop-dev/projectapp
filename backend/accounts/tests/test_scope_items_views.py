"""
API endpoint tests for:
  - project_scope_items_view (GET /projects/{id}/scope-items/)
  - Requirement list serializer exposing scope_item_* fields
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Project,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
    UserProfile,
)
from content.models import BusinessProposal

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@sci.com', email='admin@sci.com', password='adminpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@sci.com', email='client@sci.com', password='clientpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True,
        profile_completed=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def other_client(admin_user):
    user = User.objects.create_user(
        username='other@sci.com', email='other@sci.com', password='otherpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True, created_by=admin_user,
    )
    return user


def _headers(api_client, email, password):
    resp = api_client.post('/api/accounts/login/', {'email': email, 'password': password})
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def admin_headers(api_client, admin_user):
    return _headers(api_client, 'admin@sci.com', 'adminpass')


@pytest.fixture
def client_headers(api_client, client_user):
    return _headers(api_client, 'client@sci.com', 'clientpass')


@pytest.fixture
def other_client_headers(api_client, other_client):
    return _headers(api_client, 'other@sci.com', 'otherpass')


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Scope Project', client=client_user, status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def phase(project):
    bp = BusinessProposal.objects.create(
        title='BP', client_name='C', total_investment=Decimal('1'),
        hosting_percent=30, status='accepted',
    )
    return ProjectPhase.objects.create(project=project, business_proposal=bp, order=1)


def _scope_url(project_id):
    return f'/api/accounts/projects/{project_id}/scope-items/'


def _reqs_url(project_id):
    return f'/api/accounts/projects/{project_id}/requirements/'


def _make_scope(phase, **kw):
    defaults = dict(
        source_item_id='item-views-login', group_id='views', group_title='Vistas',
        name='Login', origin=ProjectScopeItem.ORIGIN_GROUP,
    )
    defaults.update(kw)
    return ProjectScopeItem.objects.create(phase=phase, **defaults)


@pytest.mark.django_db
class TestProjectScopeItemsView:
    def test_admin_lists_scope_items(self, api_client, admin_headers, project, phase):
        _make_scope(phase)
        resp = api_client.get(_scope_url(project.id), **admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Login'
        assert data[0]['group_id'] == 'views'
        assert data[0]['source_item_id'] == 'item-views-login'
        assert data[0]['requirements_count'] == 0

    def test_owning_client_lists_scope_items(self, api_client, client_headers, project, phase):
        _make_scope(phase)
        resp = api_client.get(_scope_url(project.id), **client_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_non_owner_client_gets_403(self, api_client, other_client_headers, project, phase):
        _make_scope(phase)
        resp = api_client.get(_scope_url(project.id), **other_client_headers)
        assert resp.status_code == 403

    def test_archived_hidden_for_client_shown_for_admin_with_flag(
        self, api_client, admin_headers, client_headers, project, phase,
    ):
        _make_scope(phase, source_item_id='item-a', name='Visible')
        _make_scope(phase, source_item_id='item-b', name='Gone', is_archived=True)

        resp_client = api_client.get(_scope_url(project.id), **client_headers)
        assert {i['name'] for i in resp_client.json()} == {'Visible'}

        resp_admin = api_client.get(_scope_url(project.id), **admin_headers)
        assert {i['name'] for i in resp_admin.json()} == {'Visible'}

        resp_admin_all = api_client.get(_scope_url(project.id) + '?include_archived=1', **admin_headers)
        assert {i['name'] for i in resp_admin_all.json()} == {'Visible', 'Gone'}

    def test_requirements_count_excludes_archived(self, api_client, admin_headers, project, phase):
        si = _make_scope(phase)
        Requirement.objects.create(phase=phase, title='R1', scope_item=si, source_flow_key='f1')
        Requirement.objects.create(
            phase=phase, title='R2', scope_item=si, source_flow_key='f2', is_archived=True,
        )
        resp = api_client.get(_scope_url(project.id), **admin_headers)
        assert resp.json()[0]['requirements_count'] == 1


@pytest.mark.django_db
class TestRequirementSerializerScopeFields:
    def test_requirement_list_exposes_scope_item_fields(self, api_client, admin_headers, project, phase):
        si = _make_scope(phase)
        Requirement.objects.create(phase=phase, title='Card', scope_item=si, source_flow_key='f1')
        resp = api_client.get(_reqs_url(project.id), **admin_headers)
        assert resp.status_code == 200
        card = resp.json()[0]
        assert card['scope_item_id'] == si.id
        assert card['scope_item_name'] == 'Login'
        assert card['scope_item_group_id'] == 'views'

    def test_requirement_without_scope_item_has_empty_fields(self, api_client, admin_headers, project, phase):
        Requirement.objects.create(phase=phase, title='Ungrouped', source_flow_key='f9')
        resp = api_client.get(_reqs_url(project.id), **admin_headers)
        card = next(c for c in resp.json() if c['title'] == 'Ungrouped')
        assert card['scope_item_id'] is None
        assert card['scope_item_name'] == ''
        assert card['scope_item_group_id'] == ''
