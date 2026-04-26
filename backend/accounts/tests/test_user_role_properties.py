"""Tests for the convenience properties on auth.User added in models.py."""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile

User = get_user_model()
pytestmark = pytest.mark.django_db


def _make_user(email, role=None):
    user = User.objects.create_user(username=email, email=email, password='x')
    if role is not None:
        UserProfile.objects.create(user=user, role=role)
    return user


def test_user_role_returns_client_for_client_profile():
    user = _make_user('c@test.com', UserProfile.ROLE_CLIENT)
    assert user.role == UserProfile.ROLE_CLIENT
    assert user.is_client_role is True
    assert user.is_admin_role is False


def test_user_role_returns_admin_for_admin_profile():
    user = _make_user('a@test.com', UserProfile.ROLE_ADMIN)
    assert user.role == UserProfile.ROLE_ADMIN
    assert user.is_admin_role is True
    assert user.is_client_role is False


def test_user_role_returns_none_when_profile_missing():
    user = _make_user('orphan@test.com', role=None)
    assert user.role is None
    assert user.is_client_role is False
    assert user.is_admin_role is False
