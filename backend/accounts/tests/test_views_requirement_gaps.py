"""Tests for uncovered error branches in requirement_list_view, requirement_move_view,
and requirement_comment_view.

Covers:
- requirement_list_view: deliverable not in project (line 873), not visible for client (877-878)
- requirement_move_view: DoesNotExist (1096-1097), deliverable_id mismatch (1100), not visible (1103)
- requirement_comment_view: DoesNotExist (1171-1172), deliverable_id mismatch (1175), not visible (1178)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    Project,
    Requirement,
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
def deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project,
        title='Main Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        uploaded_by=admin_user,
    )


@pytest.fixture
def other_deliverable(project, admin_user):
    """A second deliverable in the same project."""
    return Deliverable.objects.create(
        project=project,
        title='Other Deliverable',
        category=Deliverable.CATEGORY_OTHER,
        uploaded_by=admin_user,
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


@pytest.fixture
def requirement(deliverable):
    return Requirement.objects.create(
        deliverable=deliverable,
        title='Test Requirement',
        status=Requirement.STATUS_BACKLOG,
    )


@pytest.fixture
def archived_requirement(deliverable):
    return Requirement.objects.create(
        deliverable=deliverable,
        title='Archived Requirement',
        status=Requirement.STATUS_BACKLOG,
        is_archived=True,
    )


# ===========================================================================
# requirement_list_view — deliverable not found in project (line 873)
# ===========================================================================

class TestRequirementListDeliverableNotFound:
    def test_deliverable_from_other_project_returns_404(
        self, api_client, client_headers, project, admin_user,
    ):
        """GET requirements with a deliverable_id that doesn't belong to the project → 404."""
        other_project = Project.objects.create(
            name='Other Project',
            client=User.objects.get(username='client@reqgaps2.com'),
            status=Project.STATUS_ACTIVE,
        )
        foreign_deliverable = Deliverable.objects.create(
            project=other_project,
            title='Foreign Deliverable',
            category=Deliverable.CATEGORY_DOCUMENTS,
            uploaded_by=admin_user,
        )

        url = f'/api/accounts/projects/{project.id}/deliverables/{foreign_deliverable.id}/requirements/'
        resp = api_client.get(url, **client_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_list_view — deliverable not visible for client (lines 877-878)
# ===========================================================================

class TestRequirementListDeliverableNotVisible:
    def test_archived_deliverable_not_visible_to_client_returns_404(
        self, api_client, client_headers, project, archived_deliverable,
    ):
        """GET requirements with archived deliverable → 404 for non-admin client."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{archived_deliverable.id}/requirements/'
        )
        resp = api_client.get(url, **client_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_move_view — DoesNotExist (lines 1096-1097)
# ===========================================================================

class TestRequirementMoveDoesNotExist:
    def test_nonexistent_req_returns_404(self, api_client, admin_headers, project, deliverable):
        """POST move with non-existent req_id returns 404."""
        url = f'/api/accounts/projects/{project.id}/deliverables/{deliverable.id}/requirements/99999/move/'
        resp = api_client.post(url, {'status': 'todo', 'order': 0}, format='json', **admin_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_move_view — deliverable_id mismatch (line 1100)
# ===========================================================================

class TestRequirementMoveDeliverableMismatch:
    def test_req_from_different_deliverable_returns_404(
        self, api_client, admin_headers, project, deliverable, other_deliverable, requirement,
    ):
        """Requirement belongs to deliverable A but URL uses deliverable B → 404."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{other_deliverable.id}/requirements/{requirement.id}/move/'
        )
        resp = api_client.post(url, {'status': 'todo', 'order': 0}, format='json', **admin_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_move_view — not visible for client (line 1103)
# ===========================================================================

class TestRequirementMoveNotVisible:
    def test_archived_req_not_visible_to_client_returns_404(
        self, api_client, client_headers, project, deliverable, archived_requirement,
    ):
        """Archived requirement is not visible to client → POST move returns 404."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/requirements/{archived_requirement.id}/move/'
        )
        resp = api_client.post(
            url, {'status': 'todo', 'order': 0}, format='json', **client_headers,
        )

        assert resp.status_code == 404


# ===========================================================================
# requirement_comment_view — DoesNotExist (lines 1171-1172)
# ===========================================================================

class TestRequirementCommentDoesNotExist:
    def test_nonexistent_req_returns_404(self, api_client, admin_headers, project, deliverable):
        """POST comment with non-existent req_id returns 404."""
        url = f'/api/accounts/projects/{project.id}/deliverables/{deliverable.id}/requirements/99999/comments/'
        resp = api_client.post(url, {'content': 'Hello'}, format='json', **admin_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_comment_view — deliverable_id mismatch (line 1175)
# ===========================================================================

class TestRequirementCommentDeliverableMismatch:
    def test_req_from_different_deliverable_returns_404(
        self, api_client, admin_headers, project, deliverable, other_deliverable, requirement,
    ):
        """Requirement belongs to deliverable A but URL uses deliverable B → 404."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{other_deliverable.id}/requirements/{requirement.id}/comments/'
        )
        resp = api_client.post(url, {'content': 'Hello'}, format='json', **admin_headers)

        assert resp.status_code == 404


# ===========================================================================
# requirement_comment_view — not visible for client (line 1178)
# ===========================================================================

class TestRequirementCommentNotVisible:
    def test_archived_req_not_visible_to_client_returns_404(
        self, api_client, client_headers, project, deliverable, archived_requirement,
    ):
        """Archived requirement is not visible to client → POST comment returns 404."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/requirements/{archived_requirement.id}/comments/'
        )
        resp = api_client.post(url, {'content': 'Hello'}, format='json', **client_headers)

        assert resp.status_code == 404
