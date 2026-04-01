import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    DeliverableVersion,
    Project,
    UserProfile,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@del.com', email='admin@del.com', password='adminpass1',
        first_name='Admin', last_name='User',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN,
        is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@del.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@del.com', email='client@del.com', password='clientpass1',
        first_name='Carlos', last_name='López',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='DelCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@del.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Del Project', client=client_user,
        status=Project.STATUS_ACTIVE, progress=0,
    )


def _make_file(name='test.pdf', content=b'fake pdf content'):
    return ContentFile(content, name=name)


@pytest.fixture
def sample_deliverables(project, admin_user):
    items = []
    for title, cat in [
        ('Wireframes', 'designs'),
        ('API Keys', 'credentials'),
        ('User Manual', 'documents'),
    ]:
        d = Deliverable.objects.create(
            project=project, uploaded_by=admin_user,
            title=title, category=cat,
            file=_make_file(f'{title.lower().replace(" ", "-")}.pdf'),
            current_version=1,
        )
        DeliverableVersion.objects.create(
            deliverable=d, file=d.file, version_number=1, uploaded_by=admin_user,
        )
        items.append(d)
    return items


def _url(project_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/deliverables/{suffix}'


def _detail_url(project_id, del_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/deliverables/{del_id}/{suffix}'


# =========================================================================
# List & Filter
# =========================================================================


@pytest.mark.django_db
class TestDeliverableList:
    def test_admin_lists_deliverables_for_project(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        resp = api_client.get(_url(project.id), **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_client_lists_deliverables_for_own_project(
        self, api_client, client_headers, project, sample_deliverables,
    ):
        resp = api_client.get(_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_by_category_returns_matching_only(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        resp = api_client.get(f'{_url(project.id)}?category=designs', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['category'] == 'designs'

    def test_unauthenticated_request_rejected(self, api_client, project):
        resp = api_client.get(_url(project.id))

        assert resp.status_code == 401

    def test_other_client_cannot_list_deliverables(self, api_client, project):
        other = User.objects.create_user(
            username='other@del.com', email='other@del.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        client = APIClient()
        resp = client.post('/api/accounts/login/', {
            'email': 'other@del.com', 'password': 'pass1234',
        })
        token = resp.json()['tokens']['access']

        resp = client.get(_url(project.id), HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 403


# =========================================================================
# Create (admin only)
# =========================================================================


@pytest.mark.django_db
class TestDeliverableCreate:
    def test_admin_uploads_deliverable(
        self, api_client, admin_headers, project,
    ):
        f = _make_file('design-v1.pdf')

        resp = api_client.post(
            _url(project.id),
            {'title': 'Design mockup', 'description': 'First draft.', 'category': 'designs', 'file': f},
            format='multipart', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'Design mockup'
        assert data['category'] == 'designs'
        assert data['current_version'] == 1
        assert data['file_url'] is not None

    def test_create_also_creates_version_record(
        self, api_client, admin_headers, project,
    ):
        f = _make_file('doc.pdf')

        resp = api_client.post(
            _url(project.id),
            {'title': 'Doc', 'category': 'documents', 'file': f},
            format='multipart', **admin_headers,
        )

        d = Deliverable.objects.get(id=resp.json()['id'])
        assert d.versions.count() == 1
        assert d.versions.first().version_number == 1

    def test_client_cannot_upload_deliverable(
        self, api_client, client_headers, project,
    ):
        f = _make_file('hack.pdf')

        resp = api_client.post(
            _url(project.id),
            {'title': 'Forbidden', 'category': 'other', 'file': f},
            format='multipart', **client_headers,
        )

        assert resp.status_code == 403

    def test_create_without_file_fails(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _url(project.id),
            {'title': 'No file', 'category': 'other'},
            format='multipart', **admin_headers,
        )

        assert resp.status_code == 400

    def test_create_without_title_fails(
        self, api_client, admin_headers, project,
    ):
        f = _make_file('test.pdf')

        resp = api_client.post(
            _url(project.id),
            {'category': 'other', 'file': f},
            format='multipart', **admin_headers,
        )

        assert resp.status_code == 400


# =========================================================================
# Detail
# =========================================================================


@pytest.mark.django_db
class TestDeliverableDetail:
    def test_admin_gets_detail_with_versions(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        d = sample_deliverables[0]

        resp = api_client.get(_detail_url(project.id, d.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Wireframes'
        assert 'versions' in data
        assert len(data['versions']) == 1

    def test_client_gets_detail(
        self, api_client, client_headers, project, sample_deliverables,
    ):
        resp = api_client.get(_detail_url(project.id, sample_deliverables[0].id), **client_headers)

        assert resp.status_code == 200

    def test_nonexistent_deliverable_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_detail_url(project.id, 99999), **admin_headers)

        assert resp.status_code == 404


# =========================================================================
# Update metadata (admin only)
# =========================================================================


@pytest.mark.django_db
class TestDeliverableUpdate:
    def test_admin_updates_metadata(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        d = sample_deliverables[0]

        resp = api_client.patch(
            _detail_url(project.id, d.id),
            {'title': 'Updated Wireframes', 'category': 'documents'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['title'] == 'Updated Wireframes'
        assert resp.json()['category'] == 'documents'

    def test_client_cannot_update_deliverable(
        self, api_client, client_headers, project, sample_deliverables,
    ):
        resp = api_client.patch(
            _detail_url(project.id, sample_deliverables[0].id),
            {'title': 'Hacked'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403


# =========================================================================
# Delete (admin only)
# =========================================================================


@pytest.mark.django_db
class TestDeliverableDelete:
    def test_admin_deletes_deliverable(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        d = sample_deliverables[0]

        resp = api_client.delete(_detail_url(project.id, d.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['detail'] == 'Entregable archivado.'
        d.refresh_from_db()
        assert d.is_archived is True

    def test_client_cannot_delete_deliverable(
        self, api_client, client_headers, project, sample_deliverables,
    ):
        resp = api_client.delete(
            _detail_url(project.id, sample_deliverables[0].id), **client_headers,
        )

        assert resp.status_code == 403


# =========================================================================
# Upload new version (admin only)
# =========================================================================


@pytest.mark.django_db
class TestDeliverableUploadVersion:
    def test_admin_uploads_new_version(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        d = sample_deliverables[0]
        new_file = _make_file('wireframes-v2.pdf', b'updated content')

        resp = api_client.post(
            _detail_url(project.id, d.id, 'upload-version/'),
            {'file': new_file},
            format='multipart', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['current_version'] == 2
        assert len(data['versions']) == 2

    def test_version_number_increments_correctly(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        d = sample_deliverables[0]

        api_client.post(
            _detail_url(project.id, d.id, 'upload-version/'),
            {'file': _make_file('v2.pdf')},
            format='multipart', **admin_headers,
        )
        api_client.post(
            _detail_url(project.id, d.id, 'upload-version/'),
            {'file': _make_file('v3.pdf')},
            format='multipart', **admin_headers,
        )

        d.refresh_from_db()
        assert d.current_version == 3
        assert d.versions.count() == 3

    def test_client_cannot_upload_new_version(
        self, api_client, client_headers, project, sample_deliverables,
    ):
        resp = api_client.post(
            _detail_url(project.id, sample_deliverables[0].id, 'upload-version/'),
            {'file': _make_file('hack.pdf')},
            format='multipart', **client_headers,
        )

        assert resp.status_code == 403

    def test_upload_version_for_nonexistent_deliverable_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _detail_url(project.id, 99999, 'upload-version/'),
            {'file': _make_file('ghost.pdf')},
            format='multipart', **admin_headers,
        )

        assert resp.status_code == 404


# =========================================================================
# General endpoint (all projects)
# =========================================================================


@pytest.mark.django_db
class TestDeliverableAllView:
    def test_admin_sees_deliverables_across_all_projects(
        self, api_client, admin_headers, project, sample_deliverables, client_user,
    ):
        other_project = Project.objects.create(
            name='Other Project', client=client_user, status=Project.STATUS_ACTIVE,
        )
        Deliverable.objects.create(
            project=other_project, uploaded_by=User.objects.get(email='admin@del.com'),
            title='Other file', category='other',
            file=_make_file('other.pdf'),
        )

        resp = api_client.get('/api/accounts/deliverables/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        project_names = {item['project_name'] for item in data}
        assert 'Del Project' in project_names
        assert 'Other Project' in project_names

    def test_client_sees_only_own_project_deliverables(
        self, api_client, client_headers, project, sample_deliverables, admin_user,
    ):
        other_client = User.objects.create_user(
            username='other2@del.com', email='other2@del.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other_client, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        other_project = Project.objects.create(
            name='Secret Project', client=other_client, status=Project.STATUS_ACTIVE,
        )
        Deliverable.objects.create(
            project=other_project, uploaded_by=admin_user,
            title='Secret', category='other',
            file=_make_file('secret.pdf'),
        )

        resp = api_client.get('/api/accounts/deliverables/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert all(item['project_name'] == 'Del Project' for item in data)

    def test_general_endpoint_includes_project_id_and_name(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        resp = api_client.get('/api/accounts/deliverables/', **admin_headers)

        for item in resp.json():
            assert 'project_id' in item
            assert 'project_name' in item

    def test_general_endpoint_filters_by_category(
        self, api_client, admin_headers, project, sample_deliverables,
    ):
        resp = api_client.get(
            '/api/accounts/deliverables/?category=credentials', **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['category'] == 'credentials'

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get('/api/accounts/deliverables/')

        assert resp.status_code == 401
