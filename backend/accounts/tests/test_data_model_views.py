"""
API endpoint tests for data model entity views:
  - deliverable_data_model_entities_view
  - project_data_model_entities_view
  - project_data_model_template_view
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    DataModelEntity,
    Deliverable,
    Project,
    ProjectDataModelEntity,
    UserProfile,
)

User = get_user_model()


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@dmv.com', email='admin@dmv.com', password='adminpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN,
        is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@dmv.com', email='client@dmv.com', password='clientpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        created_by=admin_user,
    )
    return user


@pytest.fixture
def other_client(admin_user):
    """A client that does NOT own the project (should get 403)."""
    user = User.objects.create_user(
        username='other@dmv.com', email='other@dmv.com', password='otherpass',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, created_by=admin_user,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@dmv.com', 'password': 'adminpass',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@dmv.com', 'password': 'clientpass',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def other_client_headers(api_client, other_client):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'other@dmv.com', 'password': 'otherpass',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='DM View Project', client=client_user, status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def deliverable(project, admin_user):
    return Deliverable.objects.create(
        project=project,
        title='Test Deliverable',
        category=Deliverable.CATEGORY_DOCUMENTS,
        file=None,
        uploaded_by=admin_user,
    )


def _del_entity_url(project_id, deliverable_id):
    return f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/data-model-entities/'


def _proj_entity_url(project_id):
    return f'/api/accounts/projects/{project_id}/data-model-entities/'


def _template_url(project_id):
    return f'/api/accounts/projects/{project_id}/data-model-entities/template/'


# =========================================================================
# GET /projects/{id}/deliverables/{id}/data-model-entities/
# =========================================================================


@pytest.mark.django_db
class TestDeliverableDataModelEntitiesGet:
    def test_admin_gets_entity_list_for_deliverable(
        self, api_client, admin_headers, project, deliverable, admin_user,
    ):
        DataModelEntity.objects.create(
            deliverable=deliverable, name='User',
            description='A user', key_fields='id, email',
            source_entity_name='User',
        )

        resp = api_client.get(
            _del_entity_url(project.id, deliverable.id), **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'User'
        assert 'id' in data[0]
        assert 'description' in data[0]
        assert 'key_fields' in data[0]

    def test_client_gets_entity_list_for_own_project_deliverable(
        self, api_client, client_headers, project, deliverable,
    ):
        DataModelEntity.objects.create(
            deliverable=deliverable, name='Order',
        )

        resp = api_client.get(
            _del_entity_url(project.id, deliverable.id), **client_headers,
        )

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_archived_entities_are_excluded(
        self, api_client, admin_headers, project, deliverable,
    ):
        DataModelEntity.objects.create(
            deliverable=deliverable, name='Active',
        )
        DataModelEntity.objects.create(
            deliverable=deliverable, name='Archived', is_archived=True,
        )

        resp = api_client.get(
            _del_entity_url(project.id, deliverable.id), **admin_headers,
        )

        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Active'

    def test_returns_empty_list_when_no_entities(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.get(
            _del_entity_url(project.id, deliverable.id), **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_other_client_gets_403(
        self, api_client, other_client_headers, project, deliverable, other_client,
    ):
        resp = api_client.get(
            _del_entity_url(project.id, deliverable.id), **other_client_headers,
        )

        assert resp.status_code == 403

    def test_unauthenticated_gets_401(
        self, api_client, project, deliverable,
    ):
        resp = api_client.get(_del_entity_url(project.id, deliverable.id))

        assert resp.status_code == 401


# =========================================================================
# GET /projects/{id}/data-model-entities/
# =========================================================================


@pytest.mark.django_db
class TestProjectDataModelEntitiesGet:
    def test_admin_gets_project_entity_list(
        self, api_client, admin_headers, project,
    ):
        ProjectDataModelEntity.objects.create(
            project=project, name='Invoice',
            description='Invoice entity', relationship='1:N with Customer',
        )

        resp = api_client.get(_proj_entity_url(project.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Invoice'
        assert data[0]['relationship'] == '1:N with Customer'

    def test_client_gets_own_project_entity_list(
        self, api_client, client_headers, project,
    ):
        ProjectDataModelEntity.objects.create(project=project, name='Cart')

        resp = api_client.get(_proj_entity_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_returns_empty_list_when_no_entities(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_proj_entity_url(project.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json() == []

    def test_other_client_gets_403(
        self, api_client, other_client_headers, project, other_client,
    ):
        resp = api_client.get(_proj_entity_url(project.id), **other_client_headers)

        assert resp.status_code == 403


# =========================================================================
# POST /projects/{id}/data-model-entities/
# =========================================================================


@pytest.mark.django_db
class TestProjectDataModelEntitiesPost:
    def test_admin_uploads_entities_returns_201(
        self, api_client, admin_headers, project,
    ):
        payload = {
            'entities': [
                {'name': 'User', 'description': 'A user', 'keyFields': 'id, email'},
                {'name': 'Product', 'relationship': '1:N with Order'},
            ],
        }

        resp = api_client.post(
            _proj_entity_url(project.id), payload, format='json', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 2
        names = {e['name'] for e in data}
        assert names == {'User', 'Product'}

    def test_upload_replaces_existing_entities(
        self, api_client, admin_headers, project,
    ):
        ProjectDataModelEntity.objects.create(project=project, name='OldEntity')

        payload = {'entities': [{'name': 'NewEntity'}]}
        resp = api_client.post(
            _proj_entity_url(project.id), payload, format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert ProjectDataModelEntity.objects.filter(project=project, name='OldEntity').count() == 0
        assert ProjectDataModelEntity.objects.filter(project=project, name='NewEntity').count() == 1

    def test_client_post_returns_403(
        self, api_client, client_headers, project,
    ):
        payload = {'entities': [{'name': 'Forbidden'}]}

        resp = api_client.post(
            _proj_entity_url(project.id), payload, format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_missing_entities_key_returns_400(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _proj_entity_url(project.id), {}, format='json', **admin_headers,
        )

        assert resp.status_code == 400
        assert 'entities' in resp.json()

    def test_entity_missing_name_returns_400(
        self, api_client, admin_headers, project,
    ):
        payload = {'entities': [{'description': 'missing name'}]}

        resp = api_client.post(
            _proj_entity_url(project.id), payload, format='json', **admin_headers,
        )

        assert resp.status_code == 400

    def test_empty_entities_list_clears_all_existing(
        self, api_client, admin_headers, project,
    ):
        ProjectDataModelEntity.objects.create(project=project, name='ToBeCleared')

        resp = api_client.post(
            _proj_entity_url(project.id), {'entities': []}, format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json() == []
        assert ProjectDataModelEntity.objects.filter(project=project).count() == 0

    def test_response_excludes_project_field(
        self, api_client, admin_headers, project,
    ):
        payload = {'entities': [{'name': 'Secure'}]}

        resp = api_client.post(
            _proj_entity_url(project.id), payload, format='json', **admin_headers,
        )

        data = resp.json()
        assert 'project' not in data[0]
        assert 'project_id' not in data[0]


# =========================================================================
# GET /projects/{id}/data-model-entities/template/
# =========================================================================


@pytest.mark.django_db
class TestProjectDataModelTemplateGet:
    def test_admin_gets_template_with_entities_key(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_template_url(project.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert 'entities' in data
        assert isinstance(data['entities'], list)
        assert len(data['entities']) >= 1

    def test_client_gets_template(
        self, api_client, client_headers, project,
    ):
        resp = api_client.get(_template_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert 'entities' in resp.json()

    def test_template_entity_has_required_keys(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_template_url(project.id), **admin_headers)

        entity = resp.json()['entities'][0]
        assert 'name' in entity

    def test_other_client_gets_403(
        self, api_client, other_client_headers, project, other_client,
    ):
        resp = api_client.get(_template_url(project.id), **other_client_headers)

        assert resp.status_code == 403
