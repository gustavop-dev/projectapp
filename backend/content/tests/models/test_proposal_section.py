"""Tests for the ProposalSection model.

Covers: foreign key relationships, ordering, unique_together, __str__, defaults.
"""
import pytest

from content.models import (
    ProposalSection,
)

pytestmark = pytest.mark.django_db


class TestProposalSection:
    def test_str_returns_client_name_and_type(self, proposal_section):
        assert 'Acme Corp' in str(proposal_section)
        assert 'Greeting' in str(proposal_section)

    def test_section_belongs_to_proposal(self, proposal_section, proposal):
        assert proposal_section.proposal == proposal
        assert proposal_section.proposal_id == proposal.id

    def test_default_order_is_zero(self, proposal_section):
        assert proposal_section.order == 0
        assert isinstance(proposal_section.order, int)

    def test_default_is_enabled_true(self, proposal_section):
        assert proposal_section.is_enabled is True
        assert proposal_section.is_enabled is not None

    def test_default_content_json_empty_dict(self, proposal):
        section = ProposalSection.objects.create(
            proposal=proposal,
            section_type='timeline',
            title='Timeline',
        )
        assert section.content_json == {}

    def test_default_is_wide_panel_false(self, proposal_section):
        assert proposal_section.is_wide_panel is False
        assert proposal_section.is_wide_panel is not None

    def test_unique_together_proposal_and_section_type(self, proposal, proposal_section):
        from django.db import IntegrityError, transaction
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProposalSection.objects.create(
                    proposal=proposal,
                    section_type='greeting',
                    title='Duplicate Greeting',
                )
        assert ProposalSection.objects.filter(
            proposal=proposal, section_type='greeting'
        ).count() == 1

    def test_sections_ordered_by_order_field(self, proposal):
        """Create two sections with explicit order values and verify queryset ordering."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='timeline',
            title='Timeline',
            order=2,
        )
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='investment',
            title='Investment',
            order=1,
        )
        sections = list(proposal.sections.all())
        assert sections[0].order <= sections[1].order

    def test_cascade_delete_with_proposal(self, proposal, proposal_section):
        proposal_id = proposal.id
        proposal.delete()
        assert not ProposalSection.objects.filter(
            proposal_id=proposal_id
        ).exists()
