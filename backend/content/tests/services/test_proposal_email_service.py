"""Tests for ProposalEmailService.

Covers: send_reminder, send_urgency_email, send_response_notification —
happy paths, missing email, template rendering, error handling.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    EmailLog,
    EmailTemplateConfig,
    ProposalChangeLog,
    ProposalShareLink,
)
from content.services.proposal_email_service import ProposalEmailService

pytestmark = pytest.mark.django_db


def _stub_email():
    """Return a MagicMock email instance for EmailMultiAlternatives stubs."""
    return MagicMock()


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
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
        mock_email_cls.return_value = mock_email_instance

        result = ProposalEmailService.send_response_notification(email_proposal, 'accepted')

        assert result is True
        mock_email_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_rejected_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Rejected</html>'
        mock_email_instance = _stub_email()
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
        mock_email_instance = _stub_email()
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

    @override_settings(
        NOTIFICATION_EMAIL='team@projectapp.co,carlos18bp@gmail.com'
    )
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_to_all_notification_recipients(
        self, mock_render, mock_email_cls, email_proposal,
    ):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_response_notification(email_proposal, 'accepted')

        assert result is True
        call_kwargs = mock_email_cls.call_args[1]
        assert call_kwargs['to'] == [
            'team@projectapp.co',
            'carlos18bp@gmail.com',
        ]


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
    @patch('content.services.platform_onboarding_pdf.generate_platform_onboarding_pdf', return_value=None)
    @patch('content.services.technical_document_pdf.generate_technical_document_pdf', return_value=None)
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=b'%PDF-fake')
    def test_sends_with_pdf_attachment(self, mock_pdf, mock_tech, mock_guide, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)

        assert result is True
        mock_instance.attach.assert_called_once()
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    @patch('content.services.platform_onboarding_pdf.generate_platform_onboarding_pdf', return_value=None)
    @patch('content.services.technical_document_pdf.generate_technical_document_pdf', return_value=None)
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=None)
    def test_sends_without_pdf_when_generation_returns_none(self, mock_pdf, mock_tech, mock_guide, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService.send_acceptance_confirmation(email_proposal)

        assert result is True
        mock_instance.attach.assert_not_called()

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    @patch('content.services.proposal_pdf_service.ProposalPdfService.generate', side_effect=Exception('PDF error'))
    def test_sends_without_pdf_when_generation_fails(self, mock_pdf, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Accepted</html>'
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_context_without_additional_modules_matches_base(
        self, mock_render, mock_email_cls, email_proposal,
    ):
        mock_render.return_value = '<html>First view</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_first_view_notification(email_proposal)

        ctx = mock_render.call_args_list[0][0][1]
        assert ctx['has_additional_modules'] is False
        assert ctx['effective_total_investment'] == ctx['total_investment']

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_context_with_additional_modules_includes_effective_total(
        self, mock_render, mock_email_cls, email_proposal,
    ):
        from content.models import ProposalSection
        ProposalSection.objects.create(
            proposal=email_proposal,
            section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
            title='Requisitos',
            content_json={
                'groups': [
                    {
                        'id': 'mod-extra-1',
                        'is_calculator_module': True,
                        'price_percent': 10,
                    },
                ],
            },
        )
        email_proposal.selected_modules = ['mod-extra-1']
        email_proposal.save(update_fields=['selected_modules'])

        mock_render.return_value = '<html>First view</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_first_view_notification(email_proposal)

        ctx = mock_render.call_args_list[0][0][1]
        assert ctx['has_additional_modules'] is True
        # base 5'000.000 + 10% = 5'500.000 (COP format from format_cop_email)
        assert ctx['effective_total_investment'] != ctx['total_investment']
        digits_only = lambda s: ''.join(c for c in s if c.isdigit())
        assert digits_only(ctx['total_investment']) == '5000000'
        assert digits_only(ctx['effective_total_investment']) == '5500000'


# ---------------------------------------------------------------------------
# Comment notification
# ---------------------------------------------------------------------------

class TestSendCommentNotification:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_comment_notification(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Comment</html>'
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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
        mock_instance = _stub_email()
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


# ---------------------------------------------------------------------------
# _log_email exception handling (lines 40-41)
# ---------------------------------------------------------------------------

class TestLogEmailExceptionHandling:
    @patch('content.services.proposal_email_service.logger')
    @patch('content.models.EmailLog.objects.create', side_effect=Exception('DB error'))
    def test_logs_exception_when_email_log_creation_fails(self, mock_create, mock_logger):
        """_log_email catches exception and logs it when EmailLog.objects.create fails."""
        ProposalEmailService._log_email(
            'proposal_sent_client', 'test@example.com',
            subject='Test', proposal=None, status='sent',
        )

        assert mock_logger.exception.call_count == 1
        mock_logger.exception.assert_called_once_with('Failed to create EmailLog entry')


# ---------------------------------------------------------------------------
# _is_template_active with existing config (line 52)
# ---------------------------------------------------------------------------

class TestIsTemplateActiveWithConfig:
    def test_returns_false_when_config_exists_and_inactive(self):
        """_is_template_active returns False when EmailTemplateConfig.is_active is False."""
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            is_active=False,
        )

        result = ProposalEmailService._is_template_active('proposal_sent_client')

        assert result is False

    def test_returns_true_when_config_exists_and_active(self):
        """_is_template_active returns True when EmailTemplateConfig.is_active is True."""
        EmailTemplateConfig.objects.create(
            template_key='proposal_sent_client',
            is_active=True,
        )

        result = ProposalEmailService._is_template_active('proposal_sent_client')

        assert result is True


# ---------------------------------------------------------------------------
# Template-disabled early returns (lines 99-100, 181-182, ... 1454-1455)
# ---------------------------------------------------------------------------

class TestSendDocumentsToClient:
    """ProposalEmailService.send_documents_to_client — all code paths."""

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_email_with_multiple_attachments(self, mock_render, mock_email_cls, email_proposal):
        """Email is sent successfully with each attachment appended."""
        mock_render.return_value = '<html>Docs</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        attachments = [
            ('contrato.pdf', b'%PDF-1.4 contract', 'application/pdf'),
            ('anexo.pdf', b'%PDF-1.4 annex', 'application/pdf'),
        ]
        result = ProposalEmailService.send_documents_to_client(
            email_proposal,
            attachments=attachments,
            subject='Documentos de tu proyecto',
            greeting='Hola Test',
            body='Adjuntamos los documentos.',
            footer='Gracias.',
        )

        assert result is True
        mock_instance.send.assert_called_once_with(fail_silently=False)
        assert mock_instance.attach.call_count == 2

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_uses_provided_subject_and_body_fields(self, mock_render, mock_email_cls, email_proposal):
        """Custom subject, greeting, body, footer are passed to the email constructor."""
        mock_render.return_value = 'plain text'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        ProposalEmailService.send_documents_to_client(
            email_proposal,
            attachments=[],
            subject='Asunto personalizado',
            greeting='Querido Cliente',
            body='Cuerpo del mensaje.',
            footer='Pie de mensaje.',
        )

        call_kwargs = mock_email_cls.call_args
        assert call_kwargs[1]['subject'] == 'Asunto personalizado'

    def test_returns_false_when_no_client_email(self, no_email_proposal):
        """Returns False immediately when proposal has no client_email."""
        result = ProposalEmailService.send_documents_to_client(
            no_email_proposal,
            attachments=[('doc.pdf', b'%PDF', 'application/pdf')],
        )
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string', side_effect=Exception('SMTP failure'))
    def test_returns_false_on_send_exception(self, mock_render, email_proposal):
        """Returns False and logs when email sending raises an exception."""
        result = ProposalEmailService.send_documents_to_client(
            email_proposal,
            attachments=[('doc.pdf', b'%PDF', 'application/pdf')],
            subject='S',
            greeting='G',
            body='B',
            footer='F',
        )
        assert result is False


class TestTemplateDisabledReturnsEarly:
    """Each send method returns False when its template is disabled via EmailTemplateConfig."""

    def _disable_template(self, template_key):
        EmailTemplateConfig.objects.create(
            template_key=template_key,
            is_active=False,
        )

    def test_send_proposal_to_client_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_sent_client')
        assert ProposalEmailService.send_proposal_to_client(email_proposal) is False

    def test_send_reminder_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_reminder')
        assert ProposalEmailService.send_reminder(email_proposal) is False

    def test_send_urgency_email_returns_false_when_discount_template_disabled(self, email_proposal):
        self._disable_template('proposal_urgency')
        assert ProposalEmailService.send_urgency_email(email_proposal) is False

    def test_send_urgency_email_returns_false_when_no_discount_template_disabled(self, email_proposal):
        email_proposal.discount_percent = 0
        email_proposal.save(update_fields=['discount_percent'])
        self._disable_template('proposal_urgency_no_discount')
        assert ProposalEmailService.send_urgency_email(email_proposal) is False

    def test_send_response_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_response_notification')
        assert ProposalEmailService.send_response_notification(email_proposal, 'accepted') is False

    def test_send_acceptance_confirmation_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_accepted_client')
        assert ProposalEmailService.send_acceptance_confirmation(email_proposal) is False

    def test_send_rejection_thank_you_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_rejected_client')
        assert ProposalEmailService.send_rejection_thank_you(email_proposal) is False

    def test_send_first_view_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_first_view_notification')
        assert ProposalEmailService.send_first_view_notification(email_proposal) is False

    def test_send_comment_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_comment_notification')
        assert ProposalEmailService.send_comment_notification(email_proposal, 'test') is False

    def test_send_rejection_reengagement_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_reengagement')
        assert ProposalEmailService.send_rejection_reengagement(email_proposal) is False

    def test_send_revisit_alert_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_revisit_alert')
        assert ProposalEmailService.send_revisit_alert(email_proposal, visit_count=3) is False

    def test_send_abandonment_followup_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_abandonment_followup')
        assert ProposalEmailService.send_abandonment_followup(email_proposal) is False

    def test_send_investment_interest_followup_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_investment_interest_followup')
        assert ProposalEmailService.send_investment_interest_followup(email_proposal) is False

    def test_send_share_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_share_notification')
        share = ProposalShareLink.objects.create(
            proposal=email_proposal, shared_by_name='Alice',
        )
        assert ProposalEmailService.send_share_notification(email_proposal, share) is False

    def test_send_scheduled_followup_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_scheduled_followup')
        assert ProposalEmailService.send_scheduled_followup(email_proposal) is False

    def test_send_stakeholder_detected_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_stakeholder_detected')
        assert ProposalEmailService.send_stakeholder_detected_notification(email_proposal, 3) is False

    def test_send_seller_inactivity_escalation_returns_false_when_disabled(self, email_proposal):
        self._disable_template('seller_inactivity_escalation')
        assert ProposalEmailService.send_seller_inactivity_escalation(email_proposal, 7) is False

    def test_send_negotiation_notification_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_negotiation_notification')
        assert ProposalEmailService.send_negotiation_notification(email_proposal) is False

    def test_send_negotiation_confirmation_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_negotiation_confirmation')
        assert ProposalEmailService.send_negotiation_confirmation(email_proposal) is False

    def test_send_post_rejection_revisit_alert_returns_false_when_disabled(self, email_proposal):
        self._disable_template('post_rejection_revisit_alert')
        assert ProposalEmailService.send_post_rejection_revisit_alert(email_proposal) is False

    def test_send_daily_pipeline_digest_returns_false_when_disabled(self):
        self._disable_template('daily_pipeline_digest')
        digest_data = {
            'viewed_yesterday': [], 'inactive': [], 'expiring_soon': [],
            'total_active': 0, 'date': '2026-03-10',
        }
        assert ProposalEmailService.send_daily_pipeline_digest(digest_data) is False

    def test_send_post_expiration_visit_alert_returns_false_when_disabled(self, email_proposal):
        self._disable_template('proposal_post_expiration_visit')
        assert ProposalEmailService.send_post_expiration_visit_alert(email_proposal) is False


# ── User-composed emails (branded & proposal) ──────────────────

class TestSendComposedEmail:
    """Tests for _send_composed_email shared implementation."""

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_sends_email_with_html_and_text_alternatives(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Test</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Subject',
            'Hola', ['Section 1'],
        )

        assert result is True
        mock_instance.attach_alternative.assert_called_once()
        mock_instance.send.assert_called_once_with(fail_silently=False)

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_logs_email_on_success(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>OK</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Subject',
            'Hola', ['Sec 1'], footer='Bye',
        )

        log = EmailLog.objects.get(proposal=email_proposal, template_key='branded_email')
        assert log.status == 'sent'
        assert log.metadata['greeting'] == 'Hola'
        assert log.metadata['sections'] == ['Sec 1']
        assert log.metadata['footer'] == 'Bye'

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_logs_email_on_failure(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>Fail</html>'
        mock_instance = _stub_email()
        mock_instance.send.side_effect = Exception('SMTP down')
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Subject',
            'Hi', ['Content'],
        )

        assert result is False
        log = EmailLog.objects.get(proposal=email_proposal, template_key='branded_email')
        assert log.status == 'failed'
        assert 'SMTP down' in log.error_message

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_renders_templates_from_registry(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>T</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Sub',
            'Hi', ['Sec'],
        )

        template_paths = [call[0][0] for call in mock_render.call_args_list]
        assert 'emails/branded_email.html' in template_paths
        assert 'emails/branded_email.txt' in template_paths

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_attaches_files_when_provided(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>A</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        attachments = [
            ('doc.pdf', b'pdfdata', 'application/pdf'),
            ('img.png', b'pngdata', 'image/png'),
        ]
        ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Sub',
            'Hi', ['Sec'], attachments=attachments,
        )

        assert mock_instance.attach.call_count == 2
        mock_instance.attach.assert_any_call('doc.pdf', b'pdfdata', 'application/pdf')

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_skips_attachments_when_none(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>N</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Sub',
            'Hi', ['Sec'], attachments=None,
        )

        assert mock_instance.attach.call_count == 0, "attach should not be called when attachments is None"
        mock_instance.attach.assert_not_called()

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_metadata_includes_attachment_names(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>M</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Sub',
            'Hi', ['Sec'], attachments=[('file.pdf', b'data', 'application/pdf')],
        )

        log = EmailLog.objects.get(proposal=email_proposal, template_key='branded_email')
        assert log.metadata['attachment_names'] == ['file.pdf']

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_false_on_smtp_error(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>E</html>'
        mock_instance = _stub_email()
        mock_instance.send.side_effect = ConnectionError('refused')
        mock_email_cls.return_value = mock_instance

        result = ProposalEmailService._send_composed_email(
            'branded_email', email_proposal, 'test@example.com', 'Sub',
            'Hi', ['Sec'],
        )

        assert result is False


class TestSendBrandedEmail:
    """Tests for the send_branded_email wrapper."""

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_delegates_with_branded_template_key(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>B</html>'
        mock_email_cls.return_value = _stub_email()

        result = ProposalEmailService.send_branded_email(
            email_proposal, 'test@example.com', 'Subject', 'Hi', ['Sec'],
        )

        assert result is True
        log = EmailLog.objects.get(proposal=email_proposal)
        assert log.template_key == 'branded_email'

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_does_not_create_change_log(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>B</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_branded_email(
            email_proposal, 'test@example.com', 'Subject', 'Hi', ['Sec'],
        )

        assert not ProposalChangeLog.objects.filter(
            proposal=email_proposal, change_type='email_sent',
        ).exists()


class TestSendProposalEmailMethod:
    """Tests for the send_proposal_email wrapper with activity logging."""

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_creates_change_log_on_success(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>P</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_proposal_email(
            email_proposal, 'test@example.com', 'Proposal Email', 'Hi', ['Sec'],
        )

        log = ProposalChangeLog.objects.get(
            proposal=email_proposal, change_type='email_sent',
        )
        assert 'test@example.com' in log.description
        assert 'Proposal Email' in log.description

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_updates_last_activity_at_on_success(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>P</html>'
        mock_email_cls.return_value = _stub_email()
        old_activity = email_proposal.last_activity_at

        ProposalEmailService.send_proposal_email(
            email_proposal, 'test@example.com', 'Sub', 'Hi', ['Sec'],
        )

        email_proposal.refresh_from_db()
        assert email_proposal.last_activity_at != old_activity

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_does_not_create_change_log_on_failure(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>F</html>'
        mock_instance = _stub_email()
        mock_instance.send.side_effect = Exception('fail')
        mock_email_cls.return_value = mock_instance

        ProposalEmailService.send_proposal_email(
            email_proposal, 'test@example.com', 'Sub', 'Hi', ['Sec'],
        )

        assert not ProposalChangeLog.objects.filter(
            proposal=email_proposal, change_type='email_sent',
        ).exists()

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_change_log_uses_enum_constants(self, mock_render, mock_email_cls, email_proposal):
        mock_render.return_value = '<html>E</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_proposal_email(
            email_proposal, 'test@example.com', 'Sub', 'Hi', ['Sec'],
        )

        log = ProposalChangeLog.objects.get(proposal=email_proposal)
        assert log.change_type == ProposalChangeLog.ChangeType.EMAIL_SENT
        assert log.actor_type == ProposalChangeLog.ActorType.SELLER


# ---------------------------------------------------------------------------
# Project-stage notifications (internal team)
# ---------------------------------------------------------------------------

from datetime import date  # noqa: E402

from content.models import ProposalProjectStage  # noqa: E402


@pytest.fixture
def stage_proposal(db):
    """A proposal in `accepted` status with stage rows attached."""
    proposal = BusinessProposal.objects.create(
        title='Stage Test Proposal',
        client_name='Stage Client',
        client_email='stageclient@test.com',
        language='es',
        total_investment=Decimal('15000000'),
        currency='COP',
        status='accepted',
        expires_at=timezone.now() + timezone.timedelta(days=10),
    )
    return proposal


@pytest.fixture
def design_stage(db, stage_proposal):
    return ProposalProjectStage.objects.create(
        proposal=stage_proposal,
        stage_key='design',
        order=0,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 11),
    )


class TestSendStageWarning:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_true_on_successful_send(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>warn</html>'
        mock_email_cls.return_value = _stub_email()

        result = ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )

        assert result is True
        mock_email_cls.return_value.send.assert_called_once()

    @override_settings(NOTIFICATION_EMAIL='team@projectapp.co,carlos18bp@gmail.com')
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_uses_notification_recipients_from_settings(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>warn</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )

        call_kwargs = mock_email_cls.call_args[1]
        assert call_kwargs['to'] == [
            'team@projectapp.co',
            'carlos18bp@gmail.com',
        ]

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_subject_contains_stage_label_and_client(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>warn</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )

        subject = mock_email_cls.call_args[1]['subject']
        assert 'Diseño' in subject
        assert stage_proposal.client_name in subject

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_attaches_html_alternative(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>warn</html>'
        mock_instance = _stub_email()
        mock_email_cls.return_value = mock_instance

        ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )

        mock_instance.attach_alternative.assert_called_once()
        args = mock_instance.attach_alternative.call_args.args
        assert args[1] == 'text/html'

    def test_returns_false_when_template_disabled(
        self, stage_proposal, design_stage,
    ):
        EmailTemplateConfig.objects.create(
            template_key='proposal_stage_warning_notification',
            is_active=False,
        )
        result = ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )
        assert result is False

    @patch('content.services.proposal_email_service.render_to_string')
    def test_returns_false_on_exception(
        self, mock_render, stage_proposal, design_stage,
    ):
        mock_render.side_effect = Exception('boom')
        result = ProposalEmailService.send_stage_warning(
            stage_proposal, design_stage, days_remaining=2,
        )
        assert result is False


class TestSendStageOverdue:
    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_subject_contains_vencida_marker(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>overdue</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_stage_overdue(
            stage_proposal, design_stage, days_overdue=3,
        )

        subject = mock_email_cls.call_args[1]['subject']
        assert 'VENCIDA' in subject
        assert 'Diseño' in subject

    @patch('content.services.proposal_email_service.EmailMultiAlternatives')
    @patch('content.services.proposal_email_service.render_to_string')
    def test_text_body_includes_overdue_humanized_label(
        self, mock_render, mock_email_cls, stage_proposal, design_stage,
    ):
        mock_render.return_value = '<html>overdue</html>'
        mock_email_cls.return_value = _stub_email()

        ProposalEmailService.send_stage_overdue(
            stage_proposal, design_stage, days_overdue=8,
        )

        # The shared helper builds the context dict and passes it to
        # render_to_string. Inspect the second positional arg of the first call.
        first_call_context = mock_render.call_args_list[0].args[1]
        assert first_call_context['days_overdue'] == 8
        assert first_call_context['time_overdue_human'] == '1 semana 1 día'

    def test_returns_false_when_template_disabled(
        self, stage_proposal, design_stage,
    ):
        EmailTemplateConfig.objects.create(
            template_key='proposal_stage_overdue_notification',
            is_active=False,
        )
        result = ProposalEmailService.send_stage_overdue(
            stage_proposal, design_stage, days_overdue=3,
        )
        assert result is False
