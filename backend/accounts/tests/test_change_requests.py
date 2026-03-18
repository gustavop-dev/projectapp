import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import (
    ChangeRequest,
    ChangeRequestComment,
    Project,
    Requirement,
    UserProfile,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@cr.com', email='admin@cr.com', password='adminpass1',
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
        'email': 'admin@cr.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@cr.com', email='client@cr.com', password='clientpass1',
        first_name='Carlos', last_name='López',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='CRCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@cr.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='CR Project', client=client_user,
        status=Project.STATUS_ACTIVE, progress=0,
    )


@pytest.fixture
def sample_change_requests(project, client_user, admin_user):
    crs = []
    crs.append(ChangeRequest.objects.create(
        project=project, created_by=client_user,
        title='Add dark mode', description='Support dark theme.',
        module_or_screen='UI', suggested_priority='medium',
        status=ChangeRequest.STATUS_PENDING,
    ))
    crs.append(ChangeRequest.objects.create(
        project=project, created_by=client_user,
        title='Change button color', suggested_priority='low',
        status=ChangeRequest.STATUS_APPROVED,
        admin_response='Approved, 1 day effort.', estimated_time='1 día',
    ))
    crs.append(ChangeRequest.objects.create(
        project=project, created_by=client_user,
        title='Add export PDF', suggested_priority='high',
        is_urgent=True, status=ChangeRequest.STATUS_EVALUATING,
    ))
    return crs


