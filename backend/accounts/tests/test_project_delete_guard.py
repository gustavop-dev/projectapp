"""Hard-deleting a project stops being a silent SET_NULL sweep.

``DELETE ?force=1`` used to blank every accounting/document FK with no
trace; now it refuses while linked records exist (409 with the counts) and
leaves a PROJECT audit row when it does run. The default DELETE (archive)
audits its status change too.
"""
from decimal import Decimal

import pytest

from content.models import AccountingChangeLog, HostingRecord

pytestmark = pytest.mark.django_db


def url(project_id, *, force=False):
    base = f'/api/accounts/projects/{project_id}/'
    return f'{base}?force=1' if force else base


def project_audit_rows(project_id):
    return AccountingChangeLog.objects.filter(
        entity_type='project', object_id=project_id,
    )


class TestForceDeleteGuard:
    def test_refuses_with_the_counts_while_records_are_linked(
        self, api_client, admin_headers, client_user, project,
    ):
        HostingRecord.objects.create(
            client=client_user.profile,
            project=project,
            client_name='Client - CA',
            monthly_value=Decimal('120000.00'),
        )

        response = api_client.delete(url(project.pk, force=True), **admin_headers)

        assert response.status_code == 409
        assert response.data['code'] == 'project_has_records'
        assert response.data['counts'] == {
            'hostings': 1, 'incomes': 0, 'documents': 0,
        }
        assert type(project).objects.filter(pk=project.pk).exists()

    def test_a_clean_force_delete_runs_and_leaves_a_deleted_audit_row(
        self, api_client, admin_headers, project,
    ):
        project_id = project.pk

        response = api_client.delete(url(project_id, force=True), **admin_headers)

        assert response.status_code == 200
        assert not type(project).objects.filter(pk=project_id).exists()
        row = project_audit_rows(project_id).get()
        assert row.action == 'deleted'
        assert row.object_repr == 'CA Project'

    def test_the_default_delete_archives_and_audits_the_transition(
        self, api_client, admin_headers, project,
    ):
        response = api_client.delete(url(project.pk), **admin_headers)

        assert response.status_code == 200
        project.refresh_from_db()
        assert project.status == 'archived'
        row = project_audit_rows(project.pk).get()
        assert row.action == 'updated'
        assert any(
            change['field'] == 'status' for change in row.changes
        )

    def test_a_client_still_cannot_delete(
        self, api_client, client_headers, project,
    ):
        response = api_client.delete(url(project.pk, force=True), **client_headers)

        assert response.status_code == 403
        assert type(project).objects.filter(pk=project.pk).exists()
