"""Tests for the BusinessProposal model.

Covers: UUID generation, slug, status choices, is_expired property,
days_remaining property, public_url property, and __str__.
"""
import datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSectionView,
    ProposalShareLink,
    ProposalViewEvent,
)

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
    def test_public_url_contains_uuid(self, proposal):
        assert str(proposal.uuid) in proposal.public_url
        assert 'proposal' in proposal.public_url

    def test_public_url_starts_with_base(self, proposal):
        assert '/proposal/' in proposal.public_url
        assert str(proposal.uuid) in proposal.public_url


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
