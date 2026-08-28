"""Every proposal ships the incident-response card in its summary.

The card summarises CLAUSE 22 of the contract (attention to incidents, service
levels and operational continuity). It must state the response/resolution times
AND the fact that they only apply while the hosting and support service is
active — the contract ties them to that subscription, so a card that promised
them unconditionally would over-sell what the contract grants.
"""
import pytest

from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db


def _summary_cards(language):
    sections = ProposalService.get_default_sections(language)
    summary = next(
        s for s in sections if s['section_type'] == 'proposal_summary'
    )
    return summary['content_json']['cards']


class TestIncidentCardInDefaultSummary:
    @pytest.mark.parametrize('language', ['es', 'en'])
    def test_card_is_present(self, language):
        cards = _summary_cards(language)
        incident = [c for c in cards if c['icon'] == '🚨']
        assert len(incident) == 1, 'exactly one incident card per proposal'
        assert incident[0]['source'] == 'static'
        assert incident[0]['title']

    @pytest.mark.parametrize(
        'language,needles',
        [
            ('es', ['4 horas hábiles', '1 día hábil', '5 días hábiles',
                    '9 días hábiles']),
            ('en', ['4 business-hour', '1 business day', '5 business days',
                    '9 business days']),
        ],
    )
    def test_card_states_the_three_service_levels(self, language, needles):
        """Critical / medium / low, with the times the contract commits to."""
        card = next(c for c in _summary_cards(language) if c['icon'] == '🚨')
        for needle in needles:
            assert needle in card['description']

    @pytest.mark.parametrize(
        'language,needle',
        [
            ('es', 'mientras el servicio de hosting y soporte esté vigente'),
            ('en', 'while the hosting and support service is active'),
        ],
    )
    def test_card_declares_the_hosting_condition(self, language, needle):
        """Without this the card promises an SLA the contract conditions."""
        card = next(c for c in _summary_cards(language) if c['icon'] == '🚨')
        assert needle in card['description']

    @pytest.mark.parametrize('language', ['es', 'en'])
    def test_existing_cards_survive(self, language):
        """The card is added, never swapped in for one that was already there."""
        sources = [c['source'] for c in _summary_cards(language)]
        assert 'total_investment' in sources
        assert 'timeline_duration' in sources
        assert 'expires_at' in sources
