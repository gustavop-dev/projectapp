"""Legacy project DELETE variants are replaced by lifecycle transitions."""
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

        assert response.status_code == 410
        assert response.data['code'] == 'project_archive_replaced'
        assert type(project).objects.filter(pk=project.pk).exists()

    def test_a_clean_force_delete_is_gone(
        self, api_client, admin_headers, project,
    ):
        project_id = project.pk

        response = api_client.delete(url(project_id, force=True), **admin_headers)

        assert response.status_code == 410
        assert response.data['code'] == 'project_archive_replaced'
        assert type(project).objects.filter(pk=project_id).exists()

    def test_the_default_delete_is_gone(
        self, api_client, admin_headers, project,
    ):
        response = api_client.delete(url(project.pk), **admin_headers)

        assert response.status_code == 410
        assert response.data['code'] == 'project_archive_replaced'
        project.refresh_from_db()
        assert project.status != 'archived'

    def test_a_client_still_cannot_delete(
        self, api_client, client_headers, project,
    ):
        response = api_client.delete(url(project.pk, force=True), **client_headers)

        assert response.status_code == 403
        assert type(project).objects.filter(pk=project.pk).exists()


class TestPlatformProjectAudit:
    def test_platform_create_and_update_leave_project_rows(
        self, api_client, admin_headers, client_user,
    ):
        created = api_client.post(
            '/api/accounts/projects/',
            {'name': 'Plataforma X', 'client_id': client_user.id},
            format='json',
            **admin_headers,
        )
        assert created.status_code == 201, created.data
        project_id = created.data['id']

        patched = api_client.patch(
            f'/api/accounts/projects/{project_id}/',
            {'name': 'Plataforma X v2'}, format='json', **admin_headers,
        )
        assert patched.status_code == 200, patched.data
        # Progress is operational noise, not identity: tracked fields are
        # name/description/status/client, so this writes no row.
        api_client.patch(
            f'/api/accounts/projects/{project_id}/',
            {'progress': 40}, format='json', **admin_headers,
        )

        rows = list(
            project_audit_rows(project_id).order_by('created_at'),
        )
        assert [row.action for row in rows] == ['created', 'updated']
