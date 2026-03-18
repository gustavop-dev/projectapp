import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Project, UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@proj.com', email='admin@proj.com', password='adminpass1',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN,
        is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@proj.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@proj.com', email='client@proj.com', password='clientpass1',
        first_name='María', last_name='Torres',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='ClientCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@proj.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def sample_project(client_user):
    return Project.objects.create(
        name='Test Project', description='A test project.',
        client=client_user, status=Project.STATUS_ACTIVE,
        progress=0, start_date='2026-01-01', estimated_end_date='2026-06-01',
    )


@pytest.mark.django_db
class TestProjectList:
    def test_admin_lists_all_projects(self, api_client, admin_headers, sample_project):
        resp = api_client.get('/api/accounts/projects/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Test Project'
        assert data[0]['client_name'] == 'María Torres'

    def test_client_lists_only_own_projects(self, api_client, client_headers, sample_project):
        resp = api_client.get('/api/accounts/projects/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_client_does_not_see_other_client_projects(self, api_client, admin_user):
        other = User.objects.create_user(username='other@t.com', email='other@t.com', password='pass1234')
        UserProfile.objects.create(user=other, role=UserProfile.ROLE_CLIENT, is_onboarded=True, profile_completed=True)
        Project.objects.create(name='Other Project', client=other)

        first = User.objects.create_user(username='first@t.com', email='first@t.com', password='pass1234')
        UserProfile.objects.create(user=first, role=UserProfile.ROLE_CLIENT, is_onboarded=True, profile_completed=True)

        client = APIClient()
        resp = client.post('/api/accounts/login/', {'email': 'first@t.com', 'password': 'pass1234'})
        token = resp.json()['tokens']['access']
        resp = client.get('/api/accounts/projects/', HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_admin_filters_projects_by_client(self, api_client, admin_headers, sample_project, client_user):
        resp = api_client.get(f'/api/accounts/projects/?client={client_user.id}', **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_admin_filters_projects_by_status(self, api_client, admin_headers, sample_project):
        resp = api_client.get('/api/accounts/projects/?status=paused', **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get('/api/accounts/projects/')

        assert resp.status_code == 401


@pytest.mark.django_db
class TestProjectCreate:
    def test_admin_creates_project_for_client(self, api_client, admin_headers, client_user):
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'New Project',
            'description': 'Brand new project.',
            'client_id': client_user.id,
            'start_date': '2026-03-01',
            'estimated_end_date': '2026-09-01',
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['name'] == 'New Project'
        assert data['client_id'] == client_user.id
        assert data['status'] == 'active'

    def test_client_cannot_create_project(self, api_client, client_headers, client_user):
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Forbidden', 'client_id': client_user.id,
        }, format='json', **client_headers)

        assert resp.status_code == 403

    def test_create_project_rejects_nonexistent_client(self, api_client, admin_headers):
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Ghost', 'client_id': 99999,
        }, format='json', **admin_headers)

        assert resp.status_code == 400

    def test_create_project_rejects_admin_as_client(self, api_client, admin_headers, admin_user):
        resp = api_client.post('/api/accounts/projects/', {
            'name': 'Bad', 'client_id': admin_user.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 400


@pytest.mark.django_db
class TestProjectDetail:
    def test_admin_gets_project_detail(self, api_client, admin_headers, sample_project):
        resp = api_client.get(f'/api/accounts/projects/{sample_project.id}/', **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['name'] == 'Test Project'

    def test_owning_client_gets_project_detail(self, api_client, client_headers, sample_project):
        resp = api_client.get(f'/api/accounts/projects/{sample_project.id}/', **client_headers)

        assert resp.status_code == 200

    def test_nonexistent_project_returns_404(self, api_client, admin_headers):
        resp = api_client.get('/api/accounts/projects/99999/', **admin_headers)

        assert resp.status_code == 404


@pytest.mark.django_db
class TestProjectUpdate:
    def test_admin_updates_project(self, api_client, admin_headers, sample_project):
        resp = api_client.patch(
            f'/api/accounts/projects/{sample_project.id}/',
            {'name': 'Updated Name', 'status': 'paused'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['name'] == 'Updated Name'
        assert resp.json()['status'] == 'paused'

    def test_client_cannot_update_project(self, api_client, client_headers, sample_project):
        resp = api_client.patch(
            f'/api/accounts/projects/{sample_project.id}/',
            {'name': 'Hacked'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403


@pytest.mark.django_db
class TestProjectArchive:
    def test_admin_archives_project(self, api_client, admin_headers, sample_project):
        resp = api_client.delete(f'/api/accounts/projects/{sample_project.id}/', **admin_headers)

        assert resp.status_code == 200
        sample_project.refresh_from_db()
        assert sample_project.status == Project.STATUS_ARCHIVED

    def test_client_cannot_archive_project(self, api_client, client_headers, sample_project):
        resp = api_client.delete(f'/api/accounts/projects/{sample_project.id}/', **client_headers)

        assert resp.status_code == 403
