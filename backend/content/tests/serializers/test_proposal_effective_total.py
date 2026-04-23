"""Tests for ProposalDetailSerializer.effective_total_investment.

Covers the field added to close the divergence between the admin detail
view and the client public view: admin was seeing the base investment
while the client saw base + selected calculator modules, and the backend
was not exposing the effective total anywhere in the detail API.
"""
from decimal import Decimal

import pytest

from content.models import ProposalSection
from content.serializers.proposal import ProposalDetailSerializer

pytestmark = pytest.mark.django_db


def _make_fr_section(proposal, *, calc_percent=15, calc_group_id='mod-a',
                    extra_groups=None):
    """Create a functional_requirements section with one calculator module."""
    groups = extra_groups or []
    groups.append({
        'id': calc_group_id,
        'title': 'Módulo adicional',
        'is_calculator_module': True,
        'price_percent': calc_percent,
    })
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
        title='Funcional',
        order=3,
        is_enabled=True,
        content_json={'groups': groups},
    )


def test_effective_total_equals_base_when_no_modules_selected(proposal):
    _make_fr_section(proposal)
    proposal.selected_modules = []
    proposal.save(update_fields=['selected_modules'])

    data = ProposalDetailSerializer(proposal, context={'is_admin': True}).data

    assert Decimal(data['effective_total_investment']) == Decimal(
        proposal.total_investment,
    )


def test_effective_total_adds_selected_calculator_module(proposal):
    _make_fr_section(proposal, calc_percent=15, calc_group_id='mod-a')
    proposal.selected_modules = ['module-mod-a']
    proposal.save(update_fields=['selected_modules'])

    data = ProposalDetailSerializer(proposal, context={'is_admin': True}).data

    # 15000 base + 15% = 17250
    assert Decimal(data['effective_total_investment']) == Decimal('17250.00')


def test_effective_total_accepts_bare_group_ids(proposal):
    """Persisted payloads without the ``module-`` prefix must still resolve."""
    _make_fr_section(proposal, calc_percent=10, calc_group_id='mod-b')
    proposal.selected_modules = ['mod-b']
    proposal.save(update_fields=['selected_modules'])

    data = ProposalDetailSerializer(proposal, context={'is_admin': True}).data

    # 15000 base + 10% = 16500
    assert Decimal(data['effective_total_investment']) == Decimal('16500.00')


def test_effective_total_falls_back_to_admin_defaults(proposal):
    """When the client never confirmed, admin-marked defaults drive the total."""
    ProposalSection.objects.create(
        proposal=proposal,
        section_type=ProposalSection.SectionType.FUNCTIONAL_REQUIREMENTS,
        title='Funcional',
        order=3,
        is_enabled=True,
        content_json={
            'groups': [
                {
                    'id': 'mod-default',
                    'title': 'Default add-on',
                    'is_calculator_module': True,
                    'price_percent': 20,
                    'default_selected': True,
                },
            ],
        },
    )
    proposal.selected_modules = []
    proposal.save(update_fields=['selected_modules'])

    data = ProposalDetailSerializer(proposal, context={'is_admin': True}).data

    assert Decimal(data['effective_total_investment']) == Decimal('18000.00')


def test_effective_total_is_public_field(proposal):
    """Client-facing (non-admin) context exposes the same computed value."""
    _make_fr_section(proposal, calc_percent=15, calc_group_id='mod-a')
    proposal.selected_modules = ['module-mod-a']
    proposal.save(update_fields=['selected_modules'])

    data = ProposalDetailSerializer(proposal, context={'is_admin': False}).data

    assert 'effective_total_investment' in data
    assert Decimal(data['effective_total_investment']) == Decimal('17250.00')
