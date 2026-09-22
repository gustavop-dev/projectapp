"""Tests for the aggregated fields on GET /api/accounts/clients/."""
from datetime import date, datetime, timezone as datetime_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import HostingSubscription, Project, UserProfile
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db
MAX_CLIENT_LIST_QUERIES = 6


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(username='a@e.co', email='a@e.co', password='x')
    UserProfile.objects.create(user=u, role='admin', is_onboarded=True, profile_completed=True)
    return u


@pytest.fixture
def authed(admin_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(admin_user)["access"]}')
    return c


def _make_client(email='c@e.co'):
    u = User.objects.create_user(username=email, email=email, password='x')
    UserProfile.objects.create(user=u, role='client', is_onboarded=True, profile_completed=True)
    return u


def _create_subscription(
    project,
    *,
    plan,
    next_billing_date,
    status,
    billing_amount=Decimal('300'),
    is_archived=False,
):
    return HostingSubscription.objects.create(
        project=project,
        plan=plan,
        base_monthly_amount=Decimal('100'),
        effective_monthly_amount=Decimal('100'),
        billing_amount=billing_amount,
        start_date=date(2026, 1, 1),
        next_billing_date=next_billing_date,
        status=status,
        is_archived=is_archived,
    )


def _create_clients(prefix, count):
    users = User.objects.bulk_create([
        User(username=f'{prefix}{number}@e.co', email=f'{prefix}{number}@e.co')
        for number in range(count)
    ])
    UserProfile.objects.bulk_create([
        UserProfile(
            user=user,
            role=UserProfile.ROLE_CLIENT,
            is_onboarded=True,
            profile_completed=True,
        )
        for user in users
    ])
    return users


def _create_clients_with_hosting(prefix):
    users = _create_clients(prefix, 49)
    subscribed_users = users[:-1]
    projects = Project.objects.bulk_create([
        Project(name=f'{prefix}-project-{number}', client=user)
        for number, user in enumerate(subscribed_users)
    ])
    HostingSubscription.objects.bulk_create([
        HostingSubscription(
            project=project,
            plan=HostingSubscription.PLAN_QUARTERLY,
            base_monthly_amount=Decimal('100'),
            effective_monthly_amount=Decimal('100'),
            billing_amount=Decimal(str(400 + number)),
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 4, 1),
            status=HostingSubscription.STATUS_ACTIVE,
        )
        for number, project in enumerate(projects)
    ])
    return users


def test_client_list_includes_hosting_summary(authed):
    client = _make_client()
    null_date_project = Project.objects.create(name='Null date', client=client)
    _create_subscription(
        null_date_project,
        plan=HostingSubscription.PLAN_QUARTERLY,
        next_billing_date=None,
        status=HostingSubscription.STATUS_ACTIVE,
        billing_amount=Decimal('275'),
        is_archived=True,
    )
    _create_subscription(
        Project.objects.create(name='Later', client=client),
        plan=HostingSubscription.PLAN_SEMIANNUAL,
        next_billing_date=date(2026, 4, 1),
        status=HostingSubscription.STATUS_ACTIVE,
        billing_amount=Decimal('600'),
    )
    _create_subscription(
        Project.objects.create(name='Inactive', client=client),
        plan=HostingSubscription.PLAN_NINE_MONTH,
        next_billing_date=date(2026, 2, 1),
        status=HostingSubscription.STATUS_SUSPENDED,
        billing_amount=Decimal('900'),
    )
    _create_subscription(
        Project.objects.create(name='Archived active', client=client),
        plan=HostingSubscription.PLAN_MONTHLY,
        next_billing_date=date(2026, 1, 15),
        status=HostingSubscription.STATUS_ACTIVE,
        billing_amount=Decimal('1200'),
    )

    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)

    assert row['hosting_plan'] == 'quarterly'
    assert row['hosting_renewal_at'] is None
    assert row['hosting_renewal_value'] == 275.0


def test_client_list_no_subscription_returns_nulls(authed):
    client = _make_client('no_sub@e.co')
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['hosting_plan'] is None
    assert row['hosting_renewal_at'] is None
    assert row['hosting_renewal_value'] is None


def test_client_list_project_counts(authed):
    client = _make_client('two_projects@e.co')
    Project.objects.create(name='Active', client=client, status=Project.STATUS_ACTIVE)
    Project.objects.create(
        name='Suspended',
        client=client,
        status=Project.STATUS_SUSPENDED,
    )
    Project.objects.create(name='Archived', client=client, status=Project.STATUS_ARCHIVED)
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['active_projects_count'] == 1
    assert row['total_projects_count'] == 2


