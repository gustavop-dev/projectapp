import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import (
    Project,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
    RequirementComment,
    RequirementHistory,
    UserProfile,
)
from content.models.business_proposal import BusinessProposal

User = get_user_model()
MAX_REQUIREMENT_LIST_QUERIES = 6
REQUIREMENT_LIST_FIELDS = {
    'id', 'phase_id', 'phase_title', 'title', 'description', 'configuration', 'flow',
    'status', 'priority', 'order', 'source_epic_key', 'source_epic_title',
    'source_flow_key', 'synced_from_proposal', 'scope_item_id', 'scope_item_name',
    'scope_item_group_id', 'is_archived', 'archived_at', 'comments_count', 'created_at',
    'updated_at',
}


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
def default_phase(project):
    bp = BusinessProposal.objects.create(title='Board proposal', client_name='Carlos')
    return ProjectPhase.objects.create(project=project, business_proposal=bp, order=1)


@pytest.fixture
def sample_requirements(project, default_phase):
    reqs = []
    reqs.append(Requirement.objects.create(
        phase=default_phase, title='Task A', status='todo', priority='high', order=0,
    ))
    reqs.append(Requirement.objects.create(
        phase=default_phase, title='Task B', status='in_progress', priority='medium', order=0,
    ))
    reqs.append(Requirement.objects.create(
        phase=default_phase, title='Task C', status='done', priority='low', order=0,
    ))
    return reqs


