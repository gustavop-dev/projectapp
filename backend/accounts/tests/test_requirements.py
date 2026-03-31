import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    Deliverable,
    Project,
    Requirement,
    RequirementComment,
    RequirementHistory,
    UserProfile,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@req.com', email='admin@req.com', password='adminpass1',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN,
        is_onboarded=True, profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'admin@req.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@req.com', email='client@req.com', password='clientpass1',
        first_name='Carlos', last_name='López',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='ReqCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@req.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Board Project', client=client_user,
        status=Project.STATUS_ACTIVE, progress=0,
    )


@pytest.fixture
def default_deliverable(project, client_user):
    return Deliverable.objects.create(
        project=project,
        title='Board deliverable',
        category=Deliverable.CATEGORY_OTHER,
        file=None,
        uploaded_by=client_user,
    )


@pytest.fixture
def sample_requirements(project, default_deliverable):
    reqs = []
    reqs.append(Requirement.objects.create(
        deliverable=default_deliverable, title='Task A', status='todo', priority='high', order=0,
    ))
    reqs.append(Requirement.objects.create(
        deliverable=default_deliverable, title='Task B', status='in_progress', priority='medium', order=0,
    ))
    reqs.append(Requirement.objects.create(
        deliverable=default_deliverable, title='Task C', status='done', priority='low', order=0,
    ))
    return reqs


def _url(project_id, deliverable_id, suffix=''):
    return (
        f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/requirements/{suffix}'
    )


def _detail_url(project_id, deliverable_id, req_id, suffix=''):
    return (
        f'/api/accounts/projects/{project_id}/deliverables/{deliverable_id}/'
        f'requirements/{req_id}/{suffix}'
    )


