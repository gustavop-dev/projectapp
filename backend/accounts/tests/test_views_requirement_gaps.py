"""Edge-case coverage for requirement views after the Phase refactor.

Covers:
- requirement_move_view: DoesNotExist (404), archived req not visible to client (404).
- requirement_comment_view: DoesNotExist (404), archived req not visible to client (404).
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Project,
    ProjectPhase,
    Requirement,
    UserProfile,
)
from content.models.business_proposal import BusinessProposal

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@reqgaps2.com', email='admin@reqgaps2.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@reqgaps2.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@reqgaps2.com', email='client@reqgaps2.com', password='clientpass1',
        first_name='Carlos', last_name='Ruiz',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@reqgaps2.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='ReqGaps2 Project', client=client_user,
        status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def phase(project):
    bp = BusinessProposal.objects.create(title='Gap proposal', client_name='Carlos')
    return ProjectPhase.objects.create(project=project, business_proposal=bp, order=1)


@pytest.fixture
def requirement(phase):
    return Requirement.objects.create(
        phase=phase,
        title='Test Requirement',
        status=Requirement.STATUS_BACKLOG,
    )


@pytest.fixture
def archived_requirement(phase):
    return Requirement.objects.create(
        phase=phase,
        title='Archived Requirement',
        status=Requirement.STATUS_BACKLOG,
        is_archived=True,
    )


class TestRequirementMoveDoesNotExist:
    def test_nonexistent_req_returns_404(self, api_client, admin_headers, project):
        url = f'/api/accounts/projects/{project.id}/requirements/99999/move/'
        resp = api_client.post(url, {'status': 'todo', 'order': 0}, format='json', **admin_headers)

        assert resp.status_code == 404


class TestRequirementMoveNotVisible:
    def test_archived_req_not_visible_to_client_returns_404(
        self, api_client, client_headers, project, archived_requirement,
    ):
        """Archived requirement is not visible to client → POST move returns 404."""
        url = f'/api/accounts/projects/{project.id}/requirements/{archived_requirement.id}/move/'
        resp = api_client.post(
            url, {'status': 'todo', 'order': 0}, format='json', **client_headers,
        )

        assert resp.status_code == 404


class TestRequirementCommentDoesNotExist:
    def test_nonexistent_req_returns_404(self, api_client, admin_headers, project):
        url = f'/api/accounts/projects/{project.id}/requirements/99999/comments/'
        resp = api_client.post(url, {'content': 'Hello'}, format='json', **admin_headers)

        assert resp.status_code == 404


class TestRequirementCommentNotVisible:
    def test_archived_req_not_visible_to_client_returns_404(
        self, api_client, client_headers, project, archived_requirement,
    ):
        """Archived requirement is not visible to client → POST comment returns 404."""
        url = f'/api/accounts/projects/{project.id}/requirements/{archived_requirement.id}/comments/'
        resp = api_client.post(url, {'content': 'Hello'}, format='json', **client_headers)

        assert resp.status_code == 404
