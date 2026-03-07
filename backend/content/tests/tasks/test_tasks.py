"""Tests for Huey tasks.

Covers: send_proposal_reminder, send_urgency_reminder, expire_stale_proposals,
send_rejection_reengagement, check_engagement_followups, send_scheduled_followup.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSectionView,
    ProposalViewEvent,
)

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


class TestSendRejectionReengagementTask:
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_rejection_reengagement',
        return_value=True,
    )
    def test_sends_reengagement_for_rejected_proposal(self, mock_send):
        """Rejected proposal triggers re-engagement email and changelog entry."""
        proposal = BusinessProposal.objects.create(
            title='Rejected',
            client_name='Client',
            client_email='client@test.com',
            status='rejected',
        )

        import content.tasks as tasks_module
        tasks_module.send_rejection_reengagement.call_local(proposal.id)

        mock_send.assert_called_once()
        assert ProposalChangeLog.objects.filter(
            proposal=proposal, change_type='reengagement'
        ).exists()

    def test_skips_when_proposal_not_found(self):
        import content.tasks as tasks_module
        result = tasks_module.send_rejection_reengagement.call_local(99999)
        assert result is None

    def test_skips_when_status_is_not_rejected(self):
        proposal = BusinessProposal.objects.create(
            title='Sent',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )

        import content.tasks as tasks_module
        tasks_module.send_rejection_reengagement.call_local(proposal.id)
        assert not ProposalChangeLog.objects.filter(change_type='reengagement').exists()

    def test_skips_when_no_client_email(self):
        proposal = BusinessProposal.objects.create(
            title='No Email',
            client_name='Client',
            client_email='',
            status='rejected',
        )

        import content.tasks as tasks_module
        tasks_module.send_rejection_reengagement.call_local(proposal.id)
        assert not ProposalChangeLog.objects.filter(change_type='reengagement').exists()

    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_rejection_reengagement',
        return_value=True,
    )
    def test_skips_when_already_sent(self, mock_send):
        """Re-engagement skips when a changelog entry already exists."""
        proposal = BusinessProposal.objects.create(
            title='Already Sent',
            client_name='Client',
            client_email='client@test.com',
            status='rejected',
        )
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='reengagement',
            description='Already sent.',
        )

        import content.tasks as tasks_module
        tasks_module.send_rejection_reengagement.call_local(proposal.id)

        mock_send.assert_not_called()
        assert ProposalChangeLog.objects.filter(
            proposal=proposal, change_type='reengagement'
        ).count() == 1  # unchanged

    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_rejection_reengagement',
        return_value=False,
    )
    def test_does_not_log_when_send_fails(self, mock_send):
        """No changelog entry created when email sending returns False."""
        proposal = BusinessProposal.objects.create(
            title='Fail Send',
            client_name='Client',
            client_email='client@test.com',
            status='rejected',
        )

        import content.tasks as tasks_module
        tasks_module.send_rejection_reengagement.call_local(proposal.id)

        mock_send.assert_called_once()
        assert not ProposalChangeLog.objects.filter(
            proposal=proposal, change_type='reengagement'
        ).exists()


class TestCheckEngagementFollowupsTask:
    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_abandonment_followup',
        return_value=True,
    )
    def test_sends_abandonment_followup(self, mock_send):
        """Proposal viewed >4h ago without investment section triggers abandonment email."""
        now = timezone.now()
        proposal = BusinessProposal.objects.create(
            title='Abandoned',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            first_viewed_at=now - timedelta(hours=5),
        )
        ve = ProposalViewEvent.objects.create(
            proposal=proposal,
            session_id='sess-1',
            ip_address='127.0.0.1',
        )
        ProposalSectionView.objects.create(
            view_event=ve,
            section_type='greeting',
            time_spent_seconds=10,
            entered_at=now - timedelta(hours=5),
        )

        import content.tasks as tasks_module
        tasks_module.check_engagement_followups.call_local()

        mock_send.assert_called_once()
        assert mock_send.call_args[0][0].pk == proposal.pk

    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_abandonment_followup',
        return_value=True,
    )
    def test_skips_abandonment_when_investment_visited(self, mock_send):
        """Abandonment email skipped when client visited the investment section."""
        now = timezone.now()
        proposal = BusinessProposal.objects.create(
            title='Visited Investment',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            first_viewed_at=now - timedelta(hours=5),
        )
        ve = ProposalViewEvent.objects.create(
            proposal=proposal,
            session_id='sess-1',
            ip_address='127.0.0.1',
        )
        ProposalSectionView.objects.create(
            view_event=ve,
            section_type='investment',
            time_spent_seconds=30,
            entered_at=now - timedelta(hours=5),
        )

        import content.tasks as tasks_module
        tasks_module.check_engagement_followups.call_local()

        assert mock_send.call_count == 0

    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_investment_interest_followup',
        return_value=True,
    )
    def test_sends_investment_interest_followup(self, mock_send):
        """Proposal with >60s on investment and last view >2h ago triggers interest email."""
        now = timezone.now()
        proposal = BusinessProposal.objects.create(
            title='Interested',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            first_viewed_at=now - timedelta(hours=5),
        )
        ve = ProposalViewEvent.objects.create(
            proposal=proposal,
            session_id='sess-1',
            ip_address='127.0.0.1',
        )
        # auto_now_add ignores kwargs, so force via update()
        ProposalViewEvent.objects.filter(pk=ve.pk).update(
            viewed_at=now - timedelta(hours=3),
        )
        ProposalSectionView.objects.create(
            view_event=ve,
            section_type='investment',
            time_spent_seconds=90,
            entered_at=now - timedelta(hours=3),
        )

        import content.tasks as tasks_module
        tasks_module.check_engagement_followups.call_local()

        mock_send.assert_called_once()
        assert mock_send.call_args[0][0].pk == proposal.pk

    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_investment_interest_followup',
        return_value=True,
    )
    def test_skips_interest_when_investment_time_under_60s(self, mock_send):
        """Interest email skipped when total investment time is under 60 seconds."""
        now = timezone.now()
        proposal = BusinessProposal.objects.create(
            title='Short Investment',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            first_viewed_at=now - timedelta(hours=5),
        )
        ve = ProposalViewEvent.objects.create(
            proposal=proposal,
            session_id='sess-1',
            ip_address='127.0.0.1',
        )
        ProposalViewEvent.objects.filter(pk=ve.pk).update(
            viewed_at=now - timedelta(hours=3),
        )
        ProposalSectionView.objects.create(
            view_event=ve,
            section_type='investment',
            time_spent_seconds=30,
            entered_at=now - timedelta(hours=3),
        )

        import content.tasks as tasks_module
        tasks_module.check_engagement_followups.call_local()

        assert mock_send.call_count == 0

    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_investment_interest_followup',
        return_value=True,
    )
    def test_skips_interest_when_last_view_is_recent(self, mock_send):
        """Interest email skipped when the last view event is less than 2 hours ago."""
        now = timezone.now()
        proposal = BusinessProposal.objects.create(
            title='Recent View',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            first_viewed_at=now - timedelta(hours=5),
        )
        ve = ProposalViewEvent.objects.create(
            proposal=proposal,
            session_id='sess-1',
            ip_address='127.0.0.1',
        )
        ProposalViewEvent.objects.filter(pk=ve.pk).update(
            viewed_at=now - timedelta(minutes=30),
        )
        ProposalSectionView.objects.create(
            view_event=ve,
            section_type='investment',
            time_spent_seconds=90,
            entered_at=now - timedelta(minutes=30),
        )

        import content.tasks as tasks_module
        tasks_module.check_engagement_followups.call_local()

        assert mock_send.call_count == 0


class TestSendScheduledFollowupTask:
    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_scheduled_followup',
        return_value=True,
    )
    def test_sends_followup_for_scheduled_proposal(self, mock_send):
        """Scheduled followup task calls email service for a valid proposal."""
        proposal = BusinessProposal.objects.create(
            title='Scheduled',
            client_name='Client',
            client_email='client@test.com',
            status='rejected',
            followup_scheduled_at=timezone.now(),
        )

        import content.tasks as tasks_module
        tasks_module.send_scheduled_followup.call_local(proposal.id)

        mock_send.assert_called_once()
        assert mock_send.call_args[0][0].pk == proposal.pk

    def test_skips_when_proposal_not_found(self):
        import content.tasks as tasks_module
        result = tasks_module.send_scheduled_followup.call_local(99999)
        assert result is None

    @freeze_time('2026-03-10 12:00:00')
    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_scheduled_followup',
    )
    def test_skips_when_no_client_email(self, mock_send):
        """Scheduled followup skips when proposal has no client_email."""
        proposal = BusinessProposal.objects.create(
            title='No Email',
            client_name='Client',
            client_email='',
            status='rejected',
            followup_scheduled_at=timezone.now(),
        )

        import content.tasks as tasks_module
        tasks_module.send_scheduled_followup.call_local(proposal.id)

        assert mock_send.call_count == 0

    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_scheduled_followup',
    )
    def test_skips_when_no_scheduled_date(self, mock_send):
        """Scheduled followup skips when followup_scheduled_at is not set."""
        proposal = BusinessProposal.objects.create(
            title='No Date',
            client_name='Client',
            client_email='client@test.com',
            status='rejected',
        )

        import content.tasks as tasks_module
        tasks_module.send_scheduled_followup.call_local(proposal.id)

        assert mock_send.call_count == 0
