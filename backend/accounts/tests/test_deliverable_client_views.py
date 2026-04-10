"""Tests for deliverable client-facing views.

Covers: deliverable_attachment_files_view, deliverable_client_folders_view,
deliverable_client_folder_detail_view, deliverable_client_uploads_view.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    DeliverableClientFolder,
    DeliverableFile,
    Project,
    UserProfile,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='admin@dcv.com', email='admin@dcv.com', password='adminpass1!',
        first_name='Admin', last_name='DCV',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True)
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@dcv.com', 'password': 'adminpass1!',
    }, format='json')
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(db, admin_user):
    user = User.objects.create_user(
        username='client@dcv.com', email='client@dcv.com', password='clientpass1!',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True,
        created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@dcv.com', 'password': 'clientpass1!',
    }, format='json')
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='DCV Project', client=client_user, status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project, title='Design Docs', category=Deliverable.CATEGORY_DOCUMENTS,
        file=ContentFile(b'pdf', name='design.pdf'), uploaded_by=admin_user,
    )


@pytest.fixture
def archived_deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project, title='Old Docs', category=Deliverable.CATEGORY_DOCUMENTS,
        file=ContentFile(b'pdf', name='old.pdf'), uploaded_by=admin_user,
        is_archived=True,
    )


def _att_url(project_id, deliverable_id):
    return f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/attachments/'


def _folders_url(project_id, deliverable_id):
    return f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/client-folders/'


def _folder_detail_url(project_id, deliverable_id, folder_id):
    return (
        f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}'
        f'/client-folders/{folder_id}/'
    )


def _uploads_url(project_id, deliverable_id):
    return f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/client-uploads/'


# ===========================================================================
# deliverable_attachment_files_view — GET
# ===========================================================================

class TestDeliverableAttachmentGet:
    def test_admin_lists_empty_attachments(self, api_client, admin_headers, project, deliverable):
        resp = api_client.get(_att_url(project.id, deliverable.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    def test_admin_lists_uploaded_attachments(
        self, api_client, admin_headers, project, deliverable, admin_user,
    ):
        DeliverableFile.objects.create(
            deliverable=deliverable,
            file=ContentFile(b'contract', name='contract.pdf'),
            title='Contract',
            uploaded_by=admin_user,
        )

        resp = api_client.get(_att_url(project.id, deliverable.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Contract'

    def test_client_lists_attachments_for_own_deliverable(
        self, api_client, client_headers, project, deliverable,
    ):
        resp = api_client.get(_att_url(project.id, deliverable.id), **client_headers)

        assert resp.status_code == 200

    def test_client_gets_404_for_archived_deliverable(
        self, api_client, client_headers, project, archived_deliverable,
    ):
        resp = api_client.get(
            _att_url(project.id, archived_deliverable.id), **client_headers,
        )

        assert resp.status_code == 404

    def test_nonexistent_deliverable_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_att_url(project.id, 99999), **admin_headers)

        assert resp.status_code == 404


# ===========================================================================
# deliverable_attachment_files_view — POST
# ===========================================================================

class TestDeliverableAttachmentPost:
    def test_admin_uploads_attachment_file(
        self, api_client, admin_headers, project, deliverable,
    ):
        f = ContentFile(b'contract content', name='annex.pdf')

        resp = api_client.post(
            _att_url(project.id, deliverable.id),
            {'file': f, 'title': 'Annex A'},
            format='multipart',
            **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['title'] == 'Annex A'
        assert DeliverableFile.objects.filter(deliverable=deliverable).count() == 1

    def test_client_cannot_upload_attachment(
        self, api_client, client_headers, project, deliverable,
    ):
        f = ContentFile(b'hack', name='hack.pdf')

        resp = api_client.post(
            _att_url(project.id, deliverable.id),
            {'file': f, 'title': 'Forbidden'},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 403

    def test_upload_to_archived_deliverable_returns_400(
        self, api_client, admin_headers, project, archived_deliverable,
    ):
        f = ContentFile(b'pdf', name='test.pdf')

        resp = api_client.post(
            _att_url(project.id, archived_deliverable.id),
            {'file': f, 'title': 'Late upload'},
            format='multipart',
            **admin_headers,
        )

        assert resp.status_code == 400

    def test_upload_to_nonexistent_deliverable_returns_404(
        self, api_client, admin_headers, project,
    ):
        f = ContentFile(b'pdf', name='test.pdf')

        resp = api_client.post(
            _att_url(project.id, 99999),
            {'file': f, 'title': 'Ghost'},
            format='multipart',
            **admin_headers,
        )

        assert resp.status_code == 404


# ===========================================================================
# deliverable_client_folders_view — GET
# ===========================================================================

class TestClientFolderGet:
    def test_admin_lists_empty_folders(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.get(_folders_url(project.id, deliverable.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    def test_client_lists_folders_for_own_deliverable(
        self, api_client, client_headers, client_user, project, deliverable,
    ):
        DeliverableClientFolder.objects.create(
            deliverable=deliverable, name='Contracts', created_by=client_user,
        )

        resp = api_client.get(_folders_url(project.id, deliverable.id), **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Contracts'

    def test_third_party_client_cannot_list_folders(
        self, api_client, project, deliverable, admin_user,
    ):
        other = User.objects.create_user(
            username='other@dcv.com', email='other@dcv.com', password='pass123!',
        )
        UserProfile.objects.create(
            user=other, role=UserProfile.ROLE_CLIENT, is_onboarded=True,
            created_by=admin_user,
        )
        client = APIClient()
        resp = client.post('/api/accounts/login/', {
            'email': 'other@dcv.com', 'password': 'pass123!',
        }, format='json')
        token = resp.json()['tokens']['access']

        resp = client.get(
            _folders_url(project.id, deliverable.id),
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        assert resp.status_code == 403

    def test_client_gets_404_for_archived_deliverable_folders(
        self, api_client, client_headers, project, archived_deliverable,
    ):
        resp = api_client.get(
            _folders_url(project.id, archived_deliverable.id), **client_headers,
        )

        assert resp.status_code == 404


# ===========================================================================
# deliverable_client_folders_view — POST
# ===========================================================================

class TestClientFolderPost:
    def test_admin_creates_folder(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.post(
            _folders_url(project.id, deliverable.id),
            {'name': 'Legal Documents', 'order': 1},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['name'] == 'Legal Documents'
        assert DeliverableClientFolder.objects.filter(deliverable=deliverable).count() == 1

    def test_client_creates_folder_for_own_deliverable(
        self, api_client, client_headers, project, deliverable,
    ):
        resp = api_client.post(
            _folders_url(project.id, deliverable.id),
            {'name': 'My Documents'},
            format='json',
            **client_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['name'] == 'My Documents'

    def test_create_folder_for_archived_deliverable_returns_400(
        self, api_client, admin_headers, project, archived_deliverable,
    ):
        resp = api_client.post(
            _folders_url(project.id, archived_deliverable.id),
            {'name': 'Late Folder'},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 400

    def test_create_folder_for_nonexistent_deliverable_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _folders_url(project.id, 99999),
            {'name': 'Ghost'},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 404


# ===========================================================================
# deliverable_client_folder_detail_view — PATCH / DELETE
# ===========================================================================

class TestClientFolderDetail:
    @pytest.fixture
    def folder(self, deliverable, admin_user):
        return DeliverableClientFolder.objects.create(
            deliverable=deliverable, name='Original Name', created_by=admin_user,
        )

    def test_admin_patches_folder_name(
        self, api_client, admin_headers, project, deliverable, folder,
    ):
        resp = api_client.patch(
            _folder_detail_url(project.id, deliverable.id, folder.id),
            {'name': 'Updated Name'},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['name'] == 'Updated Name'
        folder.refresh_from_db()
        assert folder.name == 'Updated Name'

    def test_admin_patches_folder_order(
        self, api_client, admin_headers, project, deliverable, folder,
    ):
        resp = api_client.patch(
            _folder_detail_url(project.id, deliverable.id, folder.id),
            {'order': 5},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 200
        folder.refresh_from_db()
        assert folder.order == 5

    def test_admin_deletes_folder(
        self, api_client, admin_headers, project, deliverable, folder,
    ):
        resp = api_client.delete(
            _folder_detail_url(project.id, deliverable.id, folder.id),
            **admin_headers,
        )

        assert resp.status_code == 204
        assert not DeliverableClientFolder.objects.filter(id=folder.id).exists()

    def test_nonexistent_folder_returns_404(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.patch(
            _folder_detail_url(project.id, deliverable.id, 99999),
            {'name': 'Ghost'},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 404

    def test_patch_with_no_fields_returns_current_data(
        self, api_client, admin_headers, project, deliverable, folder,
    ):
        resp = api_client.patch(
            _folder_detail_url(project.id, deliverable.id, folder.id),
            {},
            format='json',
            **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['name'] == 'Original Name'


# ===========================================================================
# deliverable_client_uploads_view — GET / POST
# ===========================================================================

class TestClientUploadsGet:
    def test_admin_lists_client_uploads(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.get(_uploads_url(project.id, deliverable.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    def test_client_lists_own_uploads(
        self, api_client, client_headers, project, deliverable,
    ):
        resp = api_client.get(_uploads_url(project.id, deliverable.id), **client_headers)

        assert resp.status_code == 200

    def test_client_gets_404_for_archived_deliverable_uploads(
        self, api_client, client_headers, project, archived_deliverable,
    ):
        resp = api_client.get(
            _uploads_url(project.id, archived_deliverable.id), **client_headers,
        )

        assert resp.status_code == 404


class TestClientUploadsPost:
    def test_client_uploads_file_to_deliverable(
        self, api_client, client_headers, project, deliverable,
    ):
        f = ContentFile(b'signed doc', name='signed.pdf')

        resp = api_client.post(
            _uploads_url(project.id, deliverable.id),
            {'file': f, 'title': 'Signed Contract'},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['title'] == 'Signed Contract'

    def test_admin_uploads_file_to_deliverable(
        self, api_client, admin_headers, project, deliverable,
    ):
        f = ContentFile(b'admin doc', name='admin.pdf')

        resp = api_client.post(
            _uploads_url(project.id, deliverable.id),
            {'file': f, 'title': 'Admin Upload'},
            format='multipart',
            **admin_headers,
        )

        assert resp.status_code == 201

    def test_upload_to_archived_deliverable_returns_400(
        self, api_client, client_headers, project, archived_deliverable,
    ):
        f = ContentFile(b'late doc', name='late.pdf')

        resp = api_client.post(
            _uploads_url(project.id, archived_deliverable.id),
            {'file': f, 'title': 'Late'},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 400

    def test_upload_to_nonexistent_deliverable_returns_404(
        self, api_client, client_headers, project,
    ):
        f = ContentFile(b'ghost doc', name='ghost.pdf')

        resp = api_client.post(
            _uploads_url(project.id, 99999),
            {'file': f, 'title': 'Ghost'},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 404

    def test_client_upload_with_folder(
        self, api_client, client_headers, client_user, project, deliverable,
    ):
        folder = DeliverableClientFolder.objects.create(
            deliverable=deliverable, name='Legal', created_by=client_user,
        )
        f = ContentFile(b'foldered doc', name='foldered.pdf')

        resp = api_client.post(
            _uploads_url(project.id, deliverable.id),
            {'file': f, 'title': 'In Folder', 'folder_id': folder.id},
            format='multipart',
            **client_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['folder'] == folder.id
