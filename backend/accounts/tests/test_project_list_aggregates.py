"""Tests for the aggregated fields on GET /api/accounts/projects/.

The Deliverable model in this codebase has no due_date field; the
``next_deliverable`` aggregate is therefore null on this iteration (see
plan §A note). When per-deliverable due dates are added in a future
spec, the field will start returning a payload.
"""
from datetime import date, datetime, timezone as datetime_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import (
    BugReport,
    ChangeRequest,
    Deliverable,
    HostingSubscription,
    Project,
    ProjectPhase,
    UserProfile,
)
from accounts.services.tokens import get_tokens_for_user
from content.models import BusinessProposal

User = get_user_model()
pytestmark = pytest.mark.django_db
MAX_PROJECT_LIST_QUERIES = 6


@pytest.fixture
def admin_client_user(db):
    u = User.objects.create_user(username='a@e.co', email='a@e.co', password='x')
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def client_user(db):
    u = User.objects.create_user(username='c@e.co', email='c@e.co', password='x')
    UserProfile.objects.create(user=u, role='client', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed(admin_client_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(admin_client_user)["access"]}')
    return c


@pytest.fixture
def client_authed(client_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(client_user)["access"]}')
    return c


def _create_subscription(
    project,
    *,
    plan=HostingSubscription.PLAN_QUARTERLY,
    status=HostingSubscription.STATUS_ACTIVE,
    is_archived=False,
):
    return HostingSubscription.objects.create(
        project=project,
        plan=plan,
        base_monthly_amount=Decimal('100'),
        effective_monthly_amount=Decimal('100'),
        billing_amount=Decimal('300'),
        start_date=date(2026, 1, 1),
        next_billing_date=date(2026, 4, 1),
        status=status,
        is_archived=is_archived,
    )


def _create_projects_with_relations(client, prefix):
    projects = Project.objects.bulk_create([
        Project(name=f'{prefix}-{number}', client=client)
        for number in range(48)
    ])
    proposals = BusinessProposal.objects.bulk_create([
        BusinessProposal(
            title=f'{prefix}-proposal-{number}',
            client_name='Client',
            slug=f'{prefix}-proposal-{number}',
        )
        for number in range(48)
    ])
    ProjectPhase.objects.bulk_create([
        ProjectPhase(project=project, business_proposal=proposal, order=1)
        for project, proposal in zip(projects, proposals)
    ])
    HostingSubscription.objects.bulk_create([
        HostingSubscription(
            project=project,
            plan=HostingSubscription.PLAN_QUARTERLY,
            base_monthly_amount=Decimal('100'),
            effective_monthly_amount=Decimal('100'),
            billing_amount=Decimal('400'),
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 4, 1),
            status=HostingSubscription.STATUS_ACTIVE,
        )
        for project in projects
    ])
    BugReport.objects.bulk_create([
        BugReport(project=project, reported_by=client, title=f'{prefix}-bug-{number}')
        for number, project in enumerate(projects)
    ])
    ChangeRequest.objects.bulk_create([
        ChangeRequest(project=project, created_by=client, title=f'{prefix}-change-{number}')
        for number, project in enumerate(projects)
    ])
    empty_project = Project.objects.create(name=f'{prefix}-empty', client=client)
    return projects, empty_project


