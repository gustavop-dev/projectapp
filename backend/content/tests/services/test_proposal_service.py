"""Tests for ProposalService.

Covers: get_default_sections() for ES and EN languages,
send_proposal() happy path and error cases.
"""
from datetime import datetime, timedelta
from datetime import timezone as dt_tz
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from content.models import BusinessProposal
from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db


class TestGetDefaultSections:
    def test_returns_14_sections_for_es(self):
        """Verify ES defaults include all 14 section types (greeting through next_steps)."""
        sections = ProposalService.get_default_sections('es')
        assert len(sections) == 14

    def test_returns_14_sections_for_en(self):
        """Verify EN defaults include all 14 section types (greeting through next_steps)."""
        sections = ProposalService.get_default_sections('en')
        assert len(sections) == 14

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

    def test_section_types_cover_all_14_types(self):
        """Verify all 14 section types are present in the ES defaults."""
        expected_types = {
            'greeting', 'executive_summary', 'context_diagnostic',
            'conversion_strategy', 'design_ux', 'creative_support',
            'development_stages', 'process_methodology',
            'functional_requirements',
            'timeline', 'investment', 'proposal_summary',
            'final_note', 'next_steps',
        }
        sections = ProposalService.get_default_sections('es')
        actual_types = {s['section_type'] for s in sections}
        assert actual_types == expected_types

    def test_en_sections_have_english_titles(self):
        sections = ProposalService.get_default_sections('en')
        greeting = next(s for s in sections if s['section_type'] == 'greeting')
        assert 'Greeting' in greeting['title']

    def test_es_sections_have_spanish_content(self):
        """Verify ES executive_summary section has Spanish content in its content_json."""
        sections = ProposalService.get_default_sections('es')
        es_section = next(s for s in sections if s['section_type'] == 'executive_summary')
        assert 'Resumen' in es_section['content_json']['title']

    def test_functional_requirements_has_default_groups(self):
        """Verify ES functional_requirements has 6 groups including analytics_dashboard."""
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        groups = fr['content_json']['groups']
        assert len(groups) == 6
        group_ids = {g['id'] for g in groups}
        assert group_ids == {
            'views', 'components', 'features',
            'integrations_api', 'admin_module', 'analytics_dashboard',
        }

    def test_views_group_has_13_default_items(self):
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        views = next(g for g in fr['content_json']['groups'] if g['id'] == 'views')
        assert len(views['items']) == 13

    def test_components_group_has_5_default_items(self):
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        components = next(g for g in fr['content_json']['groups'] if g['id'] == 'components')
        assert len(components['items']) == 5

    def test_features_group_has_6_default_items(self):
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        features = next(g for g in fr['content_json']['groups'] if g['id'] == 'features')
        assert len(features['items']) == 6

    def test_integrations_api_group_has_2_default_items(self):
        sections = ProposalService.get_default_sections('es')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        integrations = next(g for g in fr['content_json']['groups'] if g['id'] == 'integrations_api')
        assert len(integrations['items']) == 2
        names = {item['name'] for item in integrations['items']}
        assert 'Internacionales' in names
        assert 'Regionales (Colombia)' in names

    def test_greeting_title_has_emoji(self):
        sections = ProposalService.get_default_sections('es')
        greeting = next(s for s in sections if s['section_type'] == 'greeting')
        assert greeting['title'].startswith('\U0001f44b')

    def test_en_functional_requirements_has_6_groups(self):
        """Verify EN functional_requirements has 6 groups including analytics_dashboard."""
        sections = ProposalService.get_default_sections('en')
        fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
        groups = fr['content_json']['groups']
        assert len(groups) == 6
        group_ids = {g['id'] for g in groups}
        assert group_ids == {
            'views', 'components', 'features',
            'integrations_api', 'admin_module', 'analytics_dashboard',
        }

    def test_development_stages_has_current_stage(self):
        sections = ProposalService.get_default_sections('es')
        ds = next(s for s in sections if s['section_type'] == 'development_stages')
        stages = ds['content_json']['stages']
        current_stages = [s for s in stages if s.get('current')]
        assert len(current_stages) == 1

    def test_defaults_to_es_for_unknown_language(self):
        """Unknown language code falls back to Spanish defaults (14 sections)."""
        sections = ProposalService.get_default_sections('fr')
        assert len(sections) == 14


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

    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_sets_status_to_sent(self, mock_reminder, mock_urgency):
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Send Test',
            client_name='Client',
            client_email='client@test.com',
        )
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'sent'
        mock_reminder.schedule.assert_called_once()

    @freeze_time('2025-06-01 12:00:00')
    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_sets_sent_at_timestamp(self, mock_reminder, mock_urgency):
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Timestamp Test',
            client_name='Client',
            client_email='client@test.com',
        )
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.sent_at == datetime(2025, 6, 1, 12, 0, 0, tzinfo=dt_tz.utc)
        mock_reminder.schedule.assert_called_once()
        mock_urgency.schedule.assert_called_once()

    @freeze_time('2025-06-01 12:00:00')
    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_schedules_both_reminder_and_urgency_tasks(self, mock_reminder, mock_urgency):
        """Both reminder (day 10) and urgency (day 15) tasks are scheduled."""
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Reminder Test',
            client_name='Client',
            client_email='client@test.com',
            reminder_days=10,
            urgency_reminder_days=15,
        )
        ProposalService.send_proposal(proposal)
        mock_reminder.schedule.assert_called_once()
        mock_urgency.schedule.assert_called_once()
        reminder_delay = mock_reminder.schedule.call_args[1]['delay']
        assert reminder_delay == 10 * 86400
        urgency_delay = mock_urgency.schedule.call_args[1]['delay']
        assert urgency_delay == 15 * 86400

    @freeze_time('2025-06-01 12:00:00')
    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_auto_sets_expires_at_to_20_days(self, mock_reminder, mock_urgency):
        """When expires_at is not set, send_proposal auto-sets it to 20 days."""
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Auto Expiry Test',
            client_name='Client',
            client_email='client@test.com',
        )
        assert proposal.expires_at is None
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.expires_at == datetime(2025, 6, 21, 12, 0, 0, tzinfo=dt_tz.utc)
        mock_reminder.schedule.assert_called_once()
        mock_urgency.schedule.assert_called_once()

    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_logs_exception_when_schedule_fails(self, mock_reminder, mock_urgency):
        """send_proposal still marks as sent even if task scheduling fails."""
        mock_reminder.schedule = MagicMock(side_effect=RuntimeError('Huey unavailable'))
        mock_urgency.schedule = MagicMock(return_value=None)
        proposal = BusinessProposal.objects.create(
            title='Exception Test',
            client_name='Client',
            client_email='client@test.com',
        )
        ProposalService.send_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'sent'
        mock_reminder.schedule.assert_called_once()


