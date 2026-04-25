"""Tests for the BusinessProposal model.

Covers: UUID generation, slug, status choices, is_expired property,
days_remaining property, public_url property, and __str__.
"""
import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalAlert,
    ProposalChangeLog,
    ProposalSectionView,
    ProposalShareLink,
    ProposalViewEvent,
)
from accounts.models import UserProfile

pytestmark = pytest.mark.django_db


class TestBusinessProposalCreation:
    def test_str_returns_title_and_client_name(self, proposal):
        assert str(proposal) == 'Web Application Development — Acme Corp'
        assert proposal.title in str(proposal)

    def test_uuid_auto_generated(self, proposal):
        assert proposal.uuid is not None
        assert len(str(proposal.uuid)) == 36

    def test_uuid_is_unique(self, proposal, sent_proposal):
        assert proposal.uuid != sent_proposal.uuid
        assert proposal.uuid is not None

    def test_slug_auto_generated_from_client_name(self, proposal):
        assert proposal.slug == 'acme-corp'
        assert proposal.slug != ''

    def test_slug_preserved_on_update(self, proposal):
        original_slug = proposal.slug
        proposal.client_name = 'New Client Name'
        proposal.save()
        assert proposal.slug == original_slug

    def test_default_status_is_draft(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Test Client',
        )
        assert prop.status == 'draft'

    def test_default_currency_is_cop(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Test Client',
        )
        assert prop.currency == 'COP'

    def test_default_language_is_es(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Test Client',
        )
        assert prop.language == 'es'

    def test_slug_uses_linked_client_full_name_when_client_name_empty(self, db):
        user = get_user_model().objects.create_user(
            username='proposal-client-fullname',
            email='client.full@example.com',
            first_name='Maria',
            last_name='Lopez',
        )
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        proposal = BusinessProposal.objects.create(
            title='Test',
            client_name='',
            client=profile,
        )

        assert proposal.slug == 'maria-lopez'

    def test_slug_uses_linked_client_email_when_full_name_missing(self, db):
        user = get_user_model().objects.create_user(
            username='proposal-client-email',
            email='fallback.slug@example.com',
        )
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        proposal = BusinessProposal.objects.create(
            title='Test',
            client_name='',
            client=profile,
        )

        assert proposal.slug == 'fallbackslugexamplecom'


class TestBusinessProposalExpiration:
    def test_is_expired_returns_true_for_expired_status(self, expired_proposal):
        assert expired_proposal.is_expired is True
        assert expired_proposal.status == 'expired'

    @freeze_time('2026-03-15 12:00:00')
    def test_is_expired_returns_true_when_past_expiry_date(self):
        prop = BusinessProposal.objects.create(
            title='Past Due',
            client_name='Client',
            expires_at=datetime.datetime(2026, 3, 10, tzinfo=datetime.timezone.utc),
        )
        assert prop.is_expired is True

    @freeze_time('2026-03-01 12:00:00')
    def test_is_expired_returns_false_when_before_expiry(self):
        prop = BusinessProposal.objects.create(
            title='Not Due',
            client_name='Client',
            expires_at=datetime.datetime(2026, 3, 15, tzinfo=datetime.timezone.utc),
        )
        assert prop.is_expired is False

    def test_is_expired_returns_false_for_draft_without_expiry(self):
        prop = BusinessProposal.objects.create(
            title='No Expiry',
            client_name='Client',
        )
        assert prop.is_expired is False


class TestBusinessProposalDaysRemaining:
    @freeze_time('2026-03-01 12:00:00')
    def test_days_remaining_returns_correct_count(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            expires_at=datetime.datetime(2026, 3, 11, 12, 0, tzinfo=datetime.timezone.utc),
        )
        assert prop.days_remaining == 10

    def test_days_remaining_returns_none_without_expiry(self):
        prop = BusinessProposal.objects.create(
            title='No Expiry',
            client_name='Client',
        )
        assert prop.days_remaining is None

    @freeze_time('2026-03-15 12:00:00')
    def test_days_remaining_returns_zero_when_past(self):
        prop = BusinessProposal.objects.create(
            title='Past',
            client_name='Client',
            expires_at=datetime.datetime(2026, 3, 10, tzinfo=datetime.timezone.utc),
        )
        assert prop.days_remaining == 0


