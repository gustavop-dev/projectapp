import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import (
    ChangeRequest,
    Notification,
    Project,
    UserProfile,
)
from accounts.services.notifications import notify, notify_project_admins, notify_project_client

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username='admin@notif.com', email='admin@notif.com', password='adminpass1',
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
        'email': 'admin@notif.com', 'password': 'adminpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def client_user(admin_user):
    user = User.objects.create_user(
        username='client@notif.com', email='client@notif.com', password='clientpass1',
        first_name='Carlos', last_name='López',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True,
        company_name='NotifCorp', created_by=admin_user,
    )
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@notif.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Notif Project', client=client_user,
        status=Project.STATUS_ACTIVE, progress=0,
    )


@pytest.fixture
def sample_notifications(admin_user, client_user, project):
    notifs = []
    notifs.append(Notification.objects.create(
        user=client_user, type=Notification.TYPE_CR_CREATED,
        title='Nueva solicitud', message='Test message.',
        project=project, related_object_type='change_request', related_object_id=1,
    ))
    notifs.append(Notification.objects.create(
        user=client_user, type=Notification.TYPE_BUG_REPORTED,
        title='Bug reportado', message='Bug message.',
        project=project, is_read=True,
    ))
    notifs.append(Notification.objects.create(
        user=client_user, type=Notification.TYPE_DELIVERABLE_UPLOADED,
        title='Nuevo entregable', project=project,
    ))
    notifs.append(Notification.objects.create(
        user=admin_user, type=Notification.TYPE_CR_CREATED,
        title='Admin notification', project=project,
    ))
    return notifs


# =========================================================================
# Notification Service
# =========================================================================


@pytest.mark.django_db
class TestNotificationService:
    def test_notify_creates_notification(self, client_user, project):
        notif = notify(
            user=client_user,
            type=Notification.TYPE_GENERAL,
            title='Test notification',
            message='Hello.',
            project=project,
        )

        assert notif.id is not None
        assert notif.user == client_user
        assert notif.title == 'Test notification'
        assert notif.is_read is False

    def test_notify_project_admins_creates_for_all_admins(self, admin_user, project):
        admin2 = User.objects.create_user(
            username='admin2@notif.com', email='admin2@notif.com', password='pass1234',
        )
        UserProfile.objects.create(
            user=admin2, role=UserProfile.ROLE_ADMIN,
            is_onboarded=True, profile_completed=True,
        )

        result = notify_project_admins(
            project, Notification.TYPE_BUG_REPORTED,
            'Bug reported', message='A bug was reported.',
        )

        assert len(result) == 2
        assert Notification.objects.filter(user=admin_user).count() == 1
        assert Notification.objects.filter(user=admin2).count() == 1

    def test_notify_project_admins_excludes_user(self, admin_user, project):
        result = notify_project_admins(
            project, Notification.TYPE_BUG_REPORTED,
            'Bug reported', exclude_user=admin_user,
        )

        assert len(result) == 0
        assert Notification.objects.filter(user=admin_user).count() == 0

    def test_notify_project_client_creates_for_client(self, client_user, project):
        result = notify_project_client(
            project, Notification.TYPE_DELIVERABLE_UPLOADED,
            'New deliverable', message='File uploaded.',
        )

        assert result is not None
        assert result.user == client_user

    def test_notify_project_client_excludes_user(self, client_user, project):
        result = notify_project_client(
            project, Notification.TYPE_GENERAL,
            'Self-excluded', exclude_user=client_user,
        )

        assert result is None


# =========================================================================
# Notification List View
# =========================================================================