def _url(project_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/requirements/{suffix}'


def _detail_url(project_id, req_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/requirements/{req_id}/{suffix}'


def _create_requirement_list_rows(project, count, *, comment_user=None):
    start = BusinessProposal.objects.filter(title__startswith='Budget proposal ').count()
    proposals = [
        BusinessProposal(
            title=f'Budget proposal {index}',
            client_name='Carlos',
            slug=f'budget-proposal-{index}',
        )
        for index in range(start, start + count)
    ]
    persisted_proposals = BusinessProposal.objects.bulk_create(proposals)
    phases = [
        ProjectPhase(project=project, business_proposal=proposal, order=index + 10)
        for index, proposal in enumerate(persisted_proposals)
    ]
    persisted_phases = ProjectPhase.objects.bulk_create(phases)
    scope_items = [
        ProjectScopeItem(
            phase=phase,
            source_item_id=f'budget-scope-{phase.id}',
            name=f'Budget scope {phase.id}',
            group_id='budget',
            group_title='Budget',
        )
        for phase in persisted_phases
    ]
    persisted_scope_items = ProjectScopeItem.objects.bulk_create(scope_items)
    requirements = Requirement.objects.bulk_create([
        Requirement(
            phase=phase,
            scope_item=scope_item,
            title=f'Budget requirement {phase.id}',
            source_flow_key=f'budget-requirement-{phase.id}',
        )
        for phase, scope_item in zip(persisted_phases, persisted_scope_items)
    ])
    if comment_user:
        RequirementComment.objects.bulk_create([
            RequirementComment(
                requirement=requirement,
                user=comment_user,
                content=f'Budget comment {requirement.id}',
            )
            for requirement in requirements
        ])


def _create_serialized_requirement(project, admin_user):
    proposal = BusinessProposal.objects.create(title='Discovery proposal', client_name='Carlos')
    phase = ProjectPhase.objects.create(project=project, business_proposal=proposal, order=2)
    scope_item = ProjectScopeItem.objects.create(
        phase=phase,
        source_item_id='discovery-scope',
        name='Discovery scope',
        group_id='discovery',
        group_title='Discovery',
    )
    requirement = Requirement.objects.create(
        phase=phase,
        scope_item=scope_item,
        title='Mapped requirement',
        description='Description',
        configuration='Admin only',
        flow='Open then review',
        status=Requirement.STATUS_IN_PROGRESS,
        priority=Requirement.PRIORITY_CRITICAL,
        order=3,
        source_epic_key='EPIC-1',
        source_epic_title='Discovery',
        source_flow_key='FLOW-1',
        synced_from_proposal=True,
    )
    RequirementComment.objects.bulk_create([
        RequirementComment(
            requirement=requirement, user=admin_user, content='Public comment', is_internal=False,
        ),
        RequirementComment(
            requirement=requirement, user=admin_user, content='Internal comment', is_internal=True,
        ),
    ])
    return requirement, phase, scope_item


@pytest.mark.django_db
class TestRequirementList:
    def test_admin_lists_requirements_for_project(
        self, api_client, admin_headers, project, default_phase, sample_requirements,
    ):
        resp = api_client.get(_url(project.id), **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_client_lists_requirements_for_own_project(
        self, api_client, client_headers, project, default_phase, sample_requirements,
    ):
        resp = api_client.get(_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_unauthenticated_request_rejected(self, api_client, project, default_phase):
        resp = api_client.get(_url(project.id))

        assert resp.status_code == 401

    def test_other_client_cannot_list_requirements(self, api_client, project, default_phase):
        other = User.objects.create_user(username='other@r.com', email='other@r.com', password='pass1234')
        UserProfile.objects.create(user=other, role=UserProfile.ROLE_CLIENT, is_onboarded=True, profile_completed=True)
        client = APIClient()
        resp = client.post('/api/accounts/login/', {'email': 'other@r.com', 'password': 'pass1234'})
        token = resp.json()['tokens']['access']

        resp = client.get(_url(project.id), HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 403

    def test_requirement_list_preserves_serialized_fields(
        self, api_client, admin_headers, admin_user, project,
    ):
        """Fails if the optimized list projection omits a requirement serializer field."""
        requirement, phase, scope_item = _create_serialized_requirement(project, admin_user)

        response = api_client.get(_url(project.id), **admin_headers)

        assert response.status_code == 200
        data = response.json()[0]
        assert set(data) == REQUIREMENT_LIST_FIELDS
        expected = {
            'id': requirement.id,
            'phase_id': phase.id,
            'phase_title': 'Discovery proposal',
            'title': 'Mapped requirement',
            'description': 'Description',
            'configuration': 'Admin only',
            'flow': 'Open then review',
            'status': Requirement.STATUS_IN_PROGRESS,
            'priority': Requirement.PRIORITY_CRITICAL,
            'order': 3,
            'source_epic_key': 'EPIC-1',
            'source_epic_title': 'Discovery',
            'source_flow_key': 'FLOW-1',
            'synced_from_proposal': True,
            'scope_item_id': scope_item.id,
            'scope_item_name': 'Discovery scope',
            'scope_item_group_id': 'discovery',
            'is_archived': False,
            'archived_at': None,
            'comments_count': 2,
        }
        assert {key: data[key] for key in expected} == expected
        assert data['created_at'] is not None
        assert data['updated_at'] is not None

    def test_requirement_list_query_budget_is_constant(
        self, api_client, admin_headers, admin_user, project,
    ):
        """Fails if each listed requirement again loads comments or its proposal."""
        _create_requirement_list_rows(project, 1)

        with CaptureQueriesContext(connection) as one_requirement_queries:
            one_requirement_response = api_client.get(_url(project.id), **admin_headers)

        _create_requirement_list_rows(project, 49, comment_user=admin_user)

        with CaptureQueriesContext(connection) as fifty_requirement_queries:
            fifty_requirement_response = api_client.get(_url(project.id), **admin_headers)

        assert one_requirement_response.status_code == 200
        assert fifty_requirement_response.status_code == 200
        assert len(one_requirement_response.json()) == 1
        assert len(fifty_requirement_response.json()) == 50
        assert len(one_requirement_queries) == len(fifty_requirement_queries)
        assert len(fifty_requirement_queries) <= MAX_REQUIREMENT_LIST_QUERIES


@pytest.mark.django_db
class TestRequirementCreate:
    def test_admin_creates_requirement(self, api_client, admin_headers, project, default_phase):
        resp = api_client.post(_url(project.id), {
            'title': 'New Task',
            'description': 'Do something.',
            'priority': 'high',
            'status': 'todo',
            'configuration': 'Solo rol: Admin',
            'flow': 'Admin abre panel → crea tarea.',
            'phase_id': default_phase.id,
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'New Task'
        assert data['priority'] == 'high'
        assert data['configuration'] == 'Solo rol: Admin'
        assert data['flow'] == 'Admin abre panel → crea tarea.'
        assert data['comments_count'] == 0
        assert data['phase_title'] == 'Board proposal'

    def test_create_requirement_recalculates_project_progress(
        self, api_client, admin_headers, project, default_phase,
    ):
        Requirement.objects.create(phase=default_phase, title='Done', status='done', order=0)

        api_client.post(_url(project.id), {
            'title': 'New Todo', 'status': 'todo', 'phase_id': default_phase.id,
        }, format='json', **admin_headers)

        project.refresh_from_db()
        assert project.progress == 50

    def test_client_cannot_create_requirement(self, api_client, client_headers, project, default_phase):
        resp = api_client.post(_url(project.id), {
            'title': 'Forbidden', 'phase_id': default_phase.id,
        }, format='json', **client_headers)

        assert resp.status_code == 403


@pytest.mark.django_db
class TestRequirementDetail:
    def test_admin_gets_requirement_detail_with_history(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.get(_detail_url(project.id, req.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Task A'
        assert 'comments' in data
        assert 'history' in data

    def test_admin_updates_requirement(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.patch(
            _detail_url(project.id, req.id),
            {'title': 'Updated Task A', 'priority': 'critical'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['title'] == 'Updated Task A'
        assert resp.json()['priority'] == 'critical'

    def test_admin_deletes_requirement(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.delete(_detail_url(project.id, req.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['detail'] == 'Requerimiento archivado.'
        req.refresh_from_db()
        assert req.is_archived is True

    def test_delete_requirement_recalculates_project_progress(self, api_client, admin_headers, project, sample_requirements):
        api_client.delete(
            _detail_url(project.id, sample_requirements[0].id),
            **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 50

    def test_client_cannot_update_requirement(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]
        resp = api_client.patch(
            _detail_url(project.id, req.id),
            {'title': 'Hacked'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_nonexistent_requirement_returns_404(self, api_client, admin_headers, project, default_phase):
        resp = api_client.get(_detail_url(project.id, 99999), **admin_headers)

        assert resp.status_code == 404


@pytest.mark.django_db
class TestRequirementMove:
    def test_admin_moves_requirement_to_different_column(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.id, 'move/'),
            {'status': 'in_progress', 'order': 0},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'in_progress'
        assert resp.json()['comments_count'] == 0
        assert resp.json()['phase_title'] == 'Board proposal'

    def test_move_creates_history_entry(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.id, 'move/'),
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
            _detail_url(project.id, req.id, 'move/'),
            {'status': 'done', 'order': 0},
            format='json', **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 67

    def test_client_cannot_move_requirement_freely(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.id, 'move/'),
            {'status': 'in_progress', 'order': 0},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_move_same_status_does_not_create_history(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.id, 'move/'),
            {'status': 'todo', 'order': 1},
            format='json', **admin_headers,
        )

        assert RequirementHistory.objects.filter(requirement=req).count() == 0


@pytest.mark.django_db
class TestRequirementBulkUpload:
    def test_bulk_upload_uses_unannotated_serializer_fallback(
        self, api_client, admin_headers, project, default_phase,
    ):
        """Fails if bulk-created requirements cannot serialize their unannotated relations."""
        response = api_client.post(
            f'{_url(project.id, "bulk/")}?phase_id={default_phase.id}',
            [{'title': 'Bulk requirement'}],
            format='json',
            **admin_headers,
        )

        assert response.status_code == 201
        data = response.json()['requirements'][0]
        assert data['title'] == 'Bulk requirement'
        assert data['comments_count'] == 0
        assert data['phase_title'] == 'Board proposal'


@pytest.mark.django_db
class TestRequirementComments:
    def test_admin_adds_public_comment(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.id, 'comments/'),
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
            _detail_url(project.id, req.id, 'comments/'),
            {'content': 'Internal note', 'is_internal': True},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['is_internal'] is True

    def test_client_adds_comment(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        resp = api_client.post(
            _detail_url(project.id, req.id, 'comments/'),
            {'content': 'Client feedback'},
            format='json', **client_headers,
        )

        assert resp.status_code == 201

    def test_client_cannot_create_internal_comment(self, api_client, client_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.post(
            _detail_url(project.id, req.id, 'comments/'),
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

        resp = api_client.get(_detail_url(project.id, req.id), **client_headers)

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

        resp = api_client.get(_detail_url(project.id, req.id), **admin_headers)

        comments = resp.json()['comments']
        assert len(comments) == 2


@pytest.mark.django_db
class TestProgressSync:
    def test_status_change_via_patch_recalculates_progress(self, api_client, admin_headers, project, sample_requirements):
        req = sample_requirements[0]

        api_client.patch(
            _detail_url(project.id, req.id),
            {'status': 'done'},
            format='json', **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 67
