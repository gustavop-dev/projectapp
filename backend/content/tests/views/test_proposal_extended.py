"""Tests for extended proposal views, services, serializers and tasks.

Covers edge cases and uncovered branches across:
- content/views/proposal.py
- content/services/proposal_email_service.py
- content/tasks.py
- content/serializers/proposal.py
- content/views/email_templates.py
- content/views/portfolio_works.py
- content/models/email_log.py
- content/serializers/blog.py
"""
import copy
from datetime import datetime, timedelta
from datetime import timezone as dt_tz
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from content.models import (
    BusinessProposal,
    EmailLog,
    ProposalChangeLog,
    ProposalSection,
    ProposalSectionView,
    ProposalViewEvent,
)

pytestmark = pytest.mark.django_db

FROZEN_NOW = datetime(2026, 1, 15, 10, 0, 0, tzinfo=dt_tz.utc)


# ═══════════════════════════════════════════════════════════════════
# content/models/email_log.py — __str__
# ═══════════════════════════════════════════════════════════════════

class TestEmailLogStr:
    def test_str_representation(self, db):
        """EmailLog.__str__ returns 'template_key → recipient (status)'."""
        log = EmailLog.objects.create(
            template_key='proposal_sent',
            recipient='client@test.com',
            subject='Test',
            status='sent',
        )
        assert str(log) == 'proposal_sent → client@test.com (sent)'


# ═══════════════════════════════════════════════════════════════════
# content/views/portfolio_works.py — legacy endpoint
# ═══════════════════════════════════════════════════════════════════

class TestLegacyPortfolioWorksList:
    def test_legacy_endpoint_returns_200(self, db):
        """Legacy portfolio_works_list endpoint returns 200 with data."""
        from content.models import PortfolioWork
        from content.views.portfolio_works import portfolio_works_list

        PortfolioWork.objects.create(
            title_en='Test Work', title_es='Trabajo Test',
            project_url='https://example.com',
        )
        factory = APIRequestFactory()
        request = factory.get('/fake/')
        response = portfolio_works_list(request)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — email_deliverability_dashboard
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestEmailDeliverabilityDashboard:
    def test_returns_counts_and_rate(self, admin_client, db):
        """Dashboard returns correct counts and success rate."""
        EmailLog.objects.create(
            template_key='proposal_sent', recipient='a@t.com',
            subject='S1', status='sent', sent_at=FROZEN_NOW - timedelta(days=1),
        )
        EmailLog.objects.create(
            template_key='proposal_sent', recipient='b@t.com',
            subject='S2', status='delivered', sent_at=FROZEN_NOW - timedelta(days=2),
        )
        EmailLog.objects.create(
            template_key='proposal_reminder', recipient='c@t.com',
            subject='S3', status='failed', error_message='SMTP error',
            sent_at=FROZEN_NOW - timedelta(days=3),
        )
        EmailLog.objects.create(
            template_key='proposal_urgency', recipient='d@t.com',
            subject='S4', status='bounced', sent_at=FROZEN_NOW - timedelta(days=4),
        )

        url = reverse('email-deliverability-dashboard')
        response = admin_client.get(url)

        assert response.status_code == 200
        data = response.data
        assert data['total_emails_30d'] == 4
        assert data['sent_count'] == 2
        assert data['failed_count'] == 2
        assert data['success_rate'] == 50.0

    def test_returns_trend_and_failures(self, admin_client, db):
        """Dashboard returns daily_trend, by_template and recent_failures."""
        EmailLog.objects.create(
            template_key='proposal_sent', recipient='a@t.com',
            subject='S1', status='failed', error_message='err',
            sent_at=FROZEN_NOW - timedelta(days=1),
        )

        url = reverse('email-deliverability-dashboard')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert len(response.data['by_template']) >= 1
        assert len(response.data['daily_trend']) >= 1
        assert len(response.data['recent_failures']) >= 1

    def test_returns_empty_stats_with_no_logs(self, admin_client, db):
        """Dashboard returns zeros when no email logs exist."""
        url = reverse('email-deliverability-dashboard')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.data['total_emails_30d'] == 0
        assert response.data['success_rate'] == 0

    def test_requires_admin(self, api_client, db):
        """Dashboard requires admin authentication."""
        url = reverse('email-deliverability-dashboard')
        response = api_client.get(url)

        assert response.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — magic link rate-limit + exception handlers
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestMagicLinkRateLimit:
    def test_rate_limited_when_recent_magic_link_sent(self, api_client, db):
        """Magic link returns 200 without sending when rate-limited."""
        BusinessProposal.objects.create(
            title='Rate Limit Test', client_name='Client',
            client_email='ratelimit@test.com',
            total_investment=Decimal('5000.00'),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        EmailLog.objects.create(
            template_key='magic_link',
            recipient='ratelimit@test.com',
            subject='Magic Link',
            status='sent',
            sent_at=FROZEN_NOW - timedelta(minutes=2),
        )

        url = reverse('request-magic-link')
        with patch(
            'content.services.proposal_email_service'
            '.ProposalEmailService.send_magic_link_email',
        ) as mock_send:
            response = api_client.post(
                url, {'email': 'ratelimit@test.com'}, format='json',
            )
            mock_send.assert_not_called()

        assert response.status_code == 200

    def test_send_exception_handled_gracefully(self, api_client, db):
        """Magic link handles send_magic_link_email exception gracefully."""
        BusinessProposal.objects.create(
            title='Exception Test', client_name='Client',
            client_email='exception@test.com',
            total_investment=Decimal('5000.00'),
            expires_at=FROZEN_NOW + timedelta(days=10),
            is_active=True,
        )

        url = reverse('request-magic-link')
        with patch(
            'content.services.proposal_email_service'
            '.ProposalEmailService.send_magic_link_email',
            side_effect=Exception('SMTP down'),
        ):
            response = api_client.post(
                url, {'email': 'exception@test.com'}, format='json',
            )

        assert response.status_code == 200

    def test_rate_limit_db_exception_is_swallowed(self, api_client, db):
        """Magic link swallows DB exceptions during rate-limit check."""
        url = reverse('request-magic-link')
        with patch(
            'content.models.email_log.EmailLog.objects',
        ) as mock_qs:
            mock_qs.filter.return_value.exists.side_effect = Exception('DB lost')
            with patch(
                'content.services.proposal_email_service'
                '.ProposalEmailService.send_magic_link_email',
            ):
                response = api_client.post(
                    url, {'email': 'db-fail@test.com'}, format='json',
                )

        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — JSON template additionalModules annotation
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestJsonTemplateAnnotation:
    def test_do_not_remove_set_on_additional_modules(self, admin_client, db):
        """JSON template annotates _do_not_remove on additionalModules."""
        from content.services.proposal_service import ProposalService

        real_defaults = ProposalService.get_default_sections('es')
        patched = copy.deepcopy(real_defaults)
        for section in patched:
            if section['section_type'] == 'functional_requirements':
                section['content_json']['additionalModules'] = [
                    {'id': 'test_mod', 'title': 'Test Module'},
                ]
                break

        url = reverse('proposal-json-template')
        with patch(
            'content.services.proposal_service.ProposalService.get_default_sections',
            return_value=patched,
        ):
            response = admin_client.get(url)

        assert response.status_code == 200
        fr = response.data.get('functionalRequirements', {})
        mods = fr.get('additionalModules', [])
        assert len(mods) >= 1
        assert mods[0].get('_do_not_remove') is True


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — view_mode update, engagement declining
# reset, cached_heat_score exception
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestTrackProposalEngagementEdgeCases:
    @pytest.fixture
    def tracked_proposal(self, db):
        """A viewed proposal with tracking data."""
        p = BusinessProposal.objects.create(
            title='Track Test', client_name='Tracker',
            client_email='track@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            sent_at=FROZEN_NOW - timedelta(days=5),
            first_viewed_at=FROZEN_NOW - timedelta(days=3),
            last_activity_at=FROZEN_NOW - timedelta(hours=2),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        ProposalSection.objects.create(
            proposal=p, section_type='greeting', title='Greeting', order=0,
        )
        ProposalSection.objects.create(
            proposal=p, section_type='investment', title='Investment', order=1,
        )
        return p

    def test_view_mode_updated_on_existing_event(self, api_client, tracked_proposal):
        """View mode updates from 'unknown' to a known value on second track call."""
        p = tracked_proposal
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': p.uuid})
        api_client.post(url, {
            'session_id': 'sess-1',
            'sections': [{'section_type': 'greeting', 'time_spent_seconds': 5}],
            'view_mode': 'unknown',
        }, format='json')

        event = ProposalViewEvent.objects.get(proposal=p, session_id='sess-1')
        assert event.view_mode == 'unknown'

        api_client.post(url, {
            'session_id': 'sess-1',
            'sections': [{'section_type': 'greeting', 'time_spent_seconds': 10}],
            'view_mode': 'executive',
        }, format='json')

        event.refresh_from_db()
        assert event.view_mode == 'executive'

    def test_engagement_declining_reset_on_normal_engagement(
        self, api_client, tracked_proposal,
    ):
        """Engagement declining flag resets when current engagement is normal."""
        p = tracked_proposal
        p.engagement_declining = True
        p.save(update_fields=['engagement_declining'])

        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': p.uuid})

        prev_event = ProposalViewEvent.objects.create(
            proposal=p, session_id='prev-sess',
            viewed_at=FROZEN_NOW - timedelta(hours=5),
        )
        ProposalSectionView.objects.create(
            view_event=prev_event, section_type='greeting',
            section_title='Greeting', time_spent_seconds=10,
            entered_at=FROZEN_NOW - timedelta(hours=5),
        )

        api_client.post(url, {
            'session_id': 'new-sess',
            'sections': [
                {'section_type': 'greeting', 'time_spent_seconds': 15},
                {'section_type': 'investment', 'time_spent_seconds': 20},
            ],
        }, format='json')

        p.refresh_from_db()
        assert p.engagement_declining is False

    def test_cached_heat_score_exception_handled(
        self, api_client, tracked_proposal,
    ):
        """Track endpoint handles _compute_heat_score_for_proposal exception."""
        p = tracked_proposal
        url = reverse('track-proposal-engagement', kwargs={'proposal_uuid': p.uuid})

        with patch(
            'content.views.proposal._compute_heat_score_for_proposal',
            side_effect=Exception('DB error'),
        ):
            response = api_client.post(url, {
                'session_id': 'exc-sess',
                'sections': [{'section_type': 'greeting', 'time_spent_seconds': 5}],
            }, format='json')

        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — heat score branches
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestHeatScoreBranches:
    def test_investment_time_60s_adds_2_points(self, db):
        """Investment section time >= 60s adds 2 points to heat score."""
        from content.views.proposal import _compute_heat_score_with_summary

        p = BusinessProposal.objects.create(
            title='Heat Test', client_name='Client',
            client_email='heat@test.com', status='viewed',
            total_investment=Decimal('5000.00'),
            view_count=1, first_viewed_at=FROZEN_NOW - timedelta(days=1),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        event = ProposalViewEvent.objects.create(
            proposal=p, session_id='heat-sess',
            viewed_at=FROZEN_NOW - timedelta(hours=1), ip_address='1.2.3.4',
        )
        ProposalSectionView.objects.create(
            view_event=event, section_type='investment',
            section_title='Investment', time_spent_seconds=65,
            entered_at=FROZEN_NOW - timedelta(hours=1),
        )

        result = _compute_heat_score_with_summary(p.id, FROZEN_NOW)
        assert result['score'] >= 2

    def test_view_count_5_adds_2_points(self, db):
        """View count >= 5 adds 2 points to heat score."""
        from content.views.proposal import _compute_heat_score_with_summary

        p = BusinessProposal.objects.create(
            title='Views Test', client_name='Client',
            client_email='views@test.com', status='viewed',
            total_investment=Decimal('5000.00'),
            view_count=5, first_viewed_at=FROZEN_NOW - timedelta(days=1),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )

        result = _compute_heat_score_with_summary(p.id, FROZEN_NOW)
        assert result['score'] >= 2


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — view mode analytics in dashboard
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestDashboardViewModeAnalytics:
    def test_dashboard_includes_view_mode_win_rate(self, admin_client, db):
        """Dashboard returns win_rate_by_view_mode when proposals have events."""
        p = BusinessProposal.objects.create(
            title='Accepted VP', client_name='Client',
            client_email='vp@test.com', status='accepted',
            total_investment=Decimal('5000.00'),
            sent_at=FROZEN_NOW - timedelta(days=10),
            first_viewed_at=FROZEN_NOW - timedelta(days=8),
            responded_at=FROZEN_NOW - timedelta(days=1),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        ProposalViewEvent.objects.create(
            proposal=p, session_id='vp-sess', view_mode='executive',
            viewed_at=FROZEN_NOW - timedelta(days=5),
        )

        url = reverse('proposal-dashboard')
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'win_rate_by_view_mode' in response.data


# ═══════════════════════════════════════════════════════════════════
# content/views/proposal.py — module merging in create-from-json
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestCreateProposalFromJSONModuleMerging:
    @pytest.fixture
    def patched_defaults_and_payload(self, db):
        """Build patched defaults with additionalModules and JSON payload."""
        from content.services.proposal_service import ProposalService

        real_defaults = ProposalService.get_default_sections('es')
        fr_default = next(
            (s for s in real_defaults
             if s['section_type'] == 'functional_requirements'), None,
        )
        if not fr_default:
            pytest.skip('No functional_requirements in defaults')

        patched_defaults = copy.deepcopy(real_defaults)
        for section in patched_defaults:
            if section['section_type'] == 'functional_requirements':
                section['content_json']['additionalModules'] = [
                    {'id': 'pwa_module', 'title': 'PWA Default', 'is_visible': True},
                    {'id': 'dark_mode_module', 'title': 'Dark Mode', 'is_visible': False},
                ]
                break

        payload = {
            'title': 'Merge Test', 'client_name': 'Merger',
            'client_email': 'merge@test.com',
            'total_investment': 5000, 'currency': 'COP', 'language': 'es',
            'sections': {
                'general': {'clientName': 'Merger', 'proposalTitle': 'Merge Test'},
                'functionalRequirements': {
                    'groups': fr_default['content_json'].get('groups', []),
                    'additionalModules': [
                        {'id': 'pwa_module', 'title': 'PWA Overridden'},
                        {'id': 'brand_new_module', 'title': 'Brand New'},
                    ],
                },
            },
        }
        return patched_defaults, payload

    def test_additional_modules_merged_with_defaults(
        self, admin_client, patched_defaults_and_payload,
    ):
        """Create-from-JSON merges additionalModules from JSON with defaults."""
        patched_defaults, payload = patched_defaults_and_payload

        url = reverse('create-proposal-from-json')
        with patch(
            'content.services.proposal_service.ProposalService.get_default_sections',
            return_value=patched_defaults,
        ):
            response = admin_client.post(url, payload, format='json')

        assert response.status_code == 201
        proposal = BusinessProposal.objects.get(title='Merge Test')
        fr_section = ProposalSection.objects.filter(
            proposal=proposal, section_type='functional_requirements',
        ).first()
        assert fr_section is not None
        modules = fr_section.content_json.get('additionalModules', [])
        module_ids = [m.get('id') for m in modules]
        assert set(module_ids) >= {'pwa_module', 'dark_mode_module', 'brand_new_module'}
        pwa = next(m for m in modules if m['id'] == 'pwa_module')
        assert pwa['title'] == 'PWA Overridden'


# ═══════════════════════════════════════════════════════════════════
# content/services/proposal_email_service.py — cooldown + magic link
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestProposalEmailServiceCooldown:
    @pytest.fixture
    def cooldown_proposal(self, db):
        """A proposal with recent automated email (cooldown active)."""
        return BusinessProposal.objects.create(
            title='Cooldown Test', client_name='Client',
            client_email='cooldown@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            sent_at=FROZEN_NOW - timedelta(days=5),
            first_viewed_at=FROZEN_NOW - timedelta(days=3),
            last_activity_at=FROZEN_NOW - timedelta(hours=2),
            expires_at=FROZEN_NOW + timedelta(days=10),
            last_automated_email_at=FROZEN_NOW - timedelta(hours=1),
        )

    def test_send_reminder_blocked_by_cooldown(self, cooldown_proposal):
        """send_reminder returns False when cooldown is active."""
        from content.services.proposal_email_service import ProposalEmailService

        result = ProposalEmailService.send_reminder(cooldown_proposal)
        assert result is False

    def test_send_urgency_email_blocked_by_cooldown(self, cooldown_proposal):
        """send_urgency_email returns False when cooldown is active."""
        from content.services.proposal_email_service import ProposalEmailService

        result = ProposalEmailService.send_urgency_email(cooldown_proposal)
        assert result is False

    def test_send_abandonment_followup_blocked_by_cooldown(self, cooldown_proposal):
        """send_abandonment_followup returns False when cooldown is active."""
        from content.services.proposal_email_service import ProposalEmailService

        result = ProposalEmailService.send_abandonment_followup(cooldown_proposal)
        assert result is False

    def test_send_investment_followup_blocked_by_cooldown(self, cooldown_proposal):
        """send_investment_interest_followup returns False when cooldown is active."""
        from content.services.proposal_email_service import ProposalEmailService

        result = ProposalEmailService.send_investment_interest_followup(
            cooldown_proposal, 120.0,
        )
        assert result is False


@freeze_time('2026-01-15T10:00:00Z')
class TestSendMagicLinkEmail:
    def test_send_magic_link_email_success(self, db):
        """send_magic_link_email sends email and logs it."""
        from content.services.proposal_email_service import ProposalEmailService

        p = BusinessProposal.objects.create(
            title='Magic Test', client_name='Link Client',
            client_email='magic@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            sent_at=FROZEN_NOW - timedelta(days=3),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )

        with patch(
            'content.services.proposal_email_service.EmailMultiAlternatives',
        ) as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            result = ProposalEmailService.send_magic_link_email('magic@test.com', [p])

        assert result is True
        mock_instance.attach_alternative.assert_called_once()
        mock_instance.send.assert_called_once()
        assert EmailLog.objects.filter(
            template_key='magic_link', recipient='magic@test.com',
        ).exists()

    def test_send_magic_link_email_returns_false_for_empty_list(self, db):
        """send_magic_link_email returns False for empty proposals list."""
        from content.services.proposal_email_service import ProposalEmailService

        result = ProposalEmailService.send_magic_link_email('test@test.com', [])
        assert result is False

    def test_send_magic_link_email_handles_send_failure(self, db):
        """send_magic_link_email returns False and logs failure on exception."""
        from content.services.proposal_email_service import ProposalEmailService

        p = BusinessProposal.objects.create(
            title='Fail Magic', client_name='Fail Client',
            client_email='fail@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            sent_at=FROZEN_NOW - timedelta(days=3),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )

        with patch(
            'content.services.proposal_email_service.EmailMultiAlternatives',
        ) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.send.side_effect = Exception('SMTP error')
            mock_cls.return_value = mock_instance
            result = ProposalEmailService.send_magic_link_email('fail@test.com', [p])

        assert result is False
        mock_instance.send.assert_called_once()
        assert EmailLog.objects.filter(
            template_key='magic_link', status='failed',
        ).exists()


# ═══════════════════════════════════════════════════════════════════
# content/tasks.py — escalation skip + refresh_cached_heat_scores
# ═══════════════════════════════════════════════════════════════════

@freeze_time('2026-01-15T10:00:00Z')
class TestEscalationAndHeatRefresh:
    def test_escalation_skips_recent_activity(self, db):
        """Escalation task skips proposals with recent last_activity_at."""
        from content.tasks import escalate_seller_inactivity

        p = BusinessProposal.objects.create(
            title='Recent Activity', client_name='Active',
            client_email='active@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            sent_at=FROZEN_NOW - timedelta(days=10),
            first_viewed_at=FROZEN_NOW - timedelta(days=8),
            last_activity_at=FROZEN_NOW - timedelta(days=1),
            expires_at=FROZEN_NOW + timedelta(days=10),
            automations_paused=False,
        )

        escalate_seller_inactivity()

        assert not ProposalChangeLog.objects.filter(
            proposal=p, change_type='escalation_email',
        ).exists()

    def test_refresh_cached_heat_scores(self, db):
        """refresh_cached_heat_scores updates changed scores."""
        from content.tasks import refresh_cached_heat_scores

        p = BusinessProposal.objects.create(
            title='Heat Refresh', client_name='Refresh',
            client_email='refresh@test.com',
            total_investment=Decimal('5000.00'),
            status='viewed',
            cached_heat_score=0,
            sent_at=FROZEN_NOW - timedelta(days=5),
            first_viewed_at=FROZEN_NOW - timedelta(days=3),
            last_activity_at=FROZEN_NOW - timedelta(hours=1),
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        ProposalViewEvent.objects.create(
            proposal=p, session_id='refresh-sess',
            viewed_at=FROZEN_NOW - timedelta(hours=1),
            ip_address='10.0.0.1',
        )

        refresh_cached_heat_scores()

        p.refresh_from_db()
        assert p.cached_heat_score > 0


# ═══════════════════════════════════════════════════════════════════
# content/serializers/proposal.py — validation branches
# ═══════════════════════════════════════════════════════════════════

class TestProposalSerializerValidation:
    def test_validate_language_rejects_invalid_directly(self):
        """validate_language raises ValidationError for invalid language."""
        from content.serializers.proposal import ProposalDefaultConfigSerializer

        serializer = ProposalDefaultConfigSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_language('fr')
        assert 'must be' in str(exc_info.value.detail)

    def test_validate_language_accepts_valid(self):
        """validate_language passes for 'es' and 'en'."""
        from content.serializers.proposal import ProposalDefaultConfigSerializer

        serializer = ProposalDefaultConfigSerializer()
        assert serializer.validate_language('es') == 'es'
        assert serializer.validate_language('en') == 'en'

    def test_sections_json_rejects_non_dict_entry(self):
        """ProposalDefaultConfigSerializer rejects non-dict section entry."""
        from content.serializers.proposal import ProposalDefaultConfigSerializer

        serializer = ProposalDefaultConfigSerializer(data={
            'language': 'es',
            'sections_json': ['not_a_dict'],
        })
        assert not serializer.is_valid()
        assert 'sections_json' in serializer.errors

    def test_validate_content_overrides_accepts_dict(self):
        """validate_content_overrides returns value for valid dict."""
        from content.serializers.proposal import EmailTemplateConfigSerializer

        serializer = EmailTemplateConfigSerializer()
        result = serializer.validate_content_overrides({'subject': 'Test'})
        assert result == {'subject': 'Test'}

    def test_validate_content_overrides_rejects_non_dict(self):
        """validate_content_overrides raises ValidationError for non-dict."""
        from content.serializers.proposal import EmailTemplateConfigSerializer

        serializer = EmailTemplateConfigSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_content_overrides('not_a_dict')
        assert 'must be a JSON object' in str(exc_info.value.detail)


# ═══════════════════════════════════════════════════════════════════
# content/views/email_templates.py — template entry None, render exception
# ═══════════════════════════════════════════════════════════════════

class TestEmailTemplateViewsEdgeCases:
    def test_list_skips_unknown_template_key(self, admin_client, db):
        """Template list skips entries where get_template_entry returns None."""
        from content.services.email_template_registry import get_all_keys

        real_keys = get_all_keys()
        fake_keys = real_keys + ['nonexistent_fake_template']

        url = reverse('email-template-list')
        with patch(
            'content.views.email_templates.get_all_keys',
            return_value=fake_keys,
        ):
            response = admin_client.get(url)

        assert response.status_code == 200
        keys = [e['template_key'] for e in response.data]
        assert 'nonexistent_fake_template' not in keys

    def test_preview_handles_render_exception(self, admin_client, db):
        """Preview returns 500 when template rendering fails."""
        from content.services.email_template_registry import (
            get_all_keys,
            get_template_entry,
        )

        target_key = None
        for k in get_all_keys():
            entry = get_template_entry(k)
            if entry and entry.get('html_template'):
                target_key = k
                break

        if not target_key:
            pytest.skip('No template with html_template found')

        url = reverse('email-template-preview', kwargs={'template_key': target_key})
        with patch(
            'content.views.email_templates.render_to_string',
            side_effect=Exception('Template render failed'),
        ):
            response = admin_client.get(url)

        assert response.status_code == 500
        assert 'Failed to render' in response.data['detail']


# ═══════════════════════════════════════════════════════════════════
# content/serializers/blog.py — source not-dict validation
# ═══════════════════════════════════════════════════════════════════

class TestBlogSerializerSourceValidation:
    def test_validate_sources_rejects_non_dict_entry(self):
        """Blog serializer validate_sources raises for non-dict source entry."""
        from content.serializers.blog import BlogPostFromJSONSerializer

        serializer = BlogPostFromJSONSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_sources(['not_a_dict'])
        assert 'JSON object' in str(exc_info.value.detail)
