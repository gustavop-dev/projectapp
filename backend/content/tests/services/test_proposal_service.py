"""
Tests for ProposalService.

Covers: get_default_sections() for ES and EN languages,
send_proposal() happy path and error cases.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from content.models import BusinessProposal
from content.services.proposal_service import ProposalService


pytestmark = pytest.mark.django_db


class TestGetDefaultSections:
    def test_returns_12_sections_for_es(self):
        sections = ProposalService.get_default_sections('es')
        assert len(sections) == 12

    def test_returns_12_sections_for_en(self):
        sections = ProposalService.get_default_sections('en')
        assert len(sections) == 12

    def test_all_sections_have_required_keys(self):
        sections = ProposalService.get_default_sections('es')
        required_keys = {'section_type', 'title', 'order', 'is_wide_panel', 'content_json'}
        for section in sections:
            assert required_keys.issubset(section.keys()), (
                f"Section {section.get('section_type')} missing keys: "
                f"{required_keys - section.keys()}"
            )

    def test_sections_ordered_by_order_field(self):
        sections = ProposalService.get_default_sections('es')
        orders = [s['order'] for s in sections]
        assert orders == sorted(orders)

    def test_section_types_cover_all_12_types(self):
        expected_types = {
            'greeting', 'executive_summary', 'context_diagnostic',
            'conversion_strategy', 'design_ux', 'creative_support',
            'development_stages', 'functional_requirements',
            'timeline', 'investment', 'final_note', 'next_steps',
        }
        sections = ProposalService.get_default_sections('es')
        actual_types = {s['section_type'] for s in sections}
        assert actual_types == expected_types

    def test_en_sections_have_english_titles(self):
        sections = ProposalService.get_default_sections('en')
        greeting = next(s for s in sections if s['section_type'] == 'greeting')
        assert 'Greeting' in greeting['title']

    def test_es_sections_have_spanish_content(self):
        sections = ProposalService.get_default_sections('es')
        es_section = next(s for s in sections if s['section_type'] == 'executive_summary')
        assert 'Resumen' in es_section['title'] or 'ejecutivo' in es_section['title'].lower()

    def test_functional_requirements_has_default_groups(self):
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        groups = fr['content_json']['groups']
        assert len(groups) >= 4
        group_ids = {g['id'] for g in groups}
        assert {'views', 'components', 'features', 'admin_module'}.issubset(group_ids)

    def test_development_stages_has_current_stage(self):
        sections = ProposalService.get_default_sections('es')
        ds = next(s for s in sections if s['section_type'] == 'development_stages')
        stages = ds['content_json']['stages']
        current_stages = [s for s in stages if s.get('current')]
        assert len(current_stages) == 1

    def test_defaults_to_es_for_unknown_language(self):
        sections = ProposalService.get_default_sections('fr')
        assert len(sections) == 12


class TestSendProposal:
    def test_raises_error_without_client_email(self):
        proposal = BusinessProposal.objects.create(
            title='No Email',
            client_name='Client',
            client_email='',
        )
        with pytest.raises(ValueError, match='email'):
            ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'draft'

    @patch('content.tasks.send_proposal_reminder')
    def test_sets_status_to_sent(self, mock_task):
        mock_task.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Send Test',
            client_name='Client',
            client_email='client@test.com',
        )
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'sent'
        mock_task.schedule.assert_called_once()

    @patch('content.tasks.send_proposal_reminder')
    def test_sets_sent_at_timestamp(self, mock_task):
        mock_task.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Timestamp Test',
            client_name='Client',
            client_email='client@test.com',
        )
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.sent_at is not None
        mock_task.schedule.assert_called_once()

    @patch('content.tasks.send_proposal_reminder')
    def test_schedules_reminder_task_with_correct_delay(self, mock_task):
        mock_task.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Reminder Test',
            client_name='Client',
            client_email='client@test.com',
            reminder_days=5,
        )
        ProposalService.send_proposal(proposal)
        mock_task.schedule.assert_called_once()
        call_kwargs = mock_task.schedule.call_args
        assert call_kwargs[1]['delay'] == 5 * 86400
