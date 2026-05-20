"""Tests for the aggregated fields on GET /api/accounts/clients/."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import HostingSubscription, Project, UserProfile
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db


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


def test_client_list_includes_hosting_summary(authed):
    client = _make_client()
    project = Project.objects.create(name='P', client=client)
    HostingSubscription.objects.create(
        project=project,
        plan=HostingSubscription.PLAN_QUARTERLY,
        base_monthly_amount=Decimal('100'),
        effective_monthly_amount=Decimal('100'),
        billing_amount=Decimal('300'),
        start_date=date.today() - timedelta(days=30),
        next_billing_date=date.today() + timedelta(days=20),
        status=HostingSubscription.STATUS_ACTIVE,
    )
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['hosting_plan'] == 'quarterly'
    assert row['hosting_renewal_value'] is not None
    assert row['hosting_renewal_at']


def test_client_list_no_subscription_returns_nulls(authed):
    client = _make_client('no_sub@e.co')
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['hosting_plan'] is None
    assert row['hosting_renewal_at'] is None


def test_client_list_project_counts(authed):
    client = _make_client('two_projects@e.co')
    Project.objects.create(name='Active', client=client, status=Project.STATUS_ACTIVE)
    Project.objects.create(name='Paused', client=client, status=Project.STATUS_PAUSED)
    Project.objects.create(name='Archived', client=client, status=Project.STATUS_ARCHIVED)
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['active_projects_count'] == 1
    assert row['total_projects_count'] == 2  # archived excluded


def test_client_list_has_logged_in_once(authed):
    fresh = _make_client('never@e.co')
    visited = _make_client('visited@e.co')
    visited.last_login = timezone.now()
    visited.save(update_fields=['last_login'])
    resp = authed.get('/api/accounts/clients/')
    by_id = {r['user_id']: r for r in resp.json()}
    assert by_id[fresh.id]['has_logged_in_once'] is False
    assert by_id[visited.id]['has_logged_in_once'] is True


def test_client_list_last_activity_at(authed):
    client = _make_client('act@e.co')
    p = Project.objects.create(name='P', client=client)
    p.updated_at = timezone.now() - timedelta(days=3)
    p.save(update_fields=['updated_at'])
    resp = authed.get('/api/accounts/clients/')
    row = next(r for r in resp.json() if r['user_id'] == client.id)
    assert row['last_activity_at'] is not None
