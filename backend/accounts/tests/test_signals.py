"""Tests for accounts/signals.py — post_delete file cleanup handlers."""
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from accounts.models import (
    BugReport,
    ChangeRequest,
    Deliverable,
    DeliverableClientUpload,
    DeliverableFile,
    DeliverableVersion,
    Project,
    UserProfile,
)
from accounts.signals import _delete_file

User = get_user_model()

pytestmark = pytest.mark.django_db


# ── _delete_file helper ──

class TestDeleteFileHelper:
    def test_calls_storage_delete_when_field_has_name(self):
        mock_field = MagicMock()
        mock_field.name = 'avatars/test.jpg'

        _delete_file(mock_field)

        mock_field.storage.delete.assert_called_once_with('avatars/test.jpg')

    def test_does_nothing_when_field_is_none(self):
        _delete_file(None)  # should not raise

    def test_does_nothing_when_field_name_is_empty(self):
        mock_field = MagicMock()
        mock_field.name = ''

        _delete_file(mock_field)

        mock_field.storage.delete.assert_not_called()

    def test_suppresses_exception_from_storage_delete(self):
        mock_field = MagicMock()
        mock_field.name = 'avatars/missing.jpg'
        mock_field.storage.delete.side_effect = OSError('File not found')

        _delete_file(mock_field)  # should not raise


# ── UserProfile delete signal ──

class TestDeleteUserProfileSignal:
    def test_deleting_user_profile_fires_signal(self):
        user = User.objects.create_user(
            username='sig_user@test.com', email='sig_user@test.com', password='pass',
        )
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        profile_pk = profile.pk

        profile.delete()

        assert not UserProfile.objects.filter(pk=profile_pk).exists()

    def test_delete_calls_delete_file_for_avatar(self):
        user = User.objects.create_user(
            username='sigav@test.com', email='sigav@test.com', password='pass',
        )
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        with patch('accounts.signals._delete_file') as mock_del:
            profile.delete()

        assert mock_del.call_count >= 1


# ── ChangeRequest delete signal ──

class TestDeleteChangeRequestSignal:
    def test_deleting_change_request_fires_signal(self):
        client = User.objects.create_user(
            username='cr_sig@test.com', email='cr_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        cr = ChangeRequest.objects.create(
            project=project, created_by=client, title='CR Signal',
        )
        cr_pk = cr.pk

        cr.delete()

        assert not ChangeRequest.objects.filter(pk=cr_pk).exists()

    def test_delete_calls_delete_file_for_screenshot(self):
        client = User.objects.create_user(
            username='cr_sig2@test.com', email='cr_sig2@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        cr = ChangeRequest.objects.create(
            project=project, created_by=client, title='CR Sig File',
        )

        with patch('accounts.signals._delete_file') as mock_del:
            cr.delete()

        mock_del.assert_called_once()


# ── BugReport delete signal ──

class TestDeleteBugReportSignal:
    def test_deleting_bug_report_fires_signal(self):
        client = User.objects.create_user(
            username='bug_sig@test.com', email='bug_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=client, title='Bug Signal',
            severity=BugReport.SEVERITY_MEDIUM,
        )
        bug_pk = bug.pk

        bug.delete()

        assert not BugReport.objects.filter(pk=bug_pk).exists()

    def test_delete_calls_delete_file_for_screenshot(self):
        client = User.objects.create_user(
            username='bug_sig2@test.com', email='bug_sig2@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=client, title='Bug File',
            severity=BugReport.SEVERITY_MEDIUM,
        )

        with patch('accounts.signals._delete_file') as mock_del:
            bug.delete()

        mock_del.assert_called_once()


# ── Deliverable delete signal ──

class TestDeleteDeliverableSignal:
    def test_delete_calls_delete_file(self):
        client = User.objects.create_user(
            username='del_sig@test.com', email='del_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )

        with patch('accounts.signals._delete_file') as mock_del:
            deliverable.delete()

        mock_del.assert_called_once()


# ── DeliverableVersion delete signal ──

class TestDeleteDeliverableVersionSignal:
    def test_delete_calls_delete_file(self):
        client = User.objects.create_user(
            username='dv_sig@test.com', email='dv_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        version = DeliverableVersion.objects.create(
            deliverable=deliverable, uploaded_by=client, file=None, version_number=1,
        )

        with patch('accounts.signals._delete_file') as mock_del:
            version.delete()

        mock_del.assert_called_once()


# ── DeliverableFile delete signal ──

class TestDeleteDeliverableFileSignal:
    def test_delete_calls_delete_file(self):
        client = User.objects.create_user(
            username='df_sig@test.com', email='df_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        att = DeliverableFile.objects.create(
            deliverable=deliverable, uploaded_by=client,
            title='Test File', category='other', file=None,
        )

        with patch('accounts.signals._delete_file') as mock_del:
            att.delete()

        mock_del.assert_called_once()


# ── DeliverableClientUpload delete signal ──

class TestDeleteDeliverableClientUploadSignal:
    def test_delete_calls_delete_file(self):
        client = User.objects.create_user(
            username='dcu_sig@test.com', email='dcu_sig@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        upload = DeliverableClientUpload.objects.create(
            deliverable=deliverable, uploaded_by=client,
            title='Upload', file=None,
        )

        with patch('accounts.signals._delete_file') as mock_del:
            upload.delete()

        mock_del.assert_called_once()
