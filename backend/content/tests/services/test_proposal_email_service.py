"""Tests for ProposalEmailService.

Covers: send_reminder, send_urgency_email, send_response_notification —
happy paths, missing email, template rendering, error handling.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import BusinessProposal
from content.services.proposal_email_service import ProposalEmailService

pytestmark = pytest.mark.django_db


@pytest.fixture
def email_proposal(db):
    """A proposal with client_email set for email tests."""
    return BusinessProposal.objects.create(
        title='Email Test Proposal',
        client_name='Email Client',
        client_email='client@email-test.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=10),
        discount_percent=20,
    )


@pytest.fixture
def no_email_proposal(db):
    """A proposal without client_email."""
    return BusinessProposal.objects.create(
        title='No Email Proposal',
        client_name='No Email',
        client_email='',
        status='sent',
    )


class TestSendReminder:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_reminder_email_successfully(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Reminder</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_reminder(email_proposal)

        assert result is True
        mock_email_instance.send.assert_called_once_with(fail_silently=False)
        email_proposal.refresh_from_db()
        assert email_proposal.reminder_sent_at is not None

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_reminder(no_email_proposal)

        assert result is False
        no_email_proposal.refresh_from_db()
        assert no_email_proposal.reminder_sent_at is None

    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_false_on_send_exception(self, mock_render, email_proposal):
        mock_render.side_effect = Exception('Template not found')

        result = ProposalEmailService.send_reminder(email_proposal)

        assert result is False

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_reminder_subject_contains_client_name(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>content</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        ProposalEmailService.send_reminder(email_proposal)

        mock_email_cls.assert_called_once()
        mock_email_instance.send.assert_called_once()
        call_kwargs = mock_email_cls.call_args[1]
        assert 'Email Client' in call_kwargs['subject']


class TestSendUrgencyEmail:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_urgency_email_with_discount(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Urgency</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_urgency_email(email_proposal)

        assert result is True
        mock_email_instance.send.assert_called_once_with(fail_silently=False)
        email_proposal.refresh_from_db()
        assert email_proposal.urgency_email_sent_at is not None

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_urgency_email(no_email_proposal)

        assert result is False

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_no_discount_template_when_discount_is_zero(
        self, mock_render, mock_email_cls, email_proposal,
    ):
        """When discount_percent is 0, urgency email still sends but uses no-discount template."""
        email_proposal.discount_percent = 0
        email_proposal.save()
        mock_render.return_value = '<html>No discount urgency</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_urgency_email(email_proposal)

        assert result is True
        mock_email_instance.send.assert_called_once_with(fail_silently=False)
        # Verify it uses the no-discount template
        template_calls = [c[0][0] for c in mock_render.call_args_list]
        assert 'emails/proposal_urgency_no_discount.html' in template_calls
        assert 'emails/proposal_urgency_no_discount.txt' in template_calls
        # Subject should NOT contain discount percentage
        call_kwargs = mock_email_cls.call_args[1]
        assert '20%' not in call_kwargs['subject']
        assert 'expira pronto' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_urgency_subject_contains_discount_percent(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>content</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        ProposalEmailService.send_urgency_email(email_proposal)

        mock_email_cls.assert_called_once()
        mock_email_instance.send.assert_called_once()
        call_kwargs = mock_email_cls.call_args[1]
        assert '20%' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_false_on_send_exception(self, mock_render, email_proposal):
        mock_render.side_effect = Exception('Template error')

        result = ProposalEmailService.send_urgency_email(email_proposal)

        assert result is False


class TestSendResponseNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_accepted_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_response_notification(email_proposal, 'accepted')

        assert result is True
        mock_email_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_rejected_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Rejected</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_response_notification(email_proposal, 'rejected')

        assert result is True
        mock_email_cls.assert_called_once()
        mock_email_instance.send.assert_called_once()
        call_kwargs = mock_email_cls.call_args[1]
        assert 'REJECTED' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_accepted_subject_contains_tag(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>content</html>'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        ProposalEmailService.send_response_notification(email_proposal, 'accepted')

        mock_email_cls.assert_called_once()
        mock_email_instance.send.assert_called_once()
        call_kwargs = mock_email_cls.call_args[1]
        assert '[ACCEPTED]' in call_kwargs['subject']
        assert email_proposal.title in call_kwargs['subject']

    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        mock_render.side_effect = Exception('Template error')

        result = ProposalEmailService.send_response_notification(email_proposal, 'accepted')

        assert result is False


class TestGetFromEmail:
    def test_returns_default_from_email_from_settings(self):
        with patch.object(ProposalEmailService, 'FROM_EMAIL', None):
            from_email = ProposalEmailService._get_from_email()
            assert from_email is not None

    def test_returns_class_from_email_when_set(self):
        with patch.object(ProposalEmailService, 'FROM_EMAIL', 'custom@test.com'):
            assert ProposalEmailService._get_from_email() == 'custom@test.com'


# ---------------------------------------------------------------------------
# Acceptance confirmation
# ---------------------------------------------------------------------------

class TestSendAcceptanceConfirmation:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=b'%PDF-fake')
    def test_sends_with_pdf_attachment(self, mock_pdf, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)

        assert result is True
        mock_instance.attach.assert_called_once()
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=None)
    def test_sends_without_pdf_when_generation_returns_none(self, mock_pdf, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)

        assert result is True
        mock_instance.attach.assert_not_called()

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', side_effect=Exception('PDF error'))
    def test_sends_without_pdf_when_generation_fails(self, mock_pdf, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once()

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_acceptance_confirmation(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('Template error'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)
        assert result is False


# ---------------------------------------------------------------------------
# Rejection thank-you
# ---------------------------------------------------------------------------

class TestSendRejectionThankYou:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_rejection_thank_you(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Thank you</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_rejection_thank_you(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_rejection_thank_you(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_rejection_thank_you(email_proposal)
        assert result is False


# ---------------------------------------------------------------------------
# First-view notification
# ---------------------------------------------------------------------------

class TestSendFirstViewNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_first_view_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>First view</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_first_view_notification(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        call_kwargs = mock_email_cls.call_args[1]
        assert '[OPENED]' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_first_view_notification(email_proposal)
        assert result is False


# ---------------------------------------------------------------------------
# Comment notification
# ---------------------------------------------------------------------------

class TestSendCommentNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_comment_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Comment</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_comment_notification(
            email_proposal, 'Can we negotiate?'
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        call_kwargs = mock_email_cls.call_args[1]
        assert '[COMENTARIO]' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_comment_notification(email_proposal, 'test')
        assert result is False


# ---------------------------------------------------------------------------
# Rejection re-engagement
# ---------------------------------------------------------------------------

class TestSendRejectionReengagement:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_reengagement_with_discount(self, mock_render, mock_email_cls, email_proposal):
        email_proposal.discount_percent = 15
        email_proposal.save(update_fields=['discount_percent'])
        mock_render.return_value = '<html>Reengage</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_rejection_reengagement(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_reengagement_without_discount(self, mock_render, mock_email_cls, email_proposal):
        """Re-engagement email sends successfully when discount_percent is zero."""
        email_proposal.discount_percent = 0
        email_proposal.save(update_fields=['discount_percent'])
        mock_render.return_value = '<html>Reengage</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_rejection_reengagement(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_rejection_reengagement(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_rejection_reengagement(email_proposal)
        assert result is False


# ---------------------------------------------------------------------------
# Revisit alert
# ---------------------------------------------------------------------------

class TestSendRevisitAlert:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_revisit_alert(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Alert</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_revisit_alert(
            email_proposal, visit_count=5, top_section='Investment', top_section_time=120,
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        email_proposal.refresh_from_db()
        assert email_proposal.revisit_alert_sent_at is not None

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_handles_empty_top_section(self, mock_render, mock_email_cls, email_proposal):
        """Revisit alert sends successfully when top_section is not provided."""
        mock_render.return_value = '<html>Alert</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_revisit_alert(email_proposal, visit_count=3)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_revisit_alert(email_proposal, visit_count=3)
        assert result is False


# ---------------------------------------------------------------------------
# Abandonment followup
# ---------------------------------------------------------------------------

class TestSendAbandonmentFollowup:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_abandonment_followup(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Abandoned</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_abandonment_followup(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        email_proposal.refresh_from_db()
        assert email_proposal.abandonment_email_sent_at is not None

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_abandonment_followup(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_abandonment_followup(email_proposal)
        assert result is False


# ---------------------------------------------------------------------------
# Investment interest followup
# ---------------------------------------------------------------------------

class TestSendInvestmentInterestFollowup:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_investment_interest_followup(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Interest</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_investment_interest_followup(
            email_proposal, time_on_investment=120,
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        email_proposal.refresh_from_db()
        assert email_proposal.investment_interest_email_sent_at is not None

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_investment_interest_followup(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_investment_interest_followup(email_proposal, 90)
        assert result is False


# ---------------------------------------------------------------------------
# Share notification
# ---------------------------------------------------------------------------

class TestSendShareNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_share_notification(self, mock_render, mock_email_cls, email_proposal):
        """Share notification sends to team with [SHARED] subject tag."""
        from content.models import ProposalShareLink
        share = ProposalShareLink.objects.create(
            proposal=email_proposal,
            shared_by_name='Alice',
            shared_by_email='alice@co.com',
        )
        mock_render.return_value = '<html>Shared</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_share_notification(email_proposal, share)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        call_kwargs = mock_email_cls.call_args[1]
        assert '[SHARED]' in call_kwargs['subject']

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        from content.models import ProposalShareLink
        share = ProposalShareLink.objects.create(
            proposal=email_proposal,
            shared_by_name='Alice',
        )
        result = ProposalEmailService.send_share_notification(email_proposal, share)
        assert result is False


# ---------------------------------------------------------------------------
# Scheduled followup
# ---------------------------------------------------------------------------

class TestSendScheduledFollowup:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_scheduled_followup(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Followup</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_scheduled_followup(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        result = ProposalEmailService.send_scheduled_followup(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        result = ProposalEmailService.send_scheduled_followup(email_proposal)
        assert result is False


class TestSendStakeholderDetectedNotification:
    """Tests for send_stakeholder_detected_notification."""

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_notification_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Stakeholder notification sends email and returns True."""
        mock_render.return_value = '<html>Stakeholder</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_stakeholder_detected_notification(
            email_proposal, 3
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering raises an exception."""
        result = ProposalEmailService.send_stakeholder_detected_notification(
            email_proposal, 2
        )
        assert result is False


class TestSendProposalToClientEdgePaths:
    def test_returns_false_when_no_client_email(self, no_email_proposal):
        """send_proposal_to_client returns False when proposal has no client_email."""
        result = ProposalEmailService.send_proposal_to_client(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('Template error'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """send_proposal_to_client returns False when template rendering fails."""
        result = ProposalEmailService.send_proposal_to_client(email_proposal)
        assert result is False


class TestSendSellerInactivityEscalation:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_escalation_email_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Escalation email sent to notification address with correct context."""
        mock_render.return_value = '<html>Escalation</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_seller_inactivity_escalation(email_proposal, 7)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering raises an exception."""
        result = ProposalEmailService.send_seller_inactivity_escalation(email_proposal, 5)
        assert result is False


class TestSendNegotiationNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_notification_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Negotiation notification sent to team with comment in context."""
        mock_render.return_value = '<html>Negotiate</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_negotiation_notification(
            email_proposal, comment='Reduce modules please'
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering fails."""
        result = ProposalEmailService.send_negotiation_notification(email_proposal)
        assert result is False


class TestSendNegotiationConfirmation:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_confirmation_to_client(self, mock_render, mock_email_cls, email_proposal):
        """Negotiation confirmation sent to client_email."""
        mock_render.return_value = '<html>Confirm</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_negotiation_confirmation(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        """Returns False when proposal has no client_email."""
        result = ProposalEmailService.send_negotiation_confirmation(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering fails."""
        result = ProposalEmailService.send_negotiation_confirmation(email_proposal)
        assert result is False


class TestSendPostExpirationVisitAlert:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_alert_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Post-expiration visit alert sent to notification address."""
        mock_render.return_value = '<html>Expired Visit</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_post_expiration_visit_alert(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering fails."""
        result = ProposalEmailService.send_post_expiration_visit_alert(email_proposal)
        assert result is False


class TestSendProposalToClient:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_email_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Sends initial proposal email to client."""
        mock_render.return_value = '<html>Proposal</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_proposal_to_client(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        """Returns False when proposal has no client_email."""
        result = ProposalEmailService.send_proposal_to_client(no_email_proposal)
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering fails."""
        result = ProposalEmailService.send_proposal_to_client(email_proposal)
        assert result is False


class TestSendPostRejectionRevisitAlert:
    @freeze_time('2026-03-10 12:00:00')
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_alert_successfully(self, mock_render, mock_email_cls, email_proposal):
        """Post-rejection revisit alert sent to notification address."""
        mock_render.return_value = '<html>Revisit</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance
        email_proposal.status = 'rejected'
        email_proposal.responded_at = timezone.now() - timezone.timedelta(days=10)
        email_proposal.save(update_fields=['status', 'responded_at'])

        result = ProposalEmailService.send_post_rejection_revisit_alert(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    @freeze_time('2026-03-10 12:00:00')
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_calculates_days_since_rejection(self, mock_render, mock_email_cls, email_proposal):
        """Days since rejection is computed from responded_at."""
        mock_render.return_value = '<html>Revisit</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance
        email_proposal.responded_at = timezone.now() - timezone.timedelta(days=15)
        email_proposal.save(update_fields=['responded_at'])

        result = ProposalEmailService.send_post_rejection_revisit_alert(email_proposal)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        call_ctx = mock_render.call_args_list[0][0][1]
        assert call_ctx['days_since_rejection'] == 15

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render, email_proposal):
        """Returns False when template rendering fails."""
        result = ProposalEmailService.send_post_rejection_revisit_alert(email_proposal)
        assert result is False


class TestSendDailyPipelineDigest:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_digest_successfully(self, mock_render, mock_email_cls):
        """Daily pipeline digest sent to notification address."""
        mock_render.return_value = '<html>Digest</html>'
        mock_instance = MagicMock()
        mock_email_cls.return_value = mock_instance
        digest_data = {
            'viewed_yesterday': [],
            'inactive': [],
            'expiring_soon': [],
            'total_active': 5,
            'date': '2026-03-10',
        }

        result = ProposalEmailService.send_daily_pipeline_digest(digest_data)

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_render.call_count == 2

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('err'))
    def test_returns_false_on_exception(self, mock_render):
        """Returns False when template rendering fails."""
        digest_data = {
            'viewed_yesterday': [], 'inactive': [], 'expiring_soon': [],
            'total_active': 0, 'date': '2026-03-10',
        }
        result = ProposalEmailService.send_daily_pipeline_digest(digest_data)
        assert result is False