def _make_test_image(width=200, height=200):
    """Create a small in-memory PNG image for upload tests."""
    img = Image.new('RGB', (width, height), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('test.png', buf.read(), content_type='image/png')


def _url(project_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/change-requests/{suffix}'


def _detail_url(project_id, cr_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/change-requests/{cr_id}/{suffix}'


# =========================================================================
# List & Filter
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestList:
    def test_admin_lists_all_change_requests_for_project(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        resp = api_client.get(_url(project.id), **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_client_lists_change_requests_for_own_project(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        resp = api_client.get(_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_by_status_returns_matching_only(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        resp = api_client.get(f'{_url(project.id)}?status=pending', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['status'] == 'pending'

    def test_unauthenticated_request_rejected(self, api_client, project):
        resp = api_client.get(_url(project.id))

        assert resp.status_code == 401

    def test_other_client_cannot_list_change_requests(self, api_client, project):
        other = User.objects.create_user(
            username='other@cr.com', email='other@cr.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        client = APIClient()
        resp = client.post('/api/accounts/login/', {
            'email': 'other@cr.com', 'password': 'pass1234',
        })
        token = resp.json()['tokens']['access']

        resp = client.get(_url(project.id), HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 403


# =========================================================================
# Create
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestCreate:
    def test_client_creates_change_request(
        self, api_client, client_headers, project,
    ):
        resp = api_client.post(_url(project.id), {
            'title': 'New feature request',
            'description': 'I need this feature.',
            'module_or_screen': 'Dashboard',
            'suggested_priority': 'high',
            'is_urgent': True,
        }, format='json', **client_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'New feature request'
        assert data['suggested_priority'] == 'high'
        assert data['is_urgent'] is True
        assert data['status'] == 'pending'
        assert data['created_by_name'] == 'Carlos López'

    def test_admin_creates_change_request(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(_url(project.id), {
            'title': 'Admin-initiated change',
        }, format='json', **admin_headers)

        assert resp.status_code == 201
        assert resp.json()['title'] == 'Admin-initiated change'

    def test_create_without_title_fails(
        self, api_client, client_headers, project,
    ):
        resp = api_client.post(_url(project.id), {
            'description': 'No title provided.',
        }, format='json', **client_headers)

        assert resp.status_code == 400

    def test_create_with_screenshot_saves_optimized_image(
        self, api_client, client_headers, project,
    ):
        image = _make_test_image(2000, 1500)

        resp = api_client.post(
            _url(project.id),
            {
                'title': 'With screenshot',
                'description': 'See attached.',
                'suggested_priority': 'medium',
                'is_urgent': 'false',
                'screenshot': image,
            },
            format='multipart', **client_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['screenshot_url'] is not None
        assert data['screenshot_url'].endswith('.jpg')

        cr = ChangeRequest.objects.get(id=data['id'])
        assert cr.screenshot is not None

    def test_create_with_large_screenshot_resizes_below_max_dimension(
        self, api_client, client_headers, project,
    ):
        image = _make_test_image(3000, 2000)

        resp = api_client.post(
            _url(project.id),
            {
                'title': 'Large screenshot',
                'suggested_priority': 'medium',
                'is_urgent': 'false',
                'screenshot': image,
            },
            format='multipart', **client_headers,
        )

        assert resp.status_code == 201
        cr = ChangeRequest.objects.get(id=resp.json()['id'])
        img = Image.open(cr.screenshot.path)
        assert max(img.width, img.height) <= 1200


# =========================================================================
# Detail
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestDetail:
    def test_admin_gets_detail_with_comments(
        self, api_client, admin_headers, project, sample_change_requests, admin_user,
    ):
        cr = sample_change_requests[0]
        ChangeRequestComment.objects.create(
            change_request=cr, user=admin_user, content='Noted.',
        )

        resp = api_client.get(_detail_url(project.id, cr.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Add dark mode'
        assert 'comments' in data
        assert len(data['comments']) == 1

    def test_client_gets_detail_for_own_project(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.get(_detail_url(project.id, cr.id), **client_headers)

        assert resp.status_code == 200
        assert resp.json()['title'] == 'Add dark mode'

    def test_nonexistent_change_request_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_detail_url(project.id, 99999), **admin_headers)

        assert resp.status_code == 404

    def test_client_does_not_see_internal_comments(
        self, api_client, admin_headers, client_headers, project,
        sample_change_requests, admin_user,
    ):
        cr = sample_change_requests[0]
        ChangeRequestComment.objects.create(
            change_request=cr, user=admin_user, content='Internal note',
            is_internal=True,
        )
        ChangeRequestComment.objects.create(
            change_request=cr, user=admin_user, content='Public note',
            is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, cr.id), **client_headers)

        comments = resp.json()['comments']
        assert len(comments) == 1
        assert comments[0]['content'] == 'Public note'

    def test_admin_sees_all_comments_including_internal(
        self, api_client, admin_headers, project, sample_change_requests, admin_user,
    ):
        cr = sample_change_requests[0]
        ChangeRequestComment.objects.create(
            change_request=cr, user=admin_user, content='Internal', is_internal=True,
        )
        ChangeRequestComment.objects.create(
            change_request=cr, user=admin_user, content='Public', is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, cr.id), **admin_headers)

        assert len(resp.json()['comments']) == 2


# =========================================================================
# Delete
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestDelete:
    def test_admin_deletes_change_request(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.delete(_detail_url(project.id, cr.id), **admin_headers)

        assert resp.status_code == 200
        assert not ChangeRequest.objects.filter(id=cr.id).exists()

    def test_client_cannot_delete_change_request(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.delete(_detail_url(project.id, cr.id), **client_headers)

        assert resp.status_code == 403
        assert ChangeRequest.objects.filter(id=cr.id).exists()


# =========================================================================
# Evaluate (admin only)
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestEvaluate:
    def test_admin_evaluates_change_request(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'evaluate/'),
            {
                'status': 'approved',
                'admin_response': 'Looks good, we will implement.',
                'estimated_time': '3 días',
                'estimated_cost': 500000,
            },
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'approved'
        assert data['admin_response'] == 'Looks good, we will implement.'
        assert data['estimated_time'] == '3 días'
        assert float(data['estimated_cost']) == 500000.0

    def test_admin_rejects_change_request_with_response(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'evaluate/'),
            {
                'status': 'rejected',
                'admin_response': 'Out of scope for this phase.',
            },
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'rejected'

    def test_admin_marks_needs_clarification(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'evaluate/'),
            {'status': 'needs_clarification', 'admin_response': 'Could you elaborate?'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'needs_clarification'

    def test_client_cannot_evaluate_change_request(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'evaluate/'),
            {'status': 'approved'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_evaluate_nonexistent_cr_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _detail_url(project.id, 99999, 'evaluate/'),
            {'status': 'approved'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 404

    def test_evaluate_persists_changes_in_database(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        api_client.post(
            _detail_url(project.id, cr.id, 'evaluate/'),
            {'status': 'out_of_scope', 'admin_response': 'Not in scope.'},
            format='json', **admin_headers,
        )

        cr.refresh_from_db()
        assert cr.status == ChangeRequest.STATUS_OUT_OF_SCOPE
        assert cr.admin_response == 'Not in scope.'


# =========================================================================
# Comments
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestComments:
    def test_admin_adds_public_comment(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'comments/'),
            {'content': 'Thanks for the request.', 'is_internal': False},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['content'] == 'Thanks for the request.'
        assert data['is_internal'] is False

    def test_admin_adds_internal_comment(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'comments/'),
            {'content': 'Internal: check with designer', 'is_internal': True},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['is_internal'] is True

    def test_client_adds_comment(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        resp = api_client.post(
            _detail_url(project.id, cr.id, 'comments/'),
            {'content': 'Please prioritize this.'},
            format='json', **client_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['content'] == 'Please prioritize this.'

    def test_client_cannot_create_internal_comment(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        cr = sample_change_requests[0]

        api_client.post(
            _detail_url(project.id, cr.id, 'comments/'),
            {'content': 'Trying internal', 'is_internal': True},
            format='json', **client_headers,
        )

        comment = ChangeRequestComment.objects.last()
        assert comment.is_internal is False

    def test_comment_on_nonexistent_cr_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _detail_url(project.id, 99999, 'comments/'),
            {'content': 'Ghost comment'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 404


# =========================================================================
# Convert to Requirement
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestConvert:
    def test_admin_converts_approved_cr_to_requirement(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        approved_cr = sample_change_requests[1]
        assert approved_cr.status == ChangeRequest.STATUS_APPROVED

        resp = api_client.post(
            _detail_url(project.id, approved_cr.id, 'convert/'),
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['linked_requirement_id'] is not None

        req = Requirement.objects.get(id=data['linked_requirement_id'])
        assert req.title == approved_cr.title
        assert req.status == Requirement.STATUS_TODO
        assert req.priority == approved_cr.suggested_priority
        assert req.module == approved_cr.module_or_screen

    def test_convert_recalculates_project_progress(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        Requirement.objects.create(
            project=project, title='Existing Done', status='done', order=0,
        )
        approved_cr = sample_change_requests[1]

        api_client.post(
            _detail_url(project.id, approved_cr.id, 'convert/'),
            format='json', **admin_headers,
        )

        project.refresh_from_db()
        assert project.progress == 50

    def test_cannot_convert_non_approved_cr(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        pending_cr = sample_change_requests[0]
        assert pending_cr.status == ChangeRequest.STATUS_PENDING

        resp = api_client.post(
            _detail_url(project.id, pending_cr.id, 'convert/'),
            format='json', **admin_headers,
        )

        assert resp.status_code == 400

    def test_cannot_convert_already_converted_cr(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        approved_cr = sample_change_requests[1]

        api_client.post(
            _detail_url(project.id, approved_cr.id, 'convert/'),
            format='json', **admin_headers,
        )

        resp = api_client.post(
            _detail_url(project.id, approved_cr.id, 'convert/'),
            format='json', **admin_headers,
        )

        assert resp.status_code == 400

    def test_client_cannot_convert_change_request(
        self, api_client, client_headers, project, sample_change_requests,
    ):
        approved_cr = sample_change_requests[1]

        resp = api_client.post(
            _detail_url(project.id, approved_cr.id, 'convert/'),
            format='json', **client_headers,
        )

        assert resp.status_code == 403


# =========================================================================
# General endpoint (all projects)
# =========================================================================


@pytest.mark.django_db
class TestChangeRequestAllView:
    def test_admin_sees_change_requests_across_all_projects(
        self, api_client, admin_headers, project, sample_change_requests, client_user,
    ):
        other_project = Project.objects.create(
            name='Other Project', client=client_user, status=Project.STATUS_ACTIVE,
        )
        ChangeRequest.objects.create(
            project=other_project, created_by=client_user,
            title='Other project CR', suggested_priority='low',
        )

        resp = api_client.get('/api/accounts/change-requests/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        project_names = {item['project_name'] for item in data}
        assert 'CR Project' in project_names
        assert 'Other Project' in project_names

    def test_client_sees_only_own_project_change_requests(
        self, api_client, client_headers, project, sample_change_requests, admin_user,
    ):
        other_client = User.objects.create_user(
            username='other2@cr.com', email='other2@cr.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other_client, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        other_project = Project.objects.create(
            name='Secret Project', client=other_client, status=Project.STATUS_ACTIVE,
        )
        ChangeRequest.objects.create(
            project=other_project, created_by=other_client,
            title='Should not see', suggested_priority='low',
        )

        resp = api_client.get('/api/accounts/change-requests/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert all(item['project_name'] == 'CR Project' for item in data)

    def test_general_endpoint_includes_project_id_and_name(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        resp = api_client.get('/api/accounts/change-requests/', **admin_headers)

        data = resp.json()
        for item in data:
            assert 'project_id' in item
            assert 'project_name' in item
            assert item['project_id'] == project.id

    def test_general_endpoint_filters_by_status(
        self, api_client, admin_headers, project, sample_change_requests,
    ):
        resp = api_client.get(
            '/api/accounts/change-requests/?status=evaluating', **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['status'] == 'evaluating'

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get('/api/accounts/change-requests/')

        assert resp.status_code == 401


# =========================================================================
# Screenshot optimization (model-level)
# =========================================================================


@pytest.mark.django_db
class TestScreenshotOptimization:
    def test_screenshot_saved_as_jpeg(self, project, client_user):
        image = _make_test_image(800, 600)

        cr = ChangeRequest(
            project=project, created_by=client_user,
            title='Screenshot test', suggested_priority='medium',
        )
        cr.screenshot = image
        cr.save()

        assert cr.screenshot.name.endswith('.jpg')

    def test_large_screenshot_resized_to_max_1200px(self, project, client_user):
        image = _make_test_image(2400, 1800)

        cr = ChangeRequest(
            project=project, created_by=client_user,
            title='Large image test', suggested_priority='medium',
        )
        cr.screenshot = image
        cr.save()

        saved_img = Image.open(cr.screenshot.path)
        assert max(saved_img.width, saved_img.height) <= 1200

    def test_small_screenshot_not_upscaled(self, project, client_user):
        image = _make_test_image(400, 300)

        cr = ChangeRequest(
            project=project, created_by=client_user,
            title='Small image test', suggested_priority='medium',
        )
        cr.screenshot = image
        cr.save()

        saved_img = Image.open(cr.screenshot.path)
        assert saved_img.width == 400
        assert saved_img.height == 300

    def test_change_request_without_screenshot_saves_normally(self, project, client_user):
        cr = ChangeRequest.objects.create(
            project=project, created_by=client_user,
            title='No screenshot', suggested_priority='medium',
        )

        assert cr.screenshot.name == ''
        assert cr.id is not None
