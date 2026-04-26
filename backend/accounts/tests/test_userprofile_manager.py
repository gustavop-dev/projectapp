"""Tests for UserProfileManager.clients() / .admins() helpers."""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from accounts.models import UserProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def mixed_users():
    a = User.objects.create_user(username='admin@t.com', email='admin@t.com', password='x')
    UserProfile.objects.create(user=a, role=UserProfile.ROLE_ADMIN)
    c1 = User.objects.create_user(username='c1@t.com', email='c1@t.com', password='x')
    UserProfile.objects.create(user=c1, role=UserProfile.ROLE_CLIENT)
    c2 = User.objects.create_user(username='c2@t.com', email='c2@t.com', password='x')
    UserProfile.objects.create(user=c2, role=UserProfile.ROLE_CLIENT)
    return a, c1, c2


def test_clients_returns_only_client_profiles(mixed_users):
    qs = UserProfile.objects.clients()
    roles = {p.role for p in qs}
    assert roles == {UserProfile.ROLE_CLIENT}
    assert qs.count() == 2


def test_admins_returns_only_admin_profiles(mixed_users):
    qs = UserProfile.objects.admins()
    assert qs.count() == 1
    assert qs.first().role == UserProfile.ROLE_ADMIN


def test_clients_select_related_user_is_a_single_query(mixed_users):
    with CaptureQueriesContext(connection) as ctx:
        for profile in UserProfile.objects.clients():
            _ = profile.user.email
    assert len(ctx.captured_queries) == 1