def test_client_list_has_logged_in_once(authed):
    fresh = _make_client('never@e.co')
    visited = _make_client('visited@e.co')
    visited.last_login = timezone.now()
    visited.save(update_fields=['last_login'])
    resp = authed.get('/api/accounts/clients/')
    by_id = {r['user_id']: r for r in resp.json()}
    assert by_id[fresh.id]['has_logged_in_once'] is False
    assert by_id[visited.id]['has_logged_in_once'] is True


@pytest.mark.parametrize(
    ('active_time', 'archived_time', 'login_time', 'expected'),
    [
        (
            datetime(2026, 2, 1, 10, 0, tzinfo=datetime_timezone.utc),
            datetime(2026, 2, 3, 10, 0, tzinfo=datetime_timezone.utc),
            datetime(2026, 2, 2, 10, 0, tzinfo=datetime_timezone.utc),
            '2026-02-03T10:00:00Z',
        ),
        (
            datetime(2026, 2, 1, 10, 0, tzinfo=datetime_timezone.utc),
            datetime(2026, 2, 2, 10, 0, tzinfo=datetime_timezone.utc),
            datetime(2026, 2, 3, 10, 0, tzinfo=datetime_timezone.utc),
            '2026-02-03T10:00:00Z',
        ),
    ],
)
def test_client_list_last_activity_at(authed, active_time, archived_time, login_time, expected):
    client = _make_client('act@e.co')
    active = Project.objects.create(name='Active', client=client, status=Project.STATUS_ACTIVE)
    archived = Project.objects.create(name='Archived', client=client, status=Project.STATUS_ARCHIVED)
    Project.objects.filter(pk=active.pk).update(updated_at=active_time)
    Project.objects.filter(pk=archived.pk).update(updated_at=archived_time)
    User.objects.filter(pk=client.pk).update(last_login=login_time)

    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)

    assert row['last_activity_at'] == expected


def test_client_list_orders_profiles_by_created_at_descending(authed):
    older = _make_client('older@e.co')
    newer = _make_client('newer@e.co')
    old_time = datetime(2026, 1, 1, 10, 0, tzinfo=datetime_timezone.utc)
    new_time = datetime(2026, 1, 2, 10, 0, tzinfo=datetime_timezone.utc)
    UserProfile.objects.filter(user=older).update(created_at=old_time)
    UserProfile.objects.filter(user=newer).update(created_at=new_time)

    response = authed.get('/api/accounts/clients/')

    assert [row['user_id'] for row in response.json()] == [newer.id, older.id]


def test_client_list_query_budget_stays_constant(authed):
    """Fails if client aggregates or subscription data query once per profile."""
    populated = _make_client('populated@e.co')
    populated_project = Project.objects.create(name='Populated', client=populated)
    _create_subscription(
        populated_project,
        plan=HostingSubscription.PLAN_QUARTERLY,
        next_billing_date=date(2026, 4, 1),
        status=HostingSubscription.STATUS_ACTIVE,
    )

    with CaptureQueriesContext(connection) as first_capture:
        first_response = authed.get('/api/accounts/clients/')

    added_clients = _create_clients_with_hosting('added')
    with CaptureQueriesContext(connection) as fiftieth_capture:
        fiftieth_response = authed.get('/api/accounts/clients/')
    added_row = next(row for row in fiftieth_response.json() if row['user_id'] == added_clients[0].id)
    empty_row = next(row for row in fiftieth_response.json() if row['user_id'] == added_clients[-1].id)

    assert (first_response.status_code, fiftieth_response.status_code) == (200, 200)
    assert len(first_response.json()) == 1
    assert len(fiftieth_response.json()) == 50
    assert len(first_capture) == len(fiftieth_capture)
    assert len(fiftieth_capture) <= MAX_CLIENT_LIST_QUERIES
    assert {
        'hosting_plan': added_row['hosting_plan'],
        'hosting_renewal_value': added_row['hosting_renewal_value'],
        'active_projects_count': added_row['active_projects_count'],
    } == {
        'hosting_plan': 'quarterly',
        'hosting_renewal_value': 400.0,
        'active_projects_count': 0,
    }
    assert {
        'hosting_plan': empty_row['hosting_plan'],
        'active_projects_count': empty_row['active_projects_count'],
        'total_projects_count': empty_row['total_projects_count'],
        'last_activity_at': empty_row['last_activity_at'],
        'has_logged_in_once': empty_row['has_logged_in_once'],
    } == {
        'hosting_plan': None,
        'active_projects_count': 0,
        'total_projects_count': 0,
        'last_activity_at': None,
        'has_logged_in_once': False,
    }