@pytest.mark.django_db
class TestRequirementList:
    def test_admin_lists_requirements_for_project(
        self, api_client, admin_headers, project, default_deliverable, sample_requirements,
    ):
        resp = api_client.get(_url(project.id, default_deliverable.id), **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_client_lists_requirements_for_own_project(
        self, api_client, client_headers, project, default_deliverable, sample_requirements,
    ):
        resp = api_client.get(_url(project.id, default_deliverable.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_unauthenticated_request_rejected(self, api_client, project, default_deliverable):
        resp = api_client.get(_url(project.id, default_deliverable.id))

        assert resp.status_code == 401

    def test_other_client_cannot_list_requirements(self, api_client, project, default_deliverable):
        other = User.objects.create_user(username='other@r.com', email='other@r.com', password='pass1234')
        UserProfile.objects.create(user=other, role=UserProfile.ROLE_CLIENT, is_onboarded=True, profile_completed=True)
        client = APIClient()
        resp = client.post('/api/accounts/login/', {'email': 'other@r.com', 'password': 'pass1234'})
        token = resp.json()['tokens']['access']

        resp = client.get(_url(project.id, default_deliverable.id), HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 403


@pytest.mark.django_db
class TestRequirementCreate:
    def test_admin_creates_requirement(self, api_client, admin_headers, project, default_deliverable):
        resp = api_client.post(_url(project.id, default_deliverable.id), {
            'title': 'New Task',
            'description': 'Do something.',
            'priority': 'high',
            'status': 'todo',
            'configuration': 'Solo rol: Admin',
            'flow': 'Admin abre panel → crea tarea.',
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'New Task'
        assert data['priority'] == 'high'
        assert data['configuration'] == 'Solo rol: Admin'
        assert data['flow'] == 'Admin abre panel → crea tarea.'

    def test_create_requirement_recalculates_project_progress(
        self, api_client, admin_headers, project, default_deliverable,
    ):
        Requirement.objects.create(deliverable=default_deliverable, title='Done', status='done', order=0)

        api_client.post(_url(project.id, default_deliverable.id), {
            'title': 'New Todo', 'status': 'todo',
        }, format='json', **admin_headers)

        project.refresh_from_db()
        assert project.progress == 50

    def test_client_cannot_create_requirement(self, api_client, client_headers, project, default_deliverable):
        resp = api_client.post(_url(project.id, default_deliverable.id), {
            'title': 'Forbidden',
        }, format='json', **client_headers)

        assert resp.status_code == 403


@pytest.mark.django_db
class TestRequirementDetail:
    def test_admin_gets_requirement_detail_with_history(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.get(_detail_url(project.id, req.deliverable_id, req.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Task A'
        assert 'comments' in data
        assert 'history' in data

    def test_admin_updates_requirement(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.patch(
            _detail_url(project.id, req.deliverable_id, req.id),
            {'title': 'Updated Task A', 'priority': 'critical'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['title'] == 'Updated Task A'
        assert resp.json()['priority'] == 'critical'

    def test_admin_deletes_requirement(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.delete(_detail_url(project.id, req.deliverable_id, req.id), **admin_headers)

        assert resp.status_code == 200
        assert not Requirement.objects.filter(id=req.id).exists()

    def test_delete_requirement_recalculates_project_progress(self, api_client, admin_headers, project, sample_requirements):
        api_client.delete(
            _detail_url(project.id, sample_requirements[0].deliverable_id, sample_requirements[0].id),
            **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 50

    def test_client_cannot_update_requirement(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.patch(
            _detail_url(project.id, req.deliverable_id, req.id),
            {'title': 'Hacked'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_nonexistent_requirement_returns_404(self, api_client, admin_headers, project, default_deliverable):
        resp = api_client.get(_detail_url(project.id, default_deliverable.id, 99999), **admin_headers)

        assert resp.status_code == 404


@pytest.mark.django_db
class TestRequirementMove:
    def test_admin_moves_requirement_to_different_column(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'move/'),
            {'status': 'in_progress', 'order': 0},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'in_progress'

    def test_move_creates_history_entry(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'move/'),
            {'status': 'in_review', 'order': 0},
            format='json', **admin_headers,
        )

        history = RequirementHistory.objects.filter(requirement=req)
        assert history.count() == 1
        entry = history.first()
        assert entry.from_status == 'todo'
        assert entry.to_status == 'in_review'

    def test_move_to_done_recalculates_project_progress(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'move/'),
            {'status': 'done', 'order': 0},
            format='json', **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 67

    def test_client_cannot_move_requirement_freely(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'move/'),
            {'status': 'in_progress', 'order': 0},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_move_same_status_does_not_create_history(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'move/'),
            {'status': 'todo', 'order': 1},
            format='json', **admin_headers,
        )

        assert RequirementHistory.objects.filter(requirement=req).count() == 0


@pytest.mark.django_db
class TestRequirementComments:
    def test_admin_adds_public_comment(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'comments/'),
            {'content': 'Looking good!', 'is_internal': False},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['content'] == 'Looking good!'
        assert data['is_internal'] is False

    def test_admin_adds_internal_comment(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'comments/'),
            {'content': 'Internal note', 'is_internal': True},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['is_internal'] is True

    def test_client_adds_comment(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'comments/'),
            {'content': 'Client feedback'},
            format='json', **client_headers,
        )

        assert resp.status_code == 201

    def test_client_cannot_create_internal_comment(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.deliverable_id, req.id, 'comments/'),
            {'content': 'Trying internal', 'is_internal': True},
            format='json', **client_headers,
        )

        comment = RequirementComment.objects.last()
        assert comment.is_internal is False

    def test_client_does_not_see_internal_comments_in_detail(self, api_client, admin_headers, client_headers, project, sample_requirements, admin_user):
        req = sample_requirements[0]
        RequirementComment.objects.create(
            requirement=req, user=admin_user, content='Secret', is_internal=True,
        )
        RequirementComment.objects.create(
            requirement=req, user=admin_user, content='Public', is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, req.deliverable_id, req.id), **client_headers)

        comments = resp.json()['comments']
        assert len(comments) == 1
        assert comments[0]['content'] == 'Public'

    def test_admin_sees_all_comments_including_internal(self, api_client, admin_headers, project, sample_requirements, admin_user):
        req = sample_requirements[0]
        RequirementComment.objects.create(
            requirement=req, user=admin_user, content='Secret', is_internal=True,
        )
        RequirementComment.objects.create(
            requirement=req, user=admin_user, content='Public', is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, req.deliverable_id, req.id), **admin_headers)

        comments = resp.json()['comments']
        assert len(comments) == 2


@pytest.mark.django_db
class TestProgressSync:
    def test_status_change_via_patch_recalculates_progress(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.patch(
            _detail_url(project.id, req.deliverable_id, req.id),
            {'status': 'done'},
            format='json', **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 67
