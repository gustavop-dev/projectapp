import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import (
    BugComment,
    BugReport,
    Deliverable,
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
        username='admin@bug.com', email='admin@bug.com', password='adminpass1',
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
        'email': 'admin@bug.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@bug.com', email='client@bug.com', password='clientpass1',
        first_name='Carlos', last_name='López',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='BugCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@bug.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Bug Project', client=client_user,
        status=Project.STATUS_ACTIVE, progress=0,
    )


@pytest.fixture
def deliverable(project, client_user):
    return Deliverable.objects.create(
        project=project, title='Main deliverable', category=Deliverable.CATEGORY_OTHER,
        file=None, uploaded_by=client_user,
    )


@pytest.fixture
def sample_bugs(project, client_user, deliverable):
    bugs = []
    bugs.append(BugReport.objects.create(
        deliverable=deliverable, reported_by=client_user,
        title='Button does not work', description='Click does nothing.',
        severity=BugReport.SEVERITY_CRITICAL,
        steps_to_reproduce=['Open page', 'Click button', 'Nothing happens'],
        expected_behavior='Should submit form.',
        actual_behavior='Nothing happens.',
        environment=BugReport.ENV_PRODUCTION,
        device_browser='Chrome / macOS',
        status=BugReport.STATUS_REPORTED,
    ))
    bugs.append(BugReport.objects.create(
        deliverable=deliverable, reported_by=client_user,
        title='Slow page load', severity=BugReport.SEVERITY_HIGH,
        status=BugReport.STATUS_FIXING,
        admin_response='Working on optimization.',
    ))
    bugs.append(BugReport.objects.create(
        deliverable=deliverable, reported_by=client_user,
        title='Typo in footer', severity=BugReport.SEVERITY_LOW,
        status=BugReport.STATUS_RESOLVED,
        admin_response='Fixed.',
    ))
    return bugs


