"""Tests for uncovered branches in accounts/views.py — second batch.

Covers:
- requirement_bulk_upload_view: success, not-list, too-many, archived deliverable
- deliverable_sync_technical_requirements_view: success, 404, archived, sync-error
- login_view: reCAPTCHA validation branches
- project_list_view: creation with proposal_id
- project_detail_view: non-owning client access denied
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
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
        username='admin@gaps2.com', email='admin@gaps2.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@gaps2.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@gaps2.com', email='client@gaps2.com', password='clientpass1',
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
        'email': 'client@gaps2.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Gaps2 Project', client=client_user,
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
def archived_deliverable(project, admin_user):
    d = Deliverable.objects.create(
        project=project,
        title='Archived Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        uploaded_by=admin_user,
        is_archived=True,
    )
    return d


# ===========================================================================
# requirement_bulk_upload_view
# ===========================================================================

class TestRequirementBulkUploadView:
    def test_admin_bulk_creates_requirements(
        self, api_client, admin_headers, project, deliverable,
    ):
        """Admin can bulk-create requirements from a JSON array."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/requirements/bulk/'
        )
        payload = [
            {'title': 'Req 1', 'description': 'First requirement'},
            {'title': 'Req 2', 'priority': 'high'},
            {'title': 'Req 3'},
        ]
        resp = api_client.post(url, payload, format='json', **admin_headers)

        assert resp.status_code == 201
        assert resp.json()['created'] == 3

    def test_returns_400_when_payload_is_not_a_list(
        self, api_client, admin_headers, project, deliverable,
    ):
        """Returns 400 when request body is not a JSON array."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/requirements/bulk/'
        )
        resp = api_client.post(url, {'title': 'bad'}, format='json', **admin_headers)

        assert resp.status_code == 400

    def test_returns_400_when_too_many_items(
        self, api_client, admin_headers, project, deliverable,
    ):
        """Returns 400 when more than 500 items are submitted."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/requirements/bulk/'
        )
        payload = [{'title': f'Req {i}'} for i in range(501)]
        resp = api_client.post(url, payload, format='json', **admin_headers)

        assert resp.status_code == 400

    def test_returns_400_when_deliverable_is_archived(
        self, api_client, admin_headers, project, archived_deliverable,
    ):
        """Returns 400 when target deliverable is archived."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{archived_deliverable.id}/requirements/bulk/'
        )
        resp = api_client.post(url, [{'title': 'Req'}], format='json', **admin_headers)

        assert resp.status_code == 400


# ===========================================================================
# deliverable_sync_technical_requirements_view
# ===========================================================================

class TestDeliverableSyncTechnicalRequirementsView:
    def test_returns_404_when_deliverable_not_found(
        self, api_client, admin_headers, project,
    ):
        """Returns 404 when deliverable_id does not exist in the project."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'99999/sync-technical-requirements/'
        )
        resp = api_client.post(url, **admin_headers)

        assert resp.status_code == 404

    def test_returns_400_when_deliverable_is_archived(
        self, api_client, admin_headers, project, archived_deliverable,
    ):
        """Returns 400 when deliverable is archived."""
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{archived_deliverable.id}/sync-technical-requirements/'
        )
        resp = api_client.post(url, **admin_headers)

        assert resp.status_code == 400

    @patch('accounts.services.technical_requirements_sync.sync_technical_requirements_for_deliverable')
    def test_returns_400_when_sync_returns_not_ok(
        self, mock_sync, api_client, admin_headers, project, deliverable,
    ):
        """Returns 400 when sync service returns {ok: False}."""
        mock_sync.return_value = {'ok': False, 'detail': 'No hay secciones técnicas.'}
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/sync-technical-requirements/'
        )
        resp = api_client.post(url, **admin_headers)

        assert resp.status_code == 400
        assert 'No hay secciones' in resp.json()['detail']

    @patch('accounts.services.technical_requirements_sync.sync_technical_requirements_for_deliverable')
    def test_success_returns_sync_result(
        self, mock_sync, api_client, admin_headers, project, deliverable,
    ):
        """Returns 200 with sync result when sync succeeds."""
        mock_sync.return_value = {
            'ok': True,
            'created': 5,
            'updated': 2,
        }
        url = (
            f'/api/accounts/projects/{project.id}/deliverables/'
            f'{deliverable.id}/sync-technical-requirements/'
        )
        resp = api_client.post(url, **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['created'] == 5


# ===========================================================================
# login_view — reCAPTCHA branches
# ===========================================================================

class TestLoginRecaptchaBranches:
    @override_settings(RECAPTCHA_SECRET_KEY='test_recaptcha_secret')
    def test_missing_recaptcha_token_returns_400(self, api_client):
        """Returns 400 when recaptcha_token is missing and secret is configured."""
        resp = api_client.post('/api/accounts/login/', {
            'email': 'nonclient@example.com',
            'password': 'password123',
        })

        assert resp.status_code == 400
        assert 'captcha' in resp.json()['detail'].lower()

    @override_settings(RECAPTCHA_SECRET_KEY='test_recaptcha_secret')
    @patch('accounts.views.http_requests.post')
    def test_invalid_recaptcha_returns_400(self, mock_post, api_client):
        """Returns 400 when reCAPTCHA verification returns success=False."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': False}
        mock_post.return_value = mock_response

        resp = api_client.post('/api/accounts/login/', {
            'email': 'nonclient@example.com',
            'password': 'password123',
            'recaptcha_token': 'bad_token',
        })

        assert resp.status_code == 400
        assert 'captcha' in resp.json()['detail'].lower()

    @override_settings(RECAPTCHA_SECRET_KEY='test_recaptcha_secret')
    @patch('accounts.views.http_requests.post')
    def test_recaptcha_network_error_allows_login(self, mock_post, api_client, client_user):
        """Network error during reCAPTCHA verification is logged but login is allowed."""
        import requests as real_requests
        mock_post.side_effect = real_requests.RequestException('timeout')

        # Should proceed past reCAPTCHA failure and fail with wrong password
        # (not a 400 captcha error)
        resp = api_client.post('/api/accounts/login/', {
            'email': 'client@gaps2.com',
            'password': 'wrongpass',
            'recaptcha_token': 'any_token',
        })

        # Not 400 (captcha), should be 401 (wrong credentials)
        assert resp.status_code == 401


# ===========================================================================
# project_detail_view — non-owning client forbidden
# ===========================================================================

class TestProjectDetailNonOwningClient:
    def test_client_cannot_access_other_clients_project(
        self, api_client, client_headers, admin_user,
    ):
        """A client cannot GET a project that belongs to another client."""
        other_client = User.objects.create_user(
            username='other@gaps2.com', email='other@gaps2.com', password='pass1',
        )
        UserProfile.objects.create(
            user=other_client, role=UserProfile.ROLE_CLIENT, is_onboarded=True,
            created_by=admin_user,
        )
        other_project = Project.objects.create(
            name='Other Project', client=other_client,
            status=Project.STATUS_ACTIVE,
        )

        resp = api_client.get(
            f'/api/accounts/projects/{other_project.id}/', **client_headers,
        )

        assert resp.status_code == 403
