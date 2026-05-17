"""Tests for the aggregated fields on GET /api/accounts/projects/.

The Deliverable model in this codebase has no due_date field; the
``next_deliverable`` aggregate is therefore null on this iteration (see
plan §A note). When per-deliverable due dates are added in a future
spec, the field will start returning a payload.
"""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import BugReport, ChangeRequest, Deliverable, Project, UserProfile
from accounts.services.tokens import get_tokens_for_user

User = get_user_model()
pytestmark = pytest.mark.django_db


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
    p.updated_at = timezone.now() - timedelta(hours=2)
    p.save(update_fields=['updated_at'])
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['last_activity_at'] is not None


def test_project_list_zero_counts_when_no_data(authed, client_user):
    p = Project.objects.create(name='P1', client=client_user)
    resp = authed.get('/api/accounts/projects/')
    row = next(r for r in resp.json() if r['id'] == p.id)
    assert row['bugs_open_count'] == 0
    assert row['changes_pending_count'] == 0
    assert row['next_deliverable'] is None