def _make_test_image(width=200, height=200):
    img = Image.new('RGB', (width, height), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('bug.png', buf.read(), content_type='image/png')


def _url(project_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/bug-reports/{suffix}'


def _detail_url(project_id, bug_id, suffix=''):
    return f'/api/accounts/projects/{project_id}/bug-reports/{bug_id}/{suffix}'


# =========================================================================
# List & Filter
# =========================================================================


@pytest.mark.django_db
class TestBugReportList:
    def test_admin_lists_all_bugs_for_project(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.get(_url(project.id), **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_client_lists_bugs_for_own_project(
        self, api_client, client_headers, project, sample_bugs,
    ):
        resp = api_client.get(_url(project.id), **client_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_by_status_returns_matching_only(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.get(f'{_url(project.id)}?status=reported', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['status'] == 'reported'

    def test_filter_by_severity_returns_matching_only(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.get(f'{_url(project.id)}?severity=critical', **admin_headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_unauthenticated_request_rejected(self, api_client, project):
        resp = api_client.get(_url(project.id))

        assert resp.status_code == 401

    def test_other_client_cannot_list_bugs(self, api_client, project):
        other = User.objects.create_user(
            username='other@bug.com', email='other@bug.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        client = APIClient()
        resp = client.post('/api/accounts/login/', {
            'email': 'other@bug.com', 'password': 'pass1234',
        })
        token = resp.json()['tokens']['access']

        resp = client.get(_url(project.id), HTTP_AUTHORIZATION=f'Bearer {token}')

        assert resp.status_code == 403


# =========================================================================
# Create
# =========================================================================


@pytest.mark.django_db
class TestBugReportCreate:
    def test_client_creates_bug_report_with_steps(
        self, api_client, client_headers, project, deliverable,
    ):
        resp = api_client.post(_url(project.id), {
            'deliverable_id': deliverable.id,
            'title': 'Login fails',
            'description': 'Cannot login with valid creds.',
            'severity': 'high',
            'steps_to_reproduce': ['Go to login', 'Enter creds', 'Click login', 'Error shown'],
            'expected_behavior': 'Should redirect to dashboard.',
            'actual_behavior': 'Shows 500 error.',
            'environment': 'production',
            'device_browser': 'Safari / iOS',
            'is_recurring': True,
        }, format='json', **client_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data['title'] == 'Login fails'
        assert data['severity'] == 'high'
        assert data['is_recurring'] is True
        assert data['status'] == 'reported'
        assert data['reported_by_name'] == 'Carlos López'
        assert len(data['steps_to_reproduce']) == 4

    def test_admin_creates_bug_report(
        self, api_client, admin_headers, project, deliverable,
    ):
        resp = api_client.post(_url(project.id), {
            'deliverable_id': deliverable.id,
            'title': 'Admin-found bug',
        }, format='json', **admin_headers)

        assert resp.status_code == 201

    def test_create_without_title_fails(
        self, api_client, client_headers, project, deliverable,
    ):
        resp = api_client.post(_url(project.id), {
            'deliverable_id': deliverable.id,
            'description': 'No title.',
        }, format='json', **client_headers)

        assert resp.status_code == 400

    def test_create_with_screenshot_saves_optimized_image(
        self, api_client, client_headers, project, deliverable,
    ):
        image = _make_test_image(2000, 1500)

        resp = api_client.post(
            _url(project.id),
            {
                'deliverable_id': deliverable.id,
                'title': 'With screenshot',
                'severity': 'medium',
                'environment': 'production',
                'is_recurring': 'false',
                'screenshot': image,
            },
            format='multipart', **client_headers,
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data['screenshot_url'] is not None
        assert data['screenshot_url'].endswith('.jpg')

    def test_create_without_deliverable_id_fails(
        self, api_client, client_headers, project,
    ):
        resp = api_client.post(_url(project.id), {
            'title': 'Missing deliverable',
        }, format='json', **client_headers)

        assert resp.status_code == 400

    def test_create_with_deliverable_from_other_project_fails(
        self, api_client, client_headers, project, admin_user,
    ):
        other = Project.objects.create(
            name='Other', client=admin_user, status=Project.STATUS_ACTIVE,
        )
        other_d = Deliverable.objects.create(
            project=other, title='Other D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=admin_user,
        )
        resp = api_client.post(_url(project.id), {
            'deliverable_id': other_d.id,
            'title': 'Wrong scope',
        }, format='json', **client_headers)

        assert resp.status_code == 400


# =========================================================================
# Detail
# =========================================================================


@pytest.mark.django_db
class TestBugReportDetail:
    def test_admin_gets_detail_with_comments(
        self, api_client, admin_headers, project, sample_bugs, admin_user,
    ):
        bug = sample_bugs[0]
        BugComment.objects.create(
            bug_report=bug, user=admin_user, content='Looking into it.',
        )

        resp = api_client.get(_detail_url(project.id, bug.id), **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data['title'] == 'Button does not work'
        assert 'comments' in data
        assert len(data['comments']) == 1
        assert len(data['steps_to_reproduce']) == 3

    def test_client_gets_detail_for_own_project(
        self, api_client, client_headers, project, sample_bugs,
    ):
        resp = api_client.get(_detail_url(project.id, sample_bugs[0].id), **client_headers)

        assert resp.status_code == 200

    def test_nonexistent_bug_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.get(_detail_url(project.id, 99999), **admin_headers)

        assert resp.status_code == 404

    def test_client_does_not_see_internal_comments(
        self, api_client, client_headers, project, sample_bugs, admin_user,
    ):
        bug = sample_bugs[0]
        BugComment.objects.create(
            bug_report=bug, user=admin_user, content='Internal', is_internal=True,
        )
        BugComment.objects.create(
            bug_report=bug, user=admin_user, content='Public', is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, bug.id), **client_headers)

        comments = resp.json()['comments']
        assert len(comments) == 1
        assert comments[0]['content'] == 'Public'

    def test_admin_sees_all_comments_including_internal(
        self, api_client, admin_headers, project, sample_bugs, admin_user,
    ):
        bug = sample_bugs[0]
        BugComment.objects.create(
            bug_report=bug, user=admin_user, content='Internal', is_internal=True,
        )
        BugComment.objects.create(
            bug_report=bug, user=admin_user, content='Public', is_internal=False,
        )

        resp = api_client.get(_detail_url(project.id, bug.id), **admin_headers)

        assert len(resp.json()['comments']) == 2


# =========================================================================
# Delete
# =========================================================================


@pytest.mark.django_db
class TestBugReportDelete:
    def test_admin_deletes_bug_report(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        resp = api_client.delete(_detail_url(project.id, bug.id), **admin_headers)

        assert resp.status_code == 200
        assert resp.json()['detail'] == 'Reporte de bug archivado.'
        bug.refresh_from_db()
        assert bug.is_archived is True

    def test_client_cannot_delete_bug_report(
        self, api_client, client_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        resp = api_client.delete(_detail_url(project.id, bug.id), **client_headers)

        assert resp.status_code == 403
        assert BugReport.objects.filter(id=bug.id).exists()


# =========================================================================
# Evaluate (admin only)
# =========================================================================


@pytest.mark.django_db
class TestBugReportEvaluate:
    def test_admin_confirms_bug(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        resp = api_client.post(
            _detail_url(project.id, bug.id, 'evaluate/'),
            {'status': 'confirmed', 'admin_response': 'Confirmed, will fix ASAP.'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'confirmed'
        assert data['admin_response'] == 'Confirmed, will fix ASAP.'

    def test_admin_resolves_bug(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        resp = api_client.post(
            _detail_url(project.id, bug.id, 'evaluate/'),
            {'status': 'resolved', 'admin_response': 'Fixed in v2.1.'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'resolved'

    def test_admin_marks_not_reproducible(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        resp = api_client.post(
            _detail_url(project.id, bug.id, 'evaluate/'),
            {'status': 'not_reproducible', 'admin_response': 'Cannot reproduce on our end.'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'not_reproducible'

    def test_admin_marks_duplicate_with_linked_bug(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        original = sample_bugs[0]
        dup = sample_bugs[1]

        resp = api_client.post(
            _detail_url(project.id, dup.id, 'evaluate/'),
            {'status': 'duplicate', 'linked_bug_id': original.id},
            format='json', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['status'] == 'duplicate'
        assert resp.json()['linked_bug_id'] == original.id

    def test_evaluate_rejects_linked_bug_from_other_deliverable(
        self, api_client, admin_headers, project, client_user, deliverable,
    ):
        other_d = Deliverable.objects.create(
            project=project, title='Other epic', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client_user,
        )
        local = BugReport.objects.create(
            deliverable=deliverable, reported_by=client_user,
            title='Here', severity=BugReport.SEVERITY_LOW,
        )
        foreign = BugReport.objects.create(
            deliverable=other_d, reported_by=client_user,
            title='There', severity=BugReport.SEVERITY_LOW,
        )

        resp = api_client.post(
            _detail_url(project.id, local.id, 'evaluate/'),
            {'status': 'duplicate', 'linked_bug_id': foreign.id},
            format='json', **admin_headers,
        )

        assert resp.status_code == 400

    def test_client_cannot_evaluate_bug(
        self, api_client, client_headers, project, sample_bugs,
    ):
        resp = api_client.post(
            _detail_url(project.id, sample_bugs[0].id, 'evaluate/'),
            {'status': 'confirmed'},
            format='json', **client_headers,
        )

        assert resp.status_code == 403

    def test_evaluate_nonexistent_bug_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _detail_url(project.id, 99999, 'evaluate/'),
            {'status': 'confirmed'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 404

    def test_evaluate_persists_changes_in_database(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        bug = sample_bugs[0]

        api_client.post(
            _detail_url(project.id, bug.id, 'evaluate/'),
            {'status': 'fixing', 'admin_response': 'On it.'},
            format='json', **admin_headers,
        )

        bug.refresh_from_db()
        assert bug.status == BugReport.STATUS_FIXING
        assert bug.admin_response == 'On it.'


# =========================================================================
# Comments
# =========================================================================


@pytest.mark.django_db
class TestBugReportComments:
    def test_admin_adds_public_comment(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.post(
            _detail_url(project.id, sample_bugs[0].id, 'comments/'),
            {'content': 'Will investigate.', 'is_internal': False},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['content'] == 'Will investigate.'
        assert resp.json()['is_internal'] is False

    def test_admin_adds_internal_comment(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.post(
            _detail_url(project.id, sample_bugs[0].id, 'comments/'),
            {'content': 'Need to check server logs', 'is_internal': True},
            format='json', **admin_headers,
        )

        assert resp.status_code == 201
        assert resp.json()['is_internal'] is True

    def test_client_adds_comment(
        self, api_client, client_headers, project, sample_bugs,
    ):
        resp = api_client.post(
            _detail_url(project.id, sample_bugs[0].id, 'comments/'),
            {'content': 'Still happening.'},
            format='json', **client_headers,
        )

        assert resp.status_code == 201

    def test_client_cannot_create_internal_comment(
        self, api_client, client_headers, project, sample_bugs,
    ):
        api_client.post(
            _detail_url(project.id, sample_bugs[0].id, 'comments/'),
            {'content': 'Trying internal', 'is_internal': True},
            format='json', **client_headers,
        )

        comment = BugComment.objects.last()
        assert comment.is_internal is False

    def test_comment_on_nonexistent_bug_returns_404(
        self, api_client, admin_headers, project,
    ):
        resp = api_client.post(
            _detail_url(project.id, 99999, 'comments/'),
            {'content': 'Ghost'},
            format='json', **admin_headers,
        )

        assert resp.status_code == 404


# =========================================================================
# General endpoint (all projects)
# =========================================================================


@pytest.mark.django_db
class TestBugReportAllView:
    def test_admin_sees_bugs_across_all_projects(
        self, api_client, admin_headers, project, sample_bugs, client_user,
    ):
        other_project = Project.objects.create(
            name='Other Project', client=client_user, status=Project.STATUS_ACTIVE,
        )
        other_d = Deliverable.objects.create(
            project=other_project, title='OD', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client_user,
        )
        BugReport.objects.create(
            deliverable=other_d, reported_by=client_user,
            title='Other bug', severity='low',
        )

        resp = api_client.get('/api/accounts/bug-reports/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        project_names = {item['project_name'] for item in data}
        assert 'Bug Project' in project_names
        assert 'Other Project' in project_names

    def test_client_sees_only_own_project_bugs(
        self, api_client, client_headers, project, sample_bugs, admin_user,
    ):
        other_client = User.objects.create_user(
            username='other2@bug.com', email='other2@bug.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=other_client, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        other_project = Project.objects.create(
            name='Secret Project', client=other_client, status=Project.STATUS_ACTIVE,
        )
        secret_d = Deliverable.objects.create(
            project=other_project, title='SD', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=other_client,
        )
        BugReport.objects.create(
            deliverable=secret_d, reported_by=other_client,
            title='Secret bug', severity='low',
        )

        resp = api_client.get('/api/accounts/bug-reports/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert all(item['project_name'] == 'Bug Project' for item in data)

    def test_general_endpoint_includes_project_id_and_name(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.get('/api/accounts/bug-reports/', **admin_headers)

        for item in resp.json():
            assert 'project_id' in item
            assert 'project_name' in item

    def test_general_endpoint_filters_by_status(
        self, api_client, admin_headers, project, sample_bugs,
    ):
        resp = api_client.get(
            '/api/accounts/bug-reports/?status=fixing', **admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['status'] == 'fixing'

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get('/api/accounts/bug-reports/')

        assert resp.status_code == 401


# =========================================================================
# Screenshot optimization (model-level)
# =========================================================================


@pytest.mark.django_db
class TestBugScreenshotOptimization:
    def test_screenshot_saved_as_jpeg(self, project, client_user, deliverable):
        image = _make_test_image(800, 600)

        bug = BugReport(
            deliverable=deliverable, reported_by=client_user,
            title='Screenshot test', severity='medium',
        )
        bug.screenshot = image
        bug.save()

        assert bug.screenshot.name.endswith('.jpg')

    def test_large_screenshot_resized_to_max_1200px(self, project, client_user, deliverable):
        image = _make_test_image(2400, 1800)

        bug = BugReport(
            deliverable=deliverable, reported_by=client_user,
            title='Large image', severity='medium',
        )
        bug.screenshot = image
        bug.save()

        saved_img = Image.open(bug.screenshot.path)
        assert max(saved_img.width, saved_img.height) <= 1200

    def test_bug_without_screenshot_saves_normally(self, project, client_user, deliverable):
        bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=client_user,
            title='No screenshot', severity='medium',
        )

        assert not bug.screenshot
        assert bug.id is not None