def test_project_list_includes_bugs_open_count(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    BugReport.objects.create(
        project=p, reported_by=client_user,
        title='B1', description='x', status=BugReport.STATUS_REPORTED,
    )
    BugReport.objects.create(
        project=p, reported_by=client_user,
        title='B2', description='x', status=BugReport.STATUS_RESOLVED,
    )
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['bugs_open_count'] == 1


def test_project_list_includes_changes_pending_count(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    ChangeRequest.objects.create(
        project=p, created_by=client_user, title='C1', description='x',
        status=ChangeRequest.STATUS_PENDING,
    )
    ChangeRequest.objects.create(
        project=p, created_by=client_user, title='C2', description='x',
        status=ChangeRequest.STATUS_APPROVED,
    )
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['changes_pending_count'] == 1


def test_project_list_next_deliverable_is_null_for_now(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    Deliverable.objects.create(
        project=p, title='D1', category=Deliverable.CATEGORY_OTHER,
        file=None, uploaded_by=client_user,
    )
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert 'next_deliverable' in row
    assert row['next_deliverable'] is None


def test_project_list_includes_last_activity_at(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    activity_time = datetime(2026, 2, 5, 12, 30, tzinfo=datetime_timezone.utc)
    Project.objects.filter(pk=p.pk).update(updated_at=activity_time)

    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)

    assert row['last_activity_at'] == '2026-02-05T12:30:00Z'


def test_project_list_zero_counts_when_no_data(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['bugs_open_count'] == 0
    assert row['changes_pending_count'] == 0
    assert row['next_deliverable'] is None
    assert row['proposal_id'] is None
    assert row['proposal_title'] is None
    assert row['next_hosting_payment'] is None
    assert row['phases_total_amount'] == 0.0


def test_project_list_keeps_aggregate_counts_independent(authed, client_user):
    """Fails if joining bugs, changes, and phases inflates the phase total."""
    project = Project.objects.create(name='Independent aggregates', client=client_user)
    BugReport.objects.create(
        project=project,
        reported_by=client_user,
        title='Open 1',
        description='x',
        is_archived=True,
    )
    BugReport.objects.create(project=project, reported_by=client_user, title='Open 2', description='x')
    BugReport.objects.create(
        project=project,
        reported_by=client_user,
        title='Resolved',
        description='x',
        status=BugReport.STATUS_RESOLVED,
    )
    ChangeRequest.objects.create(
        project=project,
        created_by=client_user,
        title='Pending 1',
        description='x',
        is_archived=True,
    )
    ChangeRequest.objects.create(project=project, created_by=client_user, title='Pending 2', description='x')
    ChangeRequest.objects.create(
        project=project,
        created_by=client_user,
        title='Approved',
        description='x',
        status=ChangeRequest.STATUS_APPROVED,
    )
    first_proposal = BusinessProposal.objects.create(
        title='First phase', client_name='Client', total_investment=Decimal('125.00'),
    )
    second_proposal = BusinessProposal.objects.create(
        title='Second phase', client_name='Client', total_investment=Decimal('125.00'),
    )
    ProjectPhase.objects.create(project=project, business_proposal=first_proposal, order=1)
    ProjectPhase.objects.create(project=project, business_proposal=second_proposal, order=2)

    response = authed.get('/api/accounts/projects/')
    row = next(item for item in response.json() if item['id'] == project.id)

    assert row['bugs_open_count'] == 2
    assert row['changes_pending_count'] == 2
    assert row['phases_total_amount'] == 250.0


def test_project_list_uses_first_phase_proposal_over_legacy_proposal(authed, client_user):
    """Fails if a legacy deliverable proposal replaces the first project phase."""
    project = Project.objects.create(name='Phase wins', client=client_user)
    deliverable = Deliverable.objects.create(
        project=project,
        title='Legacy deliverable',
        category=Deliverable.CATEGORY_OTHER,
        uploaded_by=client_user,
    )
    BusinessProposal.objects.create(title='Legacy proposal', client_name='Client', deliverable=deliverable)
    later_phase = BusinessProposal.objects.create(title='Later phase proposal', client_name='Client')
    ProjectPhase.objects.create(project=project, business_proposal=later_phase, order=2)
    first_phase = BusinessProposal.objects.create(title='Phase proposal', client_name='Client')
    ProjectPhase.objects.create(project=project, business_proposal=first_phase, order=1)

    response = authed.get('/api/accounts/projects/')
    row = next(item for item in response.json() if item['id'] == project.id)

    assert row['proposal_id'] == first_phase.id
    assert row['proposal_title'] == 'Phase proposal'


def test_project_list_uses_lowest_deliverable_legacy_proposal(authed, client_user):
    """Fails if a project without phases selects a legacy proposal in a different order."""
    project = Project.objects.create(name='Legacy fallback', client=client_user)
    first_deliverable = Deliverable.objects.create(
        project=project,
        title='First deliverable',
        category=Deliverable.CATEGORY_OTHER,
        uploaded_by=client_user,
    )
    second_deliverable = Deliverable.objects.create(
        project=project,
        title='Second deliverable',
        category=Deliverable.CATEGORY_OTHER,
        uploaded_by=client_user,
    )
    BusinessProposal.objects.create(
        title='Second legacy proposal', client_name='Client', deliverable=second_deliverable,
    )
    first_proposal = BusinessProposal.objects.create(
        title='First legacy proposal', client_name='Client', deliverable=first_deliverable,
    )

    response = authed.get('/api/accounts/projects/')
    row = next(item for item in response.json() if item['id'] == project.id)

    assert row['proposal_id'] == first_proposal.id
    assert row['proposal_title'] == 'First legacy proposal'


def test_project_list_serializes_active_hosting_payment(authed, client_user):
    project = Project.objects.create(name='Hosting', client=client_user)
    _create_subscription(
        project,
        plan=HostingSubscription.PLAN_SEMIANNUAL,
        is_archived=True,
    )

    response = authed.get('/api/accounts/projects/')
    row = next(item for item in response.json() if item['id'] == project.id)

    assert row['next_hosting_payment'] == {
        'date': '2026-04-01',
        'amount': 300.0,
        'plan': 'semiannual',
    }


def test_project_list_hides_inactive_hosting_payment(authed, client_user):
    """Fails if a suspended subscription is serialized as the next hosting payment."""
    project = Project.objects.create(name='Suspended hosting', client=client_user)
    _create_subscription(project, status=HostingSubscription.STATUS_SUSPENDED)

    response = authed.get('/api/accounts/projects/')
    row = next(item for item in response.json() if item['id'] == project.id)

    assert row['next_hosting_payment'] is None


def test_project_list_orders_projects_by_updated_at_descending(authed, client_user):
    older = Project.objects.create(name='Older', client=client_user)
    newer = Project.objects.create(name='Newer', client=client_user)
    Project.objects.filter(pk=older.pk).update(
        updated_at=datetime(2026, 1, 1, 10, 0, tzinfo=datetime_timezone.utc),
    )
    Project.objects.filter(pk=newer.pk).update(
        updated_at=datetime(2026, 1, 2, 10, 0, tzinfo=datetime_timezone.utc),
    )

    response = authed.get('/api/accounts/projects/')

    assert [row['id'] for row in response.json()] == [newer.id, older.id]


def test_project_list_admin_query_budget_stays_constant(authed, client_user):
    """Fails if the admin project list resolves aggregate data once per project."""
    populated = Project.objects.create(name='Populated', client=client_user)
    proposal = BusinessProposal.objects.create(title='Populated proposal', client_name='Client')
    ProjectPhase.objects.create(project=populated, business_proposal=proposal, order=1)
    _create_subscription(populated)
    BugReport.objects.create(project=populated, reported_by=client_user, title='Open', description='x')
    ChangeRequest.objects.create(project=populated, created_by=client_user, title='Pending', description='x')

    with CaptureQueriesContext(connection) as first_capture:
        first_response = authed.get('/api/accounts/projects/')

    added_projects, empty_project = _create_projects_with_relations(client_user, 'added-admin')
    with CaptureQueriesContext(connection) as fiftieth_capture:
        fiftieth_response = authed.get('/api/accounts/projects/')
    added_row = next(row for row in fiftieth_response.json() if row['id'] == added_projects[0].id)
    empty_row = next(row for row in fiftieth_response.json() if row['id'] == empty_project.id)

    assert len(first_response.json()) == 1
    assert len(fiftieth_response.json()) == 50
    assert len(first_capture) == len(fiftieth_capture)
    assert len(fiftieth_capture) <= MAX_PROJECT_LIST_QUERIES
    assert {
        'proposal_title': added_row['proposal_title'],
        'bugs_open_count': added_row['bugs_open_count'],
        'changes_pending_count': added_row['changes_pending_count'],
    } == {
        'proposal_title': 'added-admin-proposal-0',
        'bugs_open_count': 1,
        'changes_pending_count': 1,
    }
    assert {
        'bugs_open_count': empty_row['bugs_open_count'],
        'changes_pending_count': empty_row['changes_pending_count'],
        'proposal_id': empty_row['proposal_id'],
        'next_hosting_payment': empty_row['next_hosting_payment'],
        'phases_total_amount': empty_row['phases_total_amount'],
    } == {
        'bugs_open_count': 0,
        'changes_pending_count': 0,
        'proposal_id': None,
        'next_hosting_payment': None,
        'phases_total_amount': 0.0,
    }


def test_project_list_client_query_budget_stays_constant(client_authed, client_user):
    """Fails if the client project list resolves aggregate data once per project."""
    populated = Project.objects.create(name='Populated', client=client_user)
    proposal = BusinessProposal.objects.create(title='Populated proposal', client_name='Client')
    ProjectPhase.objects.create(project=populated, business_proposal=proposal, order=1)
    _create_subscription(populated)
    BugReport.objects.create(project=populated, reported_by=client_user, title='Open', description='x')
    ChangeRequest.objects.create(project=populated, created_by=client_user, title='Pending', description='x')

    with CaptureQueriesContext(connection) as first_capture:
        first_response = client_authed.get('/api/accounts/projects/')

    added_projects, empty_project = _create_projects_with_relations(client_user, 'added-client')
    with CaptureQueriesContext(connection) as fiftieth_capture:
        fiftieth_response = client_authed.get('/api/accounts/projects/')
    added_row = next(row for row in fiftieth_response.json() if row['id'] == added_projects[0].id)
    empty_row = next(row for row in fiftieth_response.json() if row['id'] == empty_project.id)

    assert len(first_response.json()) == 1
    assert len(fiftieth_response.json()) == 50
    assert len(first_capture) == len(fiftieth_capture)
    assert len(fiftieth_capture) <= MAX_PROJECT_LIST_QUERIES
    assert {
        'proposal_title': added_row['proposal_title'],
        'bugs_open_count': added_row['bugs_open_count'],
        'changes_pending_count': added_row['changes_pending_count'],
    } == {
        'proposal_title': 'added-client-proposal-0',
        'bugs_open_count': 1,
        'changes_pending_count': 1,
    }
    assert {
        'bugs_open_count': empty_row['bugs_open_count'],
        'changes_pending_count': empty_row['changes_pending_count'],
        'proposal_id': empty_row['proposal_id'],
        'next_hosting_payment': empty_row['next_hosting_payment'],
        'phases_total_amount': empty_row['phases_total_amount'],
    } == {
        'bugs_open_count': 0,
        'changes_pending_count': 0,
        'proposal_id': None,
        'next_hosting_payment': None,
        'phases_total_amount': 0.0,
    }
