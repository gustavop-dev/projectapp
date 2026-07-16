"""Tests for ProposalService.apply_hosting_defaults (admin-editable hosting seeds)."""
import pytest

from content.models import BusinessProposal, ProposalDefaultConfig
from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db


def _proposal(**kwargs):
    return BusinessProposal.objects.create(
        title='Hosting defaults', client_name='Cliente', **kwargs,
    )


def _config(**kwargs):
    defaults = {
        'language': 'es',
        'hosting_percent': 45,
        'hosting_discount_annual': 35,
        'hosting_discount_semiannual': 15,
        'hosting_discount_quarterly': 5,
    }
    defaults.update(kwargs)
    return ProposalDefaultConfig.objects.create(**defaults)


class TestApplyHostingDefaults:
    def test_noop_without_config_row(self):
        ProposalDefaultConfig.objects.all().delete()
        proposal = _proposal()
        ProposalService.apply_hosting_defaults(proposal, set())
        proposal.refresh_from_db()
        assert proposal.hosting_percent == 60  # model default untouched

    def test_fills_all_fields_absent_from_payload(self):
        ProposalDefaultConfig.objects.all().delete()
        _config()
        proposal = _proposal()
        ProposalService.apply_hosting_defaults(proposal, {'title', 'client_name'})
        proposal.refresh_from_db()
        assert proposal.hosting_percent == 45
        assert proposal.hosting_discount_annual == 35
        assert proposal.hosting_discount_semiannual == 15
        assert proposal.hosting_discount_quarterly == 5

    def test_payload_fields_win_over_config(self):
        ProposalDefaultConfig.objects.all().delete()
        _config()
        proposal = _proposal(hosting_percent=70)
        ProposalService.apply_hosting_defaults(proposal, {'hosting_percent'})
        proposal.refresh_from_db()
        assert proposal.hosting_percent == 70          # explicit value kept
        assert proposal.hosting_discount_annual == 35  # absent field seeded

    def test_matches_config_by_proposal_language(self):
        ProposalDefaultConfig.objects.all().delete()
        _config(language='en', hosting_percent=33)
        proposal = _proposal(language='es')
        ProposalService.apply_hosting_defaults(proposal, set())
        proposal.refresh_from_db()
        assert proposal.hosting_percent == 60  # no es-config -> untouched
