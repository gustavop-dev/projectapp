"""Tests for ProposalService.compute_validity_text (shared PDF/web sentence)."""
from datetime import datetime, timezone as dt_timezone

import pytest

from content.models import BusinessProposal
from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db

SENT = datetime(2026, 7, 16, 10, 0, tzinfo=dt_timezone.utc)
EXPIRES = datetime(2026, 8, 6, 10, 0, tzinfo=dt_timezone.utc)


def _proposal(**kwargs):
    return BusinessProposal.objects.create(
        title='Vigencia', client_name='Cliente', **kwargs,
    )


class TestComputeValidityText:
    def test_none_without_expiry(self):
        proposal = _proposal(expires_at=None)
        assert ProposalService.compute_validity_text(proposal) is None

    def test_sent_proposal_states_period_and_deadline_es(self):
        proposal = _proposal(sent_at=SENT, expires_at=EXPIRES)
        text = ProposalService.compute_validity_text(proposal)
        assert 'vigencia de 21 días calendario' in text
        assert 'su fecha de envío' in text
        assert 'válida hasta el 6 de agosto de 2026' in text

    def test_unsent_proposal_counts_from_issue_date(self):
        proposal = _proposal(expires_at=EXPIRES)
        proposal.created_at = SENT
        proposal.save(update_fields=['created_at'])
        text = ProposalService.compute_validity_text(proposal)
        assert 'su fecha de emisión' in text

    def test_english_proposal_uses_english_sentence(self):
        proposal = _proposal(language='en', sent_at=SENT, expires_at=EXPIRES)
        text = ProposalService.compute_validity_text(proposal)
        assert 'valid for 21 calendar days' in text
        assert 'valid until August 6, 2026' in text

    def test_expiry_before_reference_falls_back_to_deadline_only(self):
        proposal = _proposal(sent_at=EXPIRES, expires_at=SENT)
        text = ProposalService.compute_validity_text(proposal)
        assert text.startswith('Esta propuesta es válida hasta el')