@pytest.mark.django_db
class TestNotificationList:
    def test_user_lists_own_notifications(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get('/api/accounts/notifications/', **client_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_filter_unread_only(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get(
            '/api/accounts/notifications/?is_read=false', **client_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(not n['is_read'] for n in data)

    def test_filter_read_only(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get(
            '/api/accounts/notifications/?is_read=true', **client_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['is_read'] is True

    def test_limit_parameter(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get(
            '/api/accounts/notifications/?limit=1', **client_headers,
        )

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_user_does_not_see_other_user_notifications(
        self, api_client, admin_headers, sample_notifications,
    ):
        resp = api_client.get('/api/accounts/notifications/', **admin_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Admin notification'

    def test_notification_includes_project_name(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get('/api/accounts/notifications/', **client_headers)

        data = resp.json()
        assert all(n['project_name'] == 'Notif Project' for n in data)

    def test_unauthenticated_request_rejected(self, api_client):
        resp = api_client.get('/api/accounts/notifications/')

        assert resp.status_code == 401


# =========================================================================
# Unread Count
# =========================================================================


@pytest.mark.django_db
class TestNotificationUnreadCount:
    def test_returns_unread_count(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.get(
            '/api/accounts/notifications/unread-count/', **client_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['count'] == 2

    def test_returns_zero_when_all_read(
        self, api_client, admin_headers,
    ):
        resp = api_client.get(
            '/api/accounts/notifications/unread-count/', **admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['count'] == 0


# =========================================================================
# Mark Read
# =========================================================================


@pytest.mark.django_db
class TestNotificationMarkRead:
    def test_mark_single_notification_as_read(
        self, api_client, client_headers, sample_notifications,
    ):
        unread_notif = sample_notifications[0]
        assert unread_notif.is_read is False

        resp = api_client.post(
            f'/api/accounts/notifications/{unread_notif.id}/read/',
            **client_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['is_read'] is True

        unread_notif.refresh_from_db()
        assert unread_notif.is_read is True

    def test_cannot_mark_other_user_notification(
        self, api_client, admin_headers, sample_notifications,
    ):
        client_notif = sample_notifications[0]

        resp = api_client.post(
            f'/api/accounts/notifications/{client_notif.id}/read/',
            **admin_headers,
        )

        assert resp.status_code == 404

    def test_nonexistent_notification_returns_404(
        self, api_client, client_headers,
    ):
        resp = api_client.post(
            '/api/accounts/notifications/99999/read/',
            **client_headers,
        )

        assert resp.status_code == 404


# =========================================================================
# Mark All Read
# =========================================================================


@pytest.mark.django_db
class TestNotificationMarkAllRead:
    def test_marks_all_unread_as_read(
        self, api_client, client_headers, sample_notifications,
    ):
        resp = api_client.post(
            '/api/accounts/notifications/mark-all-read/',
            **client_headers,
        )

        assert resp.status_code == 200
        assert resp.json()['marked_read'] == 2

        remaining_unread = Notification.objects.filter(
            user=sample_notifications[0].user, is_read=False,
        ).count()
        assert remaining_unread == 0

    def test_does_not_affect_other_user_notifications(
        self, api_client, client_headers, sample_notifications,
    ):
        api_client.post(
            '/api/accounts/notifications/mark-all-read/',
            **client_headers,
        )

        admin_notif = sample_notifications[3]
        admin_notif.refresh_from_db()
        assert admin_notif.is_read is False


# =========================================================================
# Integration: CR create triggers notification
# =========================================================================


@pytest.mark.django_db
class TestNotificationIntegration:
    def test_cr_create_by_client_notifies_admins(
        self, api_client, client_headers, project, admin_user,
    ):
        api_client.post(
            f'/api/accounts/projects/{project.id}/change-requests/',
            {'title': 'New feature'},
            format='json', **client_headers,
        )

        admin_notifs = Notification.objects.filter(
            user=admin_user, type=Notification.TYPE_CR_CREATED,
        )
        assert admin_notifs.count() == 1
        assert 'New feature' in admin_notifs.first().title

    def test_cr_evaluate_notifies_client(
        self, api_client, admin_headers, client_headers, project, client_user,
    ):
        resp = api_client.post(
            f'/api/accounts/projects/{project.id}/change-requests/',
            {'title': 'Client request'},
            format='json', **client_headers,
        )
        cr_id = resp.json()['id']

        api_client.post(
            f'/api/accounts/projects/{project.id}/change-requests/{cr_id}/evaluate/',
            {'status': 'approved', 'admin_response': 'OK'},
            format='json', **admin_headers,
        )

        client_notifs = Notification.objects.filter(
            user=client_user, type=Notification.TYPE_CR_STATUS_CHANGED,
        )
        assert client_notifs.count() == 1

    def test_bug_report_by_client_notifies_admins(
        self, api_client, client_headers, project, admin_user,
    ):
        api_client.post(
            f'/api/accounts/projects/{project.id}/bug-reports/',
            {'title': 'Button broken', 'severity': 'high'},
            format='json', **client_headers,
        )

        admin_notifs = Notification.objects.filter(
            user=admin_user, type=Notification.TYPE_BUG_REPORTED,
        )
        assert admin_notifs.count() == 1

    def test_bug_evaluate_notifies_client(
        self, api_client, admin_headers, client_headers, project, client_user,
    ):
        resp = api_client.post(
            f'/api/accounts/projects/{project.id}/bug-reports/',
            {'title': 'Some bug', 'severity': 'medium'},
            format='json', **client_headers,
        )
        bug_id = resp.json()['id']

        api_client.post(
            f'/api/accounts/projects/{project.id}/bug-reports/{bug_id}/evaluate/',
            {'status': 'confirmed'},
            format='json', **admin_headers,
        )

        client_notifs = Notification.objects.filter(
            user=client_user, type=Notification.TYPE_BUG_STATUS_CHANGED,
        )
        assert client_notifs.count() == 1

    def test_deliverable_upload_notifies_client(
        self, api_client, admin_headers, project, client_user,
    ):
        from django.core.files.base import ContentFile

        f = ContentFile(b'test content', name='design.pdf')

        api_client.post(
            f'/api/accounts/projects/{project.id}/deliverables/',
            {'title': 'Design file', 'category': 'designs', 'file': f},
            format='multipart', **admin_headers,
        )

        client_notifs = Notification.objects.filter(
            user=client_user, type=Notification.TYPE_DELIVERABLE_UPLOADED,
        )
        assert client_notifs.count() == 1