class TestBusinessProposalPublicUrl:
    def test_public_url_uses_slug_not_uuid(self, proposal):
        assert '/proposal/' in proposal.public_url
        assert proposal.slug != ''
        assert proposal.slug in proposal.public_url
        # UUID must no longer appear in the public URL once a slug is in place.
        assert str(proposal.uuid) not in proposal.public_url

    def test_public_url_starts_with_base(self, proposal):
        assert '/proposal/' in proposal.public_url


class TestBusinessProposalSlug:
    def test_slug_auto_generated_from_client_name(self, db):
        prop = BusinessProposal.objects.create(
            title='Alpha proposal',
            client_name='María López',
        )
        assert prop.slug == 'maria-lopez'

    def test_slug_collision_auto_suffixes(self, db):
        a = BusinessProposal.objects.create(title='A', client_name='María López')
        b = BusinessProposal.objects.create(title='B', client_name='María López')
        c = BusinessProposal.objects.create(title='C', client_name='María López')
        assert a.slug == 'maria-lopez'
        assert b.slug == 'maria-lopez-2'
        assert c.slug == 'maria-lopez-3'

    def test_user_supplied_slug_is_kept(self, db):
        prop = BusinessProposal.objects.create(
            title='Custom',
            client_name='María López',
            slug='hola-maria',
        )
        assert prop.slug == 'hola-maria'
        assert '/proposal/hola-maria' in prop.public_url


class TestBusinessProposalStatusChoices:
    @pytest.mark.parametrize('status', [
        'draft', 'sent', 'viewed', 'accepted', 'rejected', 'negotiating',
        'expired', 'finished',
    ])
    def test_valid_status_choices(self, status):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            status=status,
        )
        assert prop.status == status

    def test_accepted_can_transition_to_finished(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            status='accepted',
        )
        assert 'finished' in prop.available_transitions

    def test_finished_is_terminal(self):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            status='finished',
        )
        assert prop.available_transitions == []


class TestProposalChangeLogStr:
    def test_str_contains_client_and_change_type(self, proposal):
        log = ProposalChangeLog.objects.create(
            proposal=proposal, change_type='status_changed',
            field_name='status', old_value='draft', new_value='sent',
        )
        result = str(log)
        assert proposal.client_name in result
        assert 'status_changed' in result


class TestProposalSectionViewStr:
    @freeze_time('2026-03-01 12:00:00')
    def test_str_contains_client_and_section_type(self, proposal):
        event = ProposalViewEvent.objects.create(
            proposal=proposal, session_id='str-test',
        )
        sv = ProposalSectionView.objects.create(
            view_event=event, section_type='greeting',
            section_title='Saludo', time_spent_seconds=5.0,
            entered_at=timezone.now(),
        )
        result = str(sv)
        assert proposal.client_name in result
        assert 'greeting' in result


class TestProposalViewEventStr:
    def test_str_contains_client_and_session_id(self, proposal):
        event = ProposalViewEvent.objects.create(
            proposal=proposal, session_id='abcdefgh-1234',
        )
        result = str(event)
        assert proposal.client_name in result
        assert 'abcdefgh' in result


class TestProposalShareLinkStr:
    def test_str_contains_client_and_recipient(self, proposal):
        link = ProposalShareLink.objects.create(
            proposal=proposal, shared_by_name='Alice',
            recipient_name='Bob',
        )
        result = str(link)
        assert proposal.client_name in result
        assert 'Bob' in result

    def test_str_shows_pending_when_no_recipient(self, proposal):
        link = ProposalShareLink.objects.create(
            proposal=proposal, shared_by_name='Alice',
        )
        result = str(link)
        assert 'pending' in result


@freeze_time('2026-04-10 12:00:00')
class TestProposalAlertModel:
    def test_save_auto_assigns_priority_from_alert_type(self, proposal):
        alert = ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='engagement_decay',
            message='High urgency',
            alert_date=timezone.now(),
        )

        assert alert.priority == 'critical'

    def test_save_preserves_non_normal_priority(self, proposal):
        alert = ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='reminder',
            priority='high',
            message='Keep custom priority',
            alert_date=timezone.now(),
        )

        assert alert.priority == 'high'

    def test_str_contains_client_name_and_message_excerpt(self, proposal):
        alert = ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='reminder',
            message='Follow up about pricing and next steps',
            alert_date=timezone.now(),
        )

        result = str(alert)
        assert proposal.client_name in result
        assert 'Follow up about pricing' in result
