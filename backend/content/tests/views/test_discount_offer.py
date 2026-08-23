"""Tests for discount sends, configured client copies and automations."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import BusinessProposal, ClientEmailCopyRecipient, EmailLog
from content.services.proposal_email_service import ProposalEmailService

pytestmark = pytest.mark.django_db


def _proposal(**kwargs):
    defaults = dict(
        title='Discount Proposal',
        client_name='Ana Cliente',
        client_email='ana@test.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=10),
        discount_percent=15,
    )
    defaults.update(kwargs)
    return BusinessProposal.objects.create(**defaults)


class TestSendDiscountOfferEndpoint:
    def _url(self, proposal):
        return reverse('send-discount-offer', kwargs={'proposal_id': proposal.id})

    @patch(
        'content.services.proposal_email_service.ProposalEmailService.send_urgency_email',
        return_value=True,
    )
    def test_success_calls_service_with_force(self, mock_send, admin_client):
        proposal = _proposal()
        resp = admin_client.post(self._url(proposal), format='json')

        assert resp.status_code == 200
        mock_send.assert_called_once()
        _, kwargs = mock_send.call_args
        assert kwargs.get('force') is True

    def test_400_when_no_discount(self, admin_client):
        proposal = _proposal(discount_percent=0)
        resp = admin_client.post(self._url(proposal), format='json')

        assert resp.status_code == 400
        assert 'descuento' in resp.json()['error'].lower()

    def test_400_when_no_client_email(self, admin_client):
        proposal = _proposal(client_email='')
        resp = admin_client.post(self._url(proposal), format='json')

        assert resp.status_code == 400

    def test_requires_admin(self, api_client):
        proposal = _proposal()
        resp = api_client.post(self._url(proposal), format='json')

        assert resp.status_code in (401, 403)


class TestClientEmailCopy:
    def test_reminder_sends_configured_hidden_copy(self, mailoutbox):
        ClientEmailCopyRecipient.objects.create(email='audit@projectapp.co')
        proposal = _proposal(discount_percent=0)  # plain reminder, no discount

        ProposalEmailService.send_reminder(proposal)

        assert len(mailoutbox) == 2
        copy_message = mailoutbox[1]
        assert copy_message.to == []
        assert copy_message.bcc == ['audit@projectapp.co']

    def test_reminder_history_links_copy_to_primary_delivery(self, mailoutbox):
        ClientEmailCopyRecipient.objects.create(email='audit@projectapp.co')
        proposal = _proposal(discount_percent=0)

        ProposalEmailService.send_reminder(proposal)

        primary = EmailLog.objects.get(
            delivery_role=EmailLog.DeliveryRole.PRIMARY,
        )
        copy_log = EmailLog.objects.get(
            delivery_role=EmailLog.DeliveryRole.COPY,
        )

        assert copy_log.delivery_id == primary.delivery_id
        assert copy_log.recipient == 'audit@projectapp.co'


class TestAutomationsDefault:
    def test_new_proposal_has_automations_enabled(self):
        proposal = BusinessProposal.objects.create(title='Fresh', client_name='X')
        assert proposal.automations_paused is False
