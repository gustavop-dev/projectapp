"""Tests for the single resolver every accounting email goes through.

If this function is wrong, notices go to the wrong people or to nobody —
and nothing else in the module would notice.
"""
import pytest

from content.models import NotificationRecipient
from content.services.notification_recipient_service import (
    active_recipient_emails,
)


@pytest.fixture
def drop_seeded_recipients(db):
    """Migration 0191 seeds two inboxes into every fresh test database.

    Not autouse: TestSeededRecipients below asserts on exactly those rows.
    """
    NotificationRecipient.objects.all().delete()


@pytest.mark.django_db
@pytest.mark.usefixtures('drop_seeded_recipients')
class TestActiveRecipientEmails:
    def test_returns_only_the_active_addresses(self):
        NotificationRecipient.objects.create(email='ana@test.com', is_active=True)
        NotificationRecipient.objects.create(email='zoe@test.com', is_active=False)

        assert active_recipient_emails() == ['ana@test.com']

    def test_is_empty_when_every_recipient_is_paused(self):
        NotificationRecipient.objects.create(email='ana@test.com', is_active=False)

        assert active_recipient_emails() == []

    def test_is_empty_when_the_list_has_no_rows(self):
        assert active_recipient_emails() == []

    def test_orders_alphabetically(self):
        for email in ('zoe@test.com', 'ana@test.com', 'mia@test.com'):
            NotificationRecipient.objects.create(email=email)

        assert active_recipient_emails() == [
            'ana@test.com', 'mia@test.com', 'zoe@test.com',
        ]

    def test_ignores_the_master_switch(self):
        """The switch is each sender's call, so its log says which one it was."""
        from content.models import AccountingSettings

        config = AccountingSettings.load()
        config.notifications_enabled = False
        config.save()
        NotificationRecipient.objects.create(email='ana@test.com')

        assert active_recipient_emails() == ['ana@test.com']


@pytest.mark.django_db
class TestSeededRecipients:
    """Migration 0191 must leave the module able to reach someone.

    Reads the rows the migration wrote when the test database was built —
    if the seeding is dropped or an address is typo'd, the module ships
    with an empty list and every notice goes nowhere.
    """

    def test_migration_registered_the_required_inboxes(self):
        seeded = NotificationRecipient.objects.filter(
            source_ref='migration:0191',
        ).values_list('email', flat=True)

        assert sorted(seeded) == ['carlos18bp@gmail.com', 'team@projectapp.co']

    def test_the_seeded_inboxes_are_active(self):
        assert sorted(active_recipient_emails()) == [
            'carlos18bp@gmail.com', 'team@projectapp.co',
        ]