class TestResendProposal:
    def test_raises_error_without_client_email(self):
        """Resend should fail if no client_email is set."""
        proposal = BusinessProposal.objects.create(
            title='No Email Resend',
            client_name='Client',
            client_email='',
            status='sent',
        )
        with pytest.raises(ValueError, match='email'):
            ProposalService.resend_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'sent'

    @freeze_time('2025-06-01 12:00:00')
    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_keeps_existing_expires_at(self, mock_reminder, mock_urgency):
        """Resend should not change the existing expires_at."""
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        original_expiry = datetime(2025, 7, 1, 12, 0, 0, tzinfo=dt_tz.utc)
        proposal = BusinessProposal.objects.create(
            title='Resend Test',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            expires_at=original_expiry,
        )
        ProposalService.resend_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'sent'
        assert proposal.expires_at == original_expiry
        assert proposal.reminder_sent_at is None
        assert proposal.urgency_email_sent_at is None
        mock_reminder.schedule.assert_called_once()
        mock_urgency.schedule.assert_called_once()

    @freeze_time('2025-06-01 12:00:00')
    @patch('content.tasks.send_urgency_reminder')
    @patch('content.tasks.send_proposal_reminder')
    def test_resets_email_tracking_fields(self, mock_reminder, mock_urgency):
        """Resend should reset reminder_sent_at and urgency_email_sent_at."""
        mock_reminder.schedule = MagicMock(return_value=None)
        mock_urgency.schedule = MagicMock(return_value=None)
        now = datetime(2025, 6, 1, 12, 0, 0, tzinfo=dt_tz.utc)
        proposal = BusinessProposal.objects.create(
            title='Reset Fields Test',
            client_name='Client',
            client_email='client@test.com',
            status='viewed',
            expires_at=now + timedelta(days=30),
            reminder_sent_at=now - timedelta(days=2),
            urgency_email_sent_at=now - timedelta(days=1),
        )
        ProposalService.resend_proposal(proposal)
        proposal.refresh_from_db()
        assert proposal.reminder_sent_at is None
        assert proposal.urgency_email_sent_at is None
        assert proposal.sent_at == now
        mock_reminder.schedule.assert_called_once()
        mock_urgency.schedule.assert_called_once()


class TestRecordView:
    def test_increments_view_count(self):
        proposal = BusinessProposal.objects.create(
            title='View Test',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )
        assert proposal.view_count == 0
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        assert proposal.view_count == 1

    @freeze_time('2026-03-01 12:00:00')
    def test_sets_first_viewed_at_on_first_visit(self):
        proposal = BusinessProposal.objects.create(
            title='First View',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )
        assert proposal.first_viewed_at is None
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        assert proposal.first_viewed_at is not None

    @freeze_time('2026-03-01 12:00:00')
    def test_does_not_overwrite_first_viewed_at_on_second_visit(self):
        proposal = BusinessProposal.objects.create(
            title='Second View',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        first_ts = proposal.first_viewed_at
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        assert proposal.first_viewed_at == first_ts
        assert proposal.view_count == 2

    def test_updates_status_from_sent_to_viewed(self):
        proposal = BusinessProposal.objects.create(
            title='Status View',
            client_name='Client',
            client_email='client@test.com',
            status='sent',
        )
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'viewed'

    def test_does_not_update_status_when_not_sent(self):
        proposal = BusinessProposal.objects.create(
            title='Draft View',
            client_name='Client',
            client_email='client@test.com',
            status='draft',
        )
        ProposalService.record_view(proposal)
        proposal.refresh_from_db()
        assert proposal.status == 'draft'


class TestCheckExpiration:
    @freeze_time('2026-03-01 12:00:00')
    def test_returns_true_for_expired_proposal(self):
        proposal = BusinessProposal.objects.create(
            title='Expired',
            client_name='Client',
            client_email='c@test.com',
            expires_at=datetime(2026, 2, 28, 12, 0, 0, tzinfo=dt_tz.utc),
        )
        assert ProposalService.check_expiration(proposal) is True

    @freeze_time('2026-03-01 12:00:00')
    def test_returns_false_for_active_proposal(self):
        proposal = BusinessProposal.objects.create(
            title='Active',
            client_name='Client',
            client_email='c@test.com',
            expires_at=datetime(2026, 4, 1, 12, 0, 0, tzinfo=dt_tz.utc),
        )
        assert ProposalService.check_expiration(proposal) is False
