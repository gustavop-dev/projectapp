"""Tests for uncovered branches in requirement_list_view.

Covers:
- POST to URL-scoped archived deliverable returns 400
- project_detail_view: 404 when project not found
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    Project,
    UserProfile,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@reqgaps.com', email='admin@reqgaps.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@reqgaps.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@reqgaps.com', email='client@reqgaps.com', password='clientpass1',
        first_name='Carlos', last_name='Ruiz',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='ReqGaps Project', client=client_user,
        status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def archived_deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project,
        title='Archived Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        uploaded_by=admin_user,
        is_archived=True,
    )


# ===========================================================================
# requirement_list_view POST — URL-scoped archived deliverable
# ===========================================================================

class TestRequirementListViewArchivedScopedDeliverable:
    def test_post_to_archived_url_scoped_deliverable_returns_400(
        self, api_client, admin_headers, project, archived_deliverable,
    ):
        """POST to a URL-scoped archived deliverable returns 400."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{archived_deliverable.id}/requirements/'
        )
        resp = api_client.post(url, {'title': 'Blocked req'}, format='json', **admin_headers)

        assert resp.status_code == 400


# ===========================================================================
# project_detail_view — 404 when project not found
# ===========================================================================

class TestProjectDetailViewNotFound:
    def test_returns_404_when_project_does_not_exist(
        self, api_client, admin_headers,
    ):
        """Returns 404 when the requested project_id does not exist."""
        resp = api_client.get('/api/accounts/projects/99999/', **admin_headers)

        assert resp.status_code == 404
