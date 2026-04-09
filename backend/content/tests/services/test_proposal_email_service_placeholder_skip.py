"""
Verify that ProposalEmailService client-facing methods skip silently when
the proposal's client email is a generated placeholder. This is the safety
net that prevents test/draft proposals from accidentally emailing recipients
when they share a placeholder address with another draft.
"""

from unittest.mock import patch

import pytest

from accounts.services import proposal_client_service
from content.models.business_proposal import BusinessProposal
from content.services.proposal_email_service import (
    ProposalEmailService,
    _is_unsendable_client_email,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def placeholder_proposal(db):
    profile = proposal_client_service.get_or_create_client_for_proposal(
        name='Placeholder Tester', email='',
    )
    return BusinessProposal.objects.create(
        title='Test', client=profile,
        client_name='Placeholder Tester',
        client_email=profile.user.email,  # cliente_<id>@temp.example.com
        client_phone='', total_investment=1000, status='sent',
    )


@pytest.fixture
def real_proposal(db):
    profile = proposal_client_service.get_or_create_client_for_proposal(
        name='Real Person', email='real@gmail.com',
    )
    return BusinessProposal.objects.create(
        title='Real test', client=profile,
        client_name='Real Person',
        client_email='real@gmail.com',
        total_investment=1000, status='sent',
    )


class TestIsUnsendableClientEmail:
    def test_returns_true_for_empty_string(self):
        assert _is_unsendable_client_email('') is True

    def test_returns_true_for_none(self):
        assert _is_unsendable_client_email(None) is True

    def test_returns_true_for_placeholder_address(self):
        assert _is_unsendable_client_email('cliente_42@temp.example.com') is True

    def test_returns_false_for_real_address(self):
        assert _is_unsendable_client_email('foo@gmail.com') is False


class TestPlaceholderSkipSendAcceptanceConfirmation:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_acceptance_confirmation(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()


class TestPlaceholderSkipSendReminder:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_reminder(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()


class TestPlaceholderSkipSendUrgencyEmail:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_urgency_email(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()


class TestPlaceholderSkipSendRejectionThankYou:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_rejection_thank_you(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()


class TestPlaceholderSkipSendNegotiationConfirmation:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_negotiation_confirmation(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()


class TestPlaceholderSkipSendAbandonmentFollowup:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    def test_skips_send_when_email_is_placeholder(
        self, mock_email_class, placeholder_proposal,
    ):
        result = ProposalEmailService.send_abandonment_followup(placeholder_proposal)
        assert result is False
        mock_email_class.assert_not_called()
