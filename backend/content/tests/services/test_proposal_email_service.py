"""
Tests for ProposalEmailService.

Covers: send_reminder, send_urgency_email, send_response_notification —
happy paths, missing email, template rendering, error handling.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

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

    def test_returns_false_when_no_discount(self, email_proposal):
        email_proposal.discount_percent = 0
        email_proposal.save()

        result = ProposalEmailService.send_urgency_email(email_proposal)

        assert result is False

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
