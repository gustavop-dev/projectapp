"""Tests for GET /api/accounts/projects/<id>/scope-items/ (project_scope_items_view).

Read-only endpoint exposing a project's ProjectScopeItem mirror to the owning
client or an admin. Covers access control, the ?phase_id filter, archived
visibility (admin-only include_archived), and the requirements_count annotation.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import (
    Project,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
    UserProfile,
)
from content.models import BusinessProposal

pytestmark = pytest.mark.django_db

User = get_user_model()

URL = '/api/accounts/projects/{pid}/scope-items/'


def _make_phase(project, order=1):
    bp = BusinessProposal.objects.create(
        title='BP', client_name='C', total_investment=Decimal('1'),
        hosting_percent=30, status='accepted',
    )
    return ProjectPhase.objects.create(project=project, business_proposal=bp, order=order)


def _make_scope_item(phase, source_id, *, name='Item', archived=False):
    si = ProjectScopeItem.objects.create(
        phase=phase, source_item_id=source_id, name=name,
        group_id='g', group_title='G',
    )
    if archived:
        si.is_archived = True
        si.archived_at = timezone.now()
        si.save(update_fields=['is_archived', 'archived_at'])
    return si


@pytest.fixture
def other_client(db, admin_user):
    user = User.objects.create_user(
        username='scope-other@test.com', email='scope-other@test.com',
        password='pass12345', first_name='Other', last_name='Client',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True, created_by=admin_user,
    )
    return user


def test_owner_client_lists_scope_items(api_client, client_headers, project):
    phase = _make_phase(project)
    _make_scope_item(phase, 'item-a', name='Alpha')

    resp = api_client.get(URL.format(pid=project.id), **client_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]['source_item_id'] == 'item-a'


def test_admin_lists_scope_items_for_any_project(api_client, admin_headers, project):
    phase = _make_phase(project)
    _make_scope_item(phase, 'item-a')

    resp = api_client.get(URL.format(pid=project.id), **admin_headers)

    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_non_owner_client_is_forbidden(api_client, client_headers, other_client):
    foreign = Project.objects.create(name='Foreign', client=other_client)
    phase = _make_phase(foreign)
    _make_scope_item(phase, 'item-a')

    resp = api_client.get(URL.format(pid=foreign.id), **client_headers)

    assert resp.status_code == 403


def test_unknown_project_returns_404(api_client, client_headers):
    resp = api_client.get(URL.format(pid=999999), **client_headers)
    assert resp.status_code == 404


def test_phase_id_filters_scope_items(api_client, admin_headers, project):
    phase1 = _make_phase(project, order=1)
    phase2 = _make_phase(project, order=2)
    _make_scope_item(phase1, 'item-p1')
    _make_scope_item(phase2, 'item-p2')

    resp = api_client.get(
        URL.format(pid=project.id), {'phase_id': phase1.id}, **admin_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert [i['source_item_id'] for i in body] == ['item-p1']


def test_archived_scope_item_hidden_by_default(api_client, admin_headers, project):
    phase = _make_phase(project)
    _make_scope_item(phase, 'item-live')
    _make_scope_item(phase, 'item-gone', archived=True)

    resp = api_client.get(URL.format(pid=project.id), **admin_headers)

    ids = [i['source_item_id'] for i in resp.json()]
    assert ids == ['item-live']


def test_admin_include_archived_shows_archived(api_client, admin_headers, project):
    phase = _make_phase(project)
    _make_scope_item(phase, 'item-live')
    _make_scope_item(phase, 'item-gone', archived=True)

    resp = api_client.get(
        URL.format(pid=project.id), {'include_archived': '1'}, **admin_headers,
    )

    ids = {i['source_item_id'] for i in resp.json()}
    assert ids == {'item-live', 'item-gone'}


def test_client_cannot_include_archived(api_client, client_headers, project):
    phase = _make_phase(project)
    _make_scope_item(phase, 'item-gone', archived=True)

    resp = api_client.get(
        URL.format(pid=project.id), {'include_archived': '1'}, **client_headers,
    )

    assert resp.json() == []


def test_requirements_count_excludes_archived_requirements(api_client, admin_headers, project):
    phase = _make_phase(project)
    si = _make_scope_item(phase, 'item-a')
    Requirement.objects.create(phase=phase, scope_item=si, title='Live', source_flow_key='f1')
    Requirement.objects.create(
        phase=phase, scope_item=si, title='Archived', source_flow_key='f2',
        is_archived=True,
    )

    resp = api_client.get(URL.format(pid=project.id), **admin_headers)

    assert resp.json()[0]['requirements_count'] == 1
