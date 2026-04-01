"""
Shared fixtures for accounts tests (collection accounts, serializers, etc.).

Uses stable emails/passwords so JWT login fixtures match API tests.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Project, UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='ca-admin@test.com',
        email='ca-admin@test.com',
        password='pass12345',
        first_name='Admin',
        last_name='Test',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    return user


@pytest.fixture
def client_user(db, admin_user):
    user = User.objects.create_user(
        username='ca-client@test.com',
        email='ca-client@test.com',
        password='pass12345',
        first_name='Client',
        last_name='User',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
        company_name='ClientCo',
        created_by=admin_user,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post(
        '/api/accounts/login/',
        {'email': 'ca-admin@test.com', 'password': 'pass12345'},
    )
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post(
        '/api/accounts/login/',
        {'email': 'ca-client@test.com', 'password': 'pass12345'},
    )
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='CA Project',
        client=client_user,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )
