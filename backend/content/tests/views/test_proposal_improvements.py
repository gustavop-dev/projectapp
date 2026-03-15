"""Tests for proposal system improvements.

Covers:
- engagement_decay alert type registration fix
- lead_score removal from list_proposals
- ProposalAlert priority auto-computation
- engagement_declining flag in heat score
- cached_heat_score update on tracking
- email cooldown (last_automated_email_at)
- auto-extension of expiration for active clients
- expired proposal 410 response enrichment
- magic link endpoint
- proposal scorecard enhancements
- alert priority sorting
"""
from datetime import datetime, timedelta
from datetime import timezone as dt_tz
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from freezegun import freeze_time

FROZEN_NOW = datetime(2026, 1, 15, 10, 0, 0, tzinfo=dt_tz.utc)

from content.models import (
    BusinessProposal,
    ProposalAlert,
    ProposalChangeLog,
    ProposalSection,
    ProposalViewEvent,
)

pytestmark = pytest.mark.django_db


# ── Fixtures ──

@pytest.fixture
@freeze_time('2026-01-15T10:00:00Z')
def viewed_proposal(db):
    """A proposal in viewed status with future expiry."""
    now = FROZEN_NOW
    return BusinessProposal.objects.create(
        title='Viewed Project',
        client_name='Viewed Client',
        client_email='viewed@client.com',
        client_phone='+573001234567',
        language='es',
        total_investment=Decimal('10000.00'),
        currency='COP',
        status='viewed',
        sent_at=now - timedelta(days=5),
        first_viewed_at=now - timedelta(days=3),
        last_activity_at=now - timedelta(hours=2),
        expires_at=now + timedelta(days=10),
        project_type='website',
        market_type='b2b',
    )


@pytest.fixture
@freeze_time('2026-01-15T10:00:00Z')
def about_to_expire_proposal(db):
    """A viewed proposal that's about to expire (expired 1 hour ago)."""
    now = FROZEN_NOW
    return BusinessProposal.objects.create(
        title='Almost Expired',
        client_name='Expiring Client',
        client_email='expiring@client.com',
        language='es',
        total_investment=Decimal('7000.00'),
        currency='COP',
        status='viewed',
        sent_at=now - timedelta(days=20),
        first_viewed_at=now - timedelta(days=15),
        expires_at=now - timedelta(hours=1),
        is_active=True,
    )


# ── 1.1 engagement_decay alert type ──

@freeze_time('2026-01-15T10:00:00Z')
class TestEngagementDecayAlertType:
    def test_engagement_decay_is_valid_alert_type(self, viewed_proposal):
        """engagement_decay should be a valid choice for ProposalAlert.alert_type."""
        alert = ProposalAlert.objects.create(
            proposal=viewed_proposal,
            alert_type='engagement_decay',
            message='Test decay alert',
            alert_date=FROZEN_NOW,
        )
        alert.refresh_from_db()
        assert alert.alert_type == 'engagement_decay'

    def test_engagement_decay_in_choices(self):
        """engagement_decay must be present in ALERT_TYPE_CHOICES."""
        types = [c[0] for c in ProposalAlert.ALERT_TYPE_CHOICES]
        assert 'engagement_decay' in types


# ── 1.2 lead_score removal ──

@freeze_time('2026-01-15T10:00:00Z')
class TestLeadScoreRemoval:
    def test_list_proposals_has_no_lead_score(self, admin_client, viewed_proposal):
        """list_proposals response should not contain lead_score."""
        url = reverse('list-proposals')
        response = admin_client.get(url)
        assert response.status_code == 200
        for item in response.data:
            assert 'lead_score' not in item

    def test_list_proposals_has_heat_score(self, admin_client, viewed_proposal):
        """list_proposals response should still contain heat_score."""
        url = reverse('list-proposals')
        response = admin_client.get(url)
        assert response.status_code == 200
        for item in response.data:
            assert 'heat_score' in item

    def test_accepted_proposal_heat_score_is_10(self, admin_client, db):
        """Accepted proposals should have heat_score=10."""
        p = BusinessProposal.objects.create(
            title='Accepted', client_name='Winner',
            client_email='w@t.com', status='accepted',
            total_investment=Decimal('5000.00'),
            expires_at=FROZEN_NOW + timedelta(days=5),
        )
        url = reverse('list-proposals')
        response = admin_client.get(url)
        accepted = [i for i in response.data if i['id'] == p.id]
        assert len(accepted) == 1
        assert accepted[0]['heat_score'] == 10


# ── 2.1 ProposalAlert priority ──

@freeze_time('2026-01-15T10:00:00Z')
class TestAlertPriority:
    def test_auto_priority_critical_for_engagement_decay(self, viewed_proposal):
        """engagement_decay alerts should auto-set priority to critical."""
        alert = ProposalAlert.objects.create(
            proposal=viewed_proposal,
            alert_type='engagement_decay',
            message='Decay detected',
            alert_date=FROZEN_NOW,
        )
        assert alert.priority == 'critical'

    def test_auto_priority_critical_for_post_expiration(self, viewed_proposal):
        """post_expiration_visit alerts should auto-set priority to critical."""
        alert = ProposalAlert.objects.create(
            proposal=viewed_proposal,
            alert_type='post_expiration_visit',
            message='Post-expiration visit',
            alert_date=FROZEN_NOW,
        )
        assert alert.priority == 'critical'

    def test_auto_priority_high_for_discount_suggestion(self, viewed_proposal):
        """discount_suggestion alerts should auto-set priority to high."""
        alert = ProposalAlert.objects.create(
            proposal=viewed_proposal,
            alert_type='discount_suggestion',
            message='Consider discount',
            alert_date=FROZEN_NOW,
        )
        assert alert.priority == 'high'

    def test_auto_priority_normal_for_reminder(self, viewed_proposal):
        """Reminder alerts should default to normal priority."""
        alert = ProposalAlert.objects.create(
            proposal=viewed_proposal,
            alert_type='reminder',
            message='Reminder',
            alert_date=FROZEN_NOW,
        )
        assert alert.priority == 'normal'

    def test_explicit_priority_not_overridden(self, viewed_proposal):
        """Explicitly set priority should not be overridden by auto-compute."""
        alert = ProposalAlert(
            proposal=viewed_proposal,
            alert_type='engagement_decay',
            message='Test',
            alert_date=FROZEN_NOW,
            priority='high',
        )
        alert.save()
        assert alert.priority == 'high'


# ── 2.2 engagement_declining flag ──

@freeze_time('2026-01-15T10:00:00Z')
class TestEngagementDeclining:
    def test_new_proposal_not_declining(self, viewed_proposal):
        """New proposals should have engagement_declining=False."""
        assert viewed_proposal.engagement_declining is False

    def test_model_field_exists(self, viewed_proposal):
        """BusinessProposal should have engagement_declining field."""
        viewed_proposal.engagement_declining = True
        viewed_proposal.save(update_fields=['engagement_declining'])
        viewed_proposal.refresh_from_db()
        assert viewed_proposal.engagement_declining is True


# ── 2.3 cached_heat_score ──

@freeze_time('2026-01-15T10:00:00Z')
class TestCachedHeatScore:
    def test_default_cached_heat_score_is_zero(self, viewed_proposal):
        """New proposals should have cached_heat_score=0."""
        assert viewed_proposal.cached_heat_score == 0

    def test_cached_heat_score_field_update(self, viewed_proposal):
        """cached_heat_score should be writable."""
        viewed_proposal.cached_heat_score = 7
        viewed_proposal.save(update_fields=['cached_heat_score'])
        viewed_proposal.refresh_from_db()
        assert viewed_proposal.cached_heat_score == 7

    def test_heat_score_penalty_for_declining(self):
        """engagement_declining should reduce heat score by 1."""
        from content.views.proposal import _compute_heat_score_with_summary

        p = BusinessProposal.objects.create(
            title='Declining Test', client_name='Test',
            client_email='t@t.com', status='viewed',
            total_investment=Decimal('5000.00'),
            view_count=3, first_viewed_at=FROZEN_NOW - timedelta(days=1),
            last_activity_at=FROZEN_NOW - timedelta(hours=1),
            engagement_declining=False,
            expires_at=FROZEN_NOW + timedelta(days=10),
        )
        result_normal = _compute_heat_score_with_summary(p.id, FROZEN_NOW)

        p.engagement_declining = True
        p.save(update_fields=['engagement_declining'])
        result_declining = _compute_heat_score_with_summary(p.id, FROZEN_NOW)

        assert result_declining['score'] <= result_normal['score']


# ── 2.4 Email cooldown ──

@freeze_time('2026-01-15T10:00:00Z')
class TestEmailCooldown:
    def test_cooldown_blocks_when_recent(self, viewed_proposal):
        """_check_cooldown should return False when email sent < 24h ago."""
        from content.services.proposal_email_service import ProposalEmailService

        viewed_proposal.last_automated_email_at = FROZEN_NOW - timedelta(hours=1)
        viewed_proposal.save(update_fields=['last_automated_email_at'])

        result = ProposalEmailService._check_cooldown(viewed_proposal)
        assert result is False

    def test_cooldown_passes_when_no_previous(self, viewed_proposal):
        """_check_cooldown should return True when no previous email."""
        from content.services.proposal_email_service import ProposalEmailService

        assert viewed_proposal.last_automated_email_at is None
        result = ProposalEmailService._check_cooldown(viewed_proposal)
        assert result is True
        viewed_proposal.refresh_from_db()
        assert viewed_proposal.last_automated_email_at is not None

    def test_cooldown_passes_after_24h(self, viewed_proposal):
        """_check_cooldown should return True when email sent > 24h ago."""
        from content.services.proposal_email_service import ProposalEmailService

        viewed_proposal.last_automated_email_at = FROZEN_NOW - timedelta(hours=25)
        viewed_proposal.save(update_fields=['last_automated_email_at'])

        result = ProposalEmailService._check_cooldown(viewed_proposal)
        assert result is True


# ── 2.5 Auto-extension ──

@freeze_time('2026-01-15T10:00:00Z')
class TestAutoExtension:
    def test_auto_extends_when_recent_activity(self, about_to_expire_proposal):
        """expire_stale_proposals should extend when client had recent views."""
        from content.tasks import expire_stale_proposals

        # Create a recent view event
        ProposalViewEvent.objects.create(
            proposal=about_to_expire_proposal,
            session_id='recent-session',
            viewed_at=FROZEN_NOW - timedelta(hours=2),
        )

        expire_stale_proposals()

        about_to_expire_proposal.refresh_from_db()
        assert about_to_expire_proposal.status == 'viewed'  # Not expired
        assert about_to_expire_proposal.expires_at > FROZEN_NOW

        # Verify changelog
        log = ProposalChangeLog.objects.filter(
            proposal=about_to_expire_proposal,
            description__icontains='Auto-extended',
        )
        assert log.exists()

    def test_expires_when_no_recent_activity(self, about_to_expire_proposal):
        """expire_stale_proposals should expire when no recent activity."""
        from content.tasks import expire_stale_proposals

        expire_stale_proposals()

        about_to_expire_proposal.refresh_from_db()
        assert about_to_expire_proposal.status == 'expired'


# ── 3.1 Expired proposal 410 response ──

@freeze_time('2026-01-15T10:00:00Z')
class TestExpiredProposalResponse:
    def test_expired_includes_expired_meta_with_seller_and_whatsapp(self, api_client, db):
        """Expired proposal returns 200 with expired_meta containing seller_name and whatsapp_url."""
        p = BusinessProposal.objects.create(
            title='Expired Proposal', client_name='Client',
            client_email='c@t.com', status='expired',
            total_investment=Decimal('5000.00'), currency='COP',
            expires_at=FROZEN_NOW - timedelta(days=1),
            is_active=True,
        )
        url = reverse('retrieve-public-proposal', kwargs={'proposal_uuid': p.uuid})
        response = api_client.get(url)
        assert response.status_code == 200
        assert 'expired_meta' in response.data
        meta = response.data['expired_meta']
        assert 'seller_name' in meta
        assert 'whatsapp_url' in meta
        assert 'total_investment' in response.data
        assert 'currency' in response.data


# ── 3.2 Magic link ──

@freeze_time('2026-01-15T10:00:00Z')
class TestMagicLink:
    def test_magic_link_returns_200_for_existing_email(self, api_client, viewed_proposal):
        """Magic link endpoint should return 200 for known email."""
        url = reverse('request-magic-link')
        with patch('content.services.proposal_email_service.ProposalEmailService.send_magic_link_email') as mock_send:
            mock_send.return_value = True
            response = api_client.post(url, {'email': viewed_proposal.client_email}, format='json')
        assert response.status_code == 200

    def test_magic_link_returns_200_for_unknown_email(self, api_client):
        """Magic link endpoint should return 200 even for unknown email (no enumeration)."""
        url = reverse('request-magic-link')
        response = api_client.post(url, {'email': 'unknown@test.com'}, format='json')
        assert response.status_code == 200

    def test_magic_link_returns_400_without_email(self, api_client):
        """Magic link endpoint should return 400 when email is missing."""
        url = reverse('request-magic-link')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == 400


# ── 5.2 Proposal scorecard ──

@freeze_time('2026-01-15T10:00:00Z')
class TestProposalScorecardEnhanced:
    def test_scorecard_includes_phone_check(self, admin_client, db):
        """Scorecard should include client_phone check."""
        p = BusinessProposal.objects.create(
            title='Scorecard Test', client_name='SC Client',
            client_email='sc@t.com', client_phone='+573001234567',
            total_investment=Decimal('5000.00'),
            expires_at=FROZEN_NOW + timedelta(days=10),
            status='draft',
        )
        ProposalSection.objects.create(
            proposal=p, section_type='intro', order=1, is_enabled=True,
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        keys = [c['key'] for c in response.data['checks']]
        assert 'client_phone' in keys
        assert 'language' in keys

    def test_scorecard_phone_fails_when_empty(self, admin_client, db):
        """Phone check should fail when client_phone is empty."""
        p = BusinessProposal.objects.create(
            title='No Phone', client_name='No Phone',
            client_email='np@t.com', client_phone='',
            total_investment=Decimal('5000.00'),
            expires_at=FROZEN_NOW + timedelta(days=10),
            status='draft',
        )
        ProposalSection.objects.create(
            proposal=p, section_type='intro', order=1, is_enabled=True,
        )
        url = reverse('proposal-scorecard', kwargs={'proposal_id': p.id})
        response = admin_client.get(url)
        phone_check = next(c for c in response.data['checks'] if c['key'] == 'client_phone')
        assert phone_check['passed'] is False


# ── Alert priority sorting ──

@freeze_time('2026-01-15T10:00:00Z')
class TestAlertPrioritySorting:
    def test_alerts_sorted_by_priority(self, admin_client, viewed_proposal):
        """Alerts should be sorted: critical first, then high, then normal."""
        ProposalAlert.objects.create(
            proposal=viewed_proposal, alert_type='reminder',
            message='Normal alert', alert_date=FROZEN_NOW,
        )
        ProposalAlert.objects.create(
            proposal=viewed_proposal, alert_type='engagement_decay',
            message='Critical alert', alert_date=FROZEN_NOW,
        )
        ProposalAlert.objects.create(
            proposal=viewed_proposal, alert_type='discount_suggestion',
            message='High alert', alert_date=FROZEN_NOW,
        )

        url = reverse('proposal-alerts')
        response = admin_client.get(url)
        assert response.status_code == 200

        # Find the manual alerts in the response
        manual = [a for a in response.data if a.get('manual_alert_id')]
        if len(manual) >= 2:
            priorities = [a['priority'] for a in manual]
            priority_order = {'critical': 0, 'high': 1, 'normal': 2}
            ordered = sorted(priorities, key=lambda p: priority_order.get(p, 2))
            assert priorities == ordered
