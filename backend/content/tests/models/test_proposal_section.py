"""Tests for ProposalSection, ProposalRequirementGroup, and ProposalRequirementItem models.

Covers: foreign key relationships, ordering, unique_together, __str__, defaults.
"""
import pytest

from content.models import (
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
)

pytestmark = pytest.mark.django_db


class TestProposalSection:
    def test_str_returns_client_name_and_type(self, proposal_section):
        assert 'Acme Corp' in str(proposal_section)
        assert 'Greeting' in str(proposal_section)

    def test_section_belongs_to_proposal(self, proposal_section, proposal):
        assert proposal_section.proposal == proposal

    def test_default_order_is_zero(self, proposal_section):
        assert proposal_section.order == 0

    def test_default_is_enabled_true(self, proposal_section):
        assert proposal_section.is_enabled is True

    def test_default_content_json_empty_dict(self, proposal):
        section = ProposalSection.objects.create(
            proposal=proposal,
            section_type='timeline',
            title='Timeline',
        )
        assert section.content_json == {}

    def test_default_is_wide_panel_false(self, proposal_section):
        assert proposal_section.is_wide_panel is False

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


class TestProposalRequirementGroup:
    def test_str_returns_client_and_title(self, requirement_group):
        assert 'Acme Corp' in str(requirement_group)
        assert 'Views' in str(requirement_group)

    def test_group_belongs_to_proposal(self, requirement_group, proposal):
        assert requirement_group.proposal == proposal

    def test_groups_ordered_by_order_field(self, proposal):
        ProposalRequirementGroup.objects.create(
            proposal=proposal, group_id='g1', title='G1', order=1,
        )
        ProposalRequirementGroup.objects.create(
            proposal=proposal, group_id='g0', title='G0', order=0,
        )
        groups = list(proposal.requirement_groups.all())
        assert groups[0].order <= groups[1].order

    def test_cascade_delete_with_proposal(self, proposal, requirement_group):
        proposal.delete()
        assert not ProposalRequirementGroup.objects.filter(
            pk=requirement_group.pk
        ).exists()


class TestProposalRequirementItem:
    def test_str_returns_name(self, requirement_item):
        assert str(requirement_item) == 'Dashboard View'

    def test_item_belongs_to_group(self, requirement_item, requirement_group):
        assert requirement_item.group == requirement_group

    def test_default_icon_is_checkmark(self, requirement_group):
        item = ProposalRequirementItem.objects.create(
            group=requirement_group,
            item_id='test-item',
            name='Test Item',
        )
        assert item.icon == '✅'

    def test_default_options_empty_list(self, requirement_item):
        assert requirement_item.options == []

    def test_default_fields_empty_list(self, requirement_item):
        assert requirement_item.fields == []

    def test_cascade_delete_with_group(self, requirement_group, requirement_item):
        requirement_group.delete()
        assert not ProposalRequirementItem.objects.filter(
            pk=requirement_item.pk
        ).exists()
