"""Tests for the BusinessProposal model.

Covers: UUID generation, slug, status choices, is_expired property,
days_remaining property, public_url property, and __str__.
"""
import datetime

import pytest
from freezegun import freeze_time

from content.models import BusinessProposal

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
        'draft', 'sent', 'viewed', 'accepted', 'rejected', 'expired',
    ])
    def test_valid_status_choices(self, status):
        prop = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            status=status,
        )
        assert prop.status == status
