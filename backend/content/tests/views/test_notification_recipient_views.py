"""API tests for the administrable notification-recipient catalog.

This list decides who receives the module's financial email, so the cases
that matter are the ones that would silently misroute it: a duplicate
sneaking in under a different casing, a toggle that does not persist, and a
non-superuser reaching the endpoints at all.
"""
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, NotificationRecipient
from content.services import accounting_service

BASE = '/api/accounting/notification-recipients/'


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


@pytest.fixture(autouse=True)
def _drop_seeded_recipients(db):
    """Start from an empty list.

    Migration 0191 seeds the two production inboxes, so they exist in every
    fresh test database; these tests assert on their own rows.
    """
    NotificationRecipient.objects.all().delete()


@pytest.mark.django_db
class TestNotificationRecipientCrud:
    def test_list_returns_rows_alphabetically_with_state_and_signup_date(
        self, super_client,
    ):
        NotificationRecipient.objects.create(email='zoe@test.com')
        NotificationRecipient.objects.create(email='ana@test.com', is_active=False)

        response = super_client.get(BASE)

        assert response.status_code == 200
        results = response.data['results']
        assert [r['email'] for r in results] == ['ana@test.com', 'zoe@test.com']
        assert [r['is_active'] for r in results] == [False, True]
        # The panel shows this as "fecha de alta".
        assert all(r['created_at'] for r in results)

    def test_create_normalizes_the_address(self, super_client):
        response = super_client.post(
            BASE + 'create/', {'email': '  Carlos18BP@Gmail.COM '}, format='json',
        )

        assert response.status_code == 201, response.data
        assert response.data['email'] == 'carlos18bp@gmail.com'
        assert response.data['is_active'] is True

    def test_create_rejects_a_duplicate_regardless_of_casing(self, super_client):
        NotificationRecipient.objects.create(email='team@projectapp.co')

        response = super_client.post(
            BASE + 'create/', {'email': 'TEAM@projectapp.co'}, format='json',
        )

        assert response.status_code == 400
        assert response.data['email'] == ['Ese correo ya está en la lista.']
        assert NotificationRecipient.objects.count() == 1

    def test_create_rejects_a_malformed_address(self, super_client):
        response = super_client.post(
            BASE + 'create/', {'email': 'no-es-un-correo'}, format='json',
        )

        assert response.status_code == 400
        assert 'email' in response.data
        assert not NotificationRecipient.objects.exists()

    def test_update_pauses_a_recipient_without_deleting_it(self, super_client):
        row = NotificationRecipient.objects.create(email='ana@test.com')

        response = super_client.patch(
            f'{BASE}{row.id}/update/', {'is_active': False}, format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['is_active'] is False
        row.refresh_from_db()
        assert row.is_active is False
        assert NotificationRecipient.objects.filter(pk=row.pk).exists()

    def test_update_keeps_its_own_address_out_of_the_duplicate_check(
        self, super_client,
    ):
        row = NotificationRecipient.objects.create(email='ana@test.com')

        response = super_client.patch(
            f'{BASE}{row.id}/update/',
            {'email': 'ana@test.com', 'notes': 'contadora'},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['notes'] == 'contadora'

    def test_delete_removes_the_row(self, super_client):
        row = NotificationRecipient.objects.create(email='ana@test.com')

        response = super_client.delete(f'{BASE}{row.id}/delete/')

        assert response.status_code == 204
        assert not NotificationRecipient.objects.filter(pk=row.pk).exists()

    def test_filters_by_active_state(self, super_client):
        NotificationRecipient.objects.create(email='ana@test.com', is_active=True)
        NotificationRecipient.objects.create(email='zoe@test.com', is_active=False)

        response = super_client.get(BASE, {'is_active': 'false'})

        assert response.status_code == 200
        assert [r['email'] for r in response.data['results']] == ['zoe@test.com']


@pytest.mark.django_db
class TestNotificationRecipientAudit:
    """Changing who gets the financial email has to leave a trail."""

    def test_create_writes_an_audit_row_identified_by_the_address(
        self, super_client,
    ):
        super_client.post(BASE + 'create/', {'email': 'ana@test.com'}, format='json')

        log = AccountingChangeLog.objects.get(entity_type='notification_recipient')
        assert log.action == 'created'
        assert log.object_repr == 'ana@test.com'

    def test_pausing_a_recipient_is_logged_as_a_field_change(self, super_client):
        row = NotificationRecipient.objects.create(email='ana@test.com')

        super_client.patch(
            f'{BASE}{row.id}/update/', {'is_active': False}, format='json',
        )

        log = AccountingChangeLog.objects.get(
            entity_type='notification_recipient', action='updated',
        )
        assert [c['field'] for c in log.changes] == ['is_active']
        assert log.changes[0]['label'] == 'Activo'


@pytest.mark.django_db
class TestNotificationRecipientPermissions:
    """Superuser-only: this list controls who sees the company's money."""

    @pytest.mark.parametrize('method,path', [
        ('get', BASE),
        ('post', BASE + 'create/'),
        ('get', BASE + '1/'),
        ('patch', BASE + '1/update/'),
        ('delete', BASE + '1/delete/'),
    ])
    def test_staff_without_superuser_is_forbidden(
        self, admin_client, method, path,
    ):
        response = getattr(admin_client, method)(path)

        assert response.status_code == 403

    def test_anonymous_is_rejected(self, api_client):
        assert api_client.get(BASE).status_code in (401, 403)
