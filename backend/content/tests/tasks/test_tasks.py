"""Tests for Huey tasks: send_proposal_reminder, send_urgency_reminder, expire_stale_proposals.

Covers: happy paths, skip conditions, edge cases.
"""
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import BusinessProposal

pytestmark = pytest.mark.django_db


class TestSendProposalReminderTask:
    @patch('content.services.proposal_email_service.ProposalEmailService.send_reminder',
           return_value=True)
    def test_sends_reminder_for_sent_proposal(self, mock_send_reminder):
        proposal = BusinessProposal.objects.create(
            title='Reminder Test',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)

        assert mock_send_reminder.call_count == 1

    @patch('content.services.proposal_email_service.ProposalEmailService.send_reminder',
           return_value=True)
    def test_sends_reminder_for_viewed_proposal(self, mock_send_reminder):
        proposal = BusinessProposal.objects.create(
            title='Viewed Test',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)

        assert mock_send_reminder.call_count == 1

    def test_skips_when_proposal_not_found(self):
        import content.tasks as tasks_module
        result = tasks_module.send_proposal_reminder.call_local(99999)
        assert result is None

    def test_skips_when_status_is_draft(self):
        proposal = BusinessProposal.objects.create(
            title='Draft',
            client_name='Client',
            client_email='client@test.com',
            status='draft',
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)
        assert proposal.status == 'draft'

    def test_skips_when_no_client_email(self):
        proposal = BusinessProposal.objects.create(
            title='No Email',
            client_name='Client',
            client_email='',
            status='sent',
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)
        assert proposal.reminder_sent_at is None

    @freeze_time('2026-03-01 12:00:00')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_reminder')
    def test_skips_when_reminder_already_sent(self, mock_send):
        proposal = BusinessProposal.objects.create(
            title='Already Sent',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
            reminder_sent_at=timezone.now(),
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)

        assert mock_send.call_count == 0

    @patch('content.services.proposal_email_service.ProposalEmailService.send_reminder')
    def test_skips_when_status_is_accepted(self, mock_send):
        proposal = BusinessProposal.objects.create(
            title='Accepted',
            client_name='Client',
            client_email='client@test.com',
            status='accepted',
        )

        import content.tasks as tasks_module
        tasks_module.send_proposal_reminder.call_local(proposal.id)

        assert mock_send.call_count == 0


class TestSendUrgencyReminderTask:
    @patch('content.services.proposal_email_service.ProposalEmailService.send_urgency_email',
           return_value=True)
    def test_sends_urgency_for_sent_proposal(self, mock_send):
        """One-shot urgency task sends email for a sent proposal."""
        proposal = BusinessProposal.objects.create(
            title='Urgency Test',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)

        assert mock_send.call_count == 1

    @patch('content.services.proposal_email_service.ProposalEmailService.send_urgency_email',
           return_value=True)
    def test_sends_urgency_for_viewed_proposal(self, mock_send):
        """One-shot urgency task sends email for a viewed proposal."""
        proposal = BusinessProposal.objects.create(
            title='Viewed Urgency',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)

        assert mock_send.call_count == 1

    def test_skips_when_proposal_not_found(self):
        """Task should not raise when proposal ID does not exist."""
        import content.tasks as tasks_module
        result = tasks_module.send_urgency_reminder.call_local(99999)
        assert result is None

    def test_skips_when_status_is_draft(self):
        """Urgency task should skip draft proposals."""
        proposal = BusinessProposal.objects.create(
            title='Draft Urgency',
            client_name='Client',
            client_email='client@test.com',
            status='draft',
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)
        proposal.refresh_from_db()
        assert proposal.urgency_email_sent_at is None

    def test_skips_when_no_client_email(self):
        """Urgency task should skip proposals without client_email."""
        proposal = BusinessProposal.objects.create(
            title='No Email Urgency',
            client_name='Client',
            client_email='',
            status='sent',
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)
        proposal.refresh_from_db()
        assert proposal.urgency_email_sent_at is None

    @freeze_time('2026-03-01 12:00:00')
    @patch('content.services.proposal_email_service.ProposalEmailService.send_urgency_email')
    def test_skips_when_urgency_already_sent(self, mock_send):
        """Urgency task should skip if urgency_email_sent_at is already set."""
        proposal = BusinessProposal.objects.create(
            title='Already Sent Urgency',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
            urgency_email_sent_at=timezone.now(),
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)

        assert mock_send.call_count == 0

    @patch('content.services.proposal_email_service.ProposalEmailService.send_urgency_email')
    def test_skips_when_status_is_accepted(self, mock_send):
        """Urgency task should skip accepted proposals."""
        proposal = BusinessProposal.objects.create(
            title='Accepted Urgency',
            client_name='Client',
            client_email='client@test.com',
            status='accepted',
        )

        import content.tasks as tasks_module
        tasks_module.send_urgency_reminder.call_local(proposal.id)

        assert mock_send.call_count == 0


class TestExpireStaleProposalsTask:
    @freeze_time('2026-03-10 10:00:00')
    def test_marks_expired_proposals(self):
        proposal = BusinessProposal.objects.create(
            title='Should Expire',
            client_name='Client',
            status='sent',
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        import content.tasks as tasks_module
        tasks_module.expire_stale_proposals.call_local()

        proposal.refresh_from_db()
        assert proposal.status == 'expired'

    @freeze_time('2026-03-10 10:00:00')
    def test_does_not_expire_draft_proposals(self):
        proposal = BusinessProposal.objects.create(
            title='Draft Expired',
            client_name='Client',
            status='draft',
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        import content.tasks as tasks_module
        tasks_module.expire_stale_proposals.call_local()

        proposal.refresh_from_db()
        assert proposal.status == 'draft'

    @freeze_time('2026-03-10 10:00:00')
    def test_does_not_expire_proposals_with_future_expiry(self):
        proposal = BusinessProposal.objects.create(
            title='Not Yet',
            client_name='Client',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=5),
        )

        import content.tasks as tasks_module
        tasks_module.expire_stale_proposals.call_local()

        proposal.refresh_from_db()
        assert proposal.status == 'sent'

    @freeze_time('2026-03-10 10:00:00')
    def test_expires_multiple_proposals(self):
        for i in range(3):
            BusinessProposal.objects.create(
                title=f'Expire {i}',
                client_name=f'Client {i}',
                status='viewed',
                expires_at=timezone.now() - timezone.timedelta(days=1),
            )

        import content.tasks as tasks_module
        tasks_module.expire_stale_proposals.call_local()

        assert BusinessProposal.objects.filter(status='expired').count() == 3

    @freeze_time('2026-03-10 10:00:00')
    def test_does_not_expire_inactive_proposals(self):
        """Inactive proposals should not be auto-expired."""
        proposal = BusinessProposal.objects.create(
            title='Inactive Expired',
            client_name='Client',
            status='sent',
            is_active=False,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        import content.tasks as tasks_module
        tasks_module.expire_stale_proposals.call_local()

        proposal.refresh_from_db()
        assert proposal.status == 'sent'
