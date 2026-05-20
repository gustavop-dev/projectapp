"""Tests for the ProjectPhase model, service, and REST endpoints."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Project, ProjectPhase, UserProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def client_user(db):
    return User.objects.create_user(
        username='client@example.com', email='client@example.com', password='x',
    )


@pytest.fixture
def project(client_user):
    return Project.objects.create(name='Test project', client=client_user)


@pytest.fixture
def business_proposal(db):
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(title='Proposal A', client_name='Test Client')


# =========================================================================
# Model tests
# =========================================================================


def test_phase_links_project_and_proposal_with_order(project, business_proposal):
    p = ProjectPhase.objects.create(
        project=project, business_proposal=business_proposal, order=1,
    )
    assert p.project == project
    assert p.business_proposal == business_proposal
    assert p.order == 1


def test_unique_constraint_blocks_same_proposal_twice_on_one_project(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    with pytest.raises(IntegrityError):
        ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=2)


def test_ordering_by_order_field(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    ProjectPhase.objects.create(project=project, business_proposal=p2, order=2)
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    titles = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles == ['Proposal A', 'P2']


def test_linked_business_proposal_returns_first_phase_proposal(project, business_proposal):
    ProjectPhase.objects.create(project=project, business_proposal=business_proposal, order=1)
    assert project.linked_business_proposal() == business_proposal


def test_linked_business_proposal_returns_none_when_no_phases(project):
    assert project.linked_business_proposal() is None


# =========================================================================
# Service tests
# =========================================================================


from accounts.services.project_phases import (  # noqa: E402
    PhaseError,
    add_phase,
    list_phases,
    remove_phase,
    reorder_phases,
)


def test_add_phase_appends_at_end_when_order_omitted(project, business_proposal):
    phase = add_phase(project, business_proposal)
    assert phase.order == 1
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    phase2 = add_phase(project, p2)
    assert phase2.order == 2


def test_add_phase_rejects_duplicate(project, business_proposal):
    add_phase(project, business_proposal)
    with pytest.raises(PhaseError) as exc:
        add_phase(project, business_proposal)
    assert exc.value.code == 'duplicate_proposal'


def test_remove_phase_renumbers_remaining(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    p3 = BusinessProposal.objects.create(title='P3', client_name='X')
    add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    add_phase(project, p3)
    remove_phase(project, ph2.id)
    remaining = list(project.phases.values_list('order', 'business_proposal__title').order_by('order'))
    assert remaining == [(1, 'Proposal A'), (2, 'P3')]


def test_reorder_phases_writes_new_order_atomically(project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    p3 = BusinessProposal.objects.create(title='P3', client_name='X')
    ph1 = add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    ph3 = add_phase(project, p3)
    reorder_phases(project, [
        {'id': ph3.id, 'order': 1},
        {'id': ph1.id, 'order': 2},
        {'id': ph2.id, 'order': 3},
    ])
    titles_in_order = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles_in_order == ['P3', 'Proposal A', 'P2']


def test_reorder_phases_rejects_phase_from_another_project(project, business_proposal, client_user):
    other = Project.objects.create(name='Other', client=client_user)
    from content.models import BusinessProposal
    p_other = BusinessProposal.objects.create(title='PO', client_name='X')
    phase_other = add_phase(other, p_other)
    ph1 = add_phase(project, business_proposal)
    with pytest.raises(PhaseError) as exc:
        reorder_phases(project, [
            {'id': phase_other.id, 'order': 1},
            {'id': ph1.id, 'order': 2},
        ])
    assert exc.value.code == 'invalid_phase_id'


# =========================================================================
# HTTP-level endpoint tests
# =========================================================================


from rest_framework.test import APIClient  # noqa: E402

from accounts.services.tokens import get_tokens_for_user  # noqa: E402


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        username='admin@example.com', email='admin@example.com', password='x',
    )
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed_client(admin_user):
    tokens = get_tokens_for_user(admin_user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    return c


def test_list_phases_endpoint_returns_ordered_phases(authed_client, project, business_proposal):
    add_phase(project, business_proposal)
    resp = authed_client.get(f'/api/accounts/projects/{project.id}/phases/')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]['proposal']['title'] == 'Proposal A'


def test_add_phase_endpoint(authed_client, project, business_proposal):
    resp = authed_client.post(
        f'/api/accounts/projects/{project.id}/phases/',
        {'proposal_id': business_proposal.id},
        format='json',
    )
    assert resp.status_code == 201
    assert resp.json()['order'] == 1


def test_add_phase_endpoint_rejects_duplicate(authed_client, project, business_proposal):
    add_phase(project, business_proposal)
    resp = authed_client.post(
        f'/api/accounts/projects/{project.id}/phases/',
        {'proposal_id': business_proposal.id},
        format='json',
    )
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'duplicate_proposal'


def test_remove_phase_endpoint(authed_client, project, business_proposal):
    phase = add_phase(project, business_proposal)
    resp = authed_client.delete(f'/api/accounts/projects/{project.id}/phases/{phase.id}/')
    assert resp.status_code == 204
    assert project.phases.count() == 0


def test_reorder_phases_endpoint(authed_client, project, business_proposal):
    from content.models import BusinessProposal
    p2 = BusinessProposal.objects.create(title='P2', client_name='X')
    ph1 = add_phase(project, business_proposal)
    ph2 = add_phase(project, p2)
    resp = authed_client.patch(
        f'/api/accounts/projects/{project.id}/phases/reorder/',
        [{'id': ph2.id, 'order': 1}, {'id': ph1.id, 'order': 2}],
        format='json',
    )
    assert resp.status_code == 200
    titles = [ph.business_proposal.title for ph in project.phases.all()]
    assert titles == ['P2', 'Proposal A']


def test_patch_phase_sets_hosting_start_date(authed_client, project, business_proposal):
    phase = add_phase(project, business_proposal)
    resp = authed_client.patch(
        f'/api/accounts/projects/{project.id}/phases/{phase.id}/',
        {'hosting_start_date': '2026-06-01'},
        format='json',
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['hosting_start_date'] == '2026-06-01'
    phase.refresh_from_db()
    assert str(phase.hosting_start_date) == '2026-06-01'


def test_patch_phase_clears_hosting_start_date(authed_client, project, business_proposal):
    phase = add_phase(project, business_proposal)
    phase.hosting_start_date = '2026-06-01'
    phase.save()
    resp = authed_client.patch(
        f'/api/accounts/projects/{project.id}/phases/{phase.id}/',
        {'hosting_start_date': None},
        format='json',
    )
    assert resp.status_code == 200
    phase.refresh_from_db()
    assert phase.hosting_start_date is None


def test_patch_phase_returns_hosting_tiers(authed_client, project, business_proposal):
    """hosting_tiers are returned in the phase response."""
    phase = add_phase(project, business_proposal)
    resp = authed_client.patch(
        f'/api/accounts/projects/{project.id}/phases/{phase.id}/',
        {'hosting_start_date': '2026-07-01'},
        format='json',
    )
    assert resp.status_code == 200
    tiers = resp.json().get('hosting_tiers', [])
    assert len(tiers) == 3
    frequencies = [t['frequency'] for t in tiers]
    assert frequencies == ['monthly', 'quarterly', 'semiannual']


def test_patch_phase_rejects_non_admin(project, business_proposal, client_user):
    """Client user cannot PATCH a phase."""
    from accounts.services.tokens import get_tokens_for_user
    phase = add_phase(project, business_proposal)
    tokens = get_tokens_for_user(client_user)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    resp = c.patch(
        f'/api/accounts/projects/{project.id}/phases/{phase.id}/',
        {'hosting_start_date': '2026-06-01'},
        format='json',
    )
    assert resp.status_code == 403


def test_list_phases_includes_hosting_tiers_and_start_date(authed_client, project, business_proposal):
    phase = add_phase(project, business_proposal)
    phase.hosting_start_date = '2026-05-01'
    phase.save()
    resp = authed_client.get(f'/api/accounts/projects/{project.id}/phases/')
    assert resp.status_code == 200
    data = resp.json()[0]
    assert data['hosting_start_date'] == '2026-05-01'
    assert 'hosting_tiers' in data
    assert len(data['hosting_tiers']) == 3
