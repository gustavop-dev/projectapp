"""Tests for the manual discount-offer send, team-copy of automated emails,
and the automations-enabled-by-default behavior."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from content.models import BusinessProposal
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


class TestTeamCopy:
    def test_reminder_sends_client_and_team_copy(self, mailoutbox):
        proposal = _proposal(discount_percent=0)  # plain reminder, no discount
        ProposalEmailService.send_reminder(proposal)

        # One email to the client + one copy to the team inbox.
        assert len(mailoutbox) == 2
        team = [m for m in mailoutbox if 'team@projectapp.co' in m.to]
        assert len(team) == 1
        assert team[0].subject.startswith('[Cliente: Ana Cliente]')

    def test_team_copy_helper_prefixes_subject(self, mailoutbox, settings):
        settings.AUTOMATED_EMAIL_TEAM_COPY = 'team@projectapp.co'
        proposal = _proposal()
        ProposalEmailService._send_team_copy(
            subject='Tu propuesta expira pronto',
            text_body='texto',
            html_body='<p>html</p>',
            proposal=proposal,
        )
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ['team@projectapp.co']
        assert mailoutbox[0].subject == '[Cliente: Ana Cliente] Tu propuesta expira pronto'


class TestAutomationsDefault:
    def test_new_proposal_has_automations_enabled(self):
        proposal = BusinessProposal.objects.create(title='Fresh', client_name='X')
        assert proposal.automations_paused is False
