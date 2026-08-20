from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps

from content.models import (
    BusinessProposal,
    HostingCycle,
    HostingRecord,
    ProposalDefaultConfig,
    ProposalSection,
)


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0203_hosting_nine_month_terms')


def investment_tiers(frequency='annual', months=12, label='Anual'):
    return {
        'hostingPlan': {
            'billingTiers': [{
                'frequency': frequency,
                'months': months,
                'discountPercent': 40,
                'label': label,
            }],
        },
    }


def make_proposal(status, *, is_active=True):
    proposal = BusinessProposal.objects.create(
        title=f'Proposal {status}',
        client_name='Cliente',
        status=status,
        is_active=is_active,
    )
    section = ProposalSection.objects.create(
        proposal=proposal,
        section_type='investment',
        title='Inversión',
        content_json=investment_tiers(),
    )
    return proposal, section


def test_forward_updates_current_proposal_without_rewriting_closed_snapshot():
    _, current_section = make_proposal('sent')
    _, closed_section = make_proposal('accepted')

    migration.migrate_to_nine_month(apps, None)

    current_section.refresh_from_db()
    closed_section.refresh_from_db()
    current_tier = current_section.content_json['hostingPlan']['billingTiers'][0]
    closed_tier = closed_section.content_json['hostingPlan']['billingTiers'][0]
    assert (current_tier['frequency'], current_tier['months']) == ('nine_month', 9)
    assert current_tier['label'] == 'Cada 9 meses'
    assert (closed_tier['frequency'], closed_tier['months']) == ('annual', 12)


def test_forward_preserves_effective_monthly_price_and_cycle_history():
    current = HostingRecord.objects.create(
        client_name='Actual',
        monthly_value=Decimal('100000.00'),
        payment_modality='annual',
        payment_per_cycle=Decimal('1200000.00'),
        is_active=True,
    )
    historical_cycle = HostingCycle.objects.create(
        hosting_record=current,
        modality='annual',
        amount=Decimal('1200000.00'),
        paid_at='2025-01-01',
    )
    inactive = HostingRecord.objects.create(
        client_name='Cerrado',
        monthly_value=Decimal('100000.00'),
        payment_modality='annual',
        payment_per_cycle=Decimal('1200000.00'),
        is_active=False,
    )

    migration.migrate_to_nine_month(apps, None)

    current.refresh_from_db()
    inactive.refresh_from_db()
    historical_cycle.refresh_from_db()
    assert current.payment_modality == 'nine_month'
    assert current.payment_per_cycle == Decimal('900000.00')
    assert inactive.payment_modality == 'annual'
    assert historical_cycle.modality == 'annual'
    assert historical_cycle.amount == Decimal('1200000.00')


def test_forward_updates_the_admin_default_section():
    config = ProposalDefaultConfig.objects.create(
        language='en',
        sections_json=[{
            'section_type': 'investment',
            'content_json': investment_tiers(label='Annual'),
        }],
    )

    migration.migrate_to_nine_month(apps, None)

    config.refresh_from_db()
    tier = config.sections_json[0]['content_json']['hostingPlan']['billingTiers'][0]
    assert tier['frequency'] == 'nine_month'
    assert tier['months'] == 9
    assert tier['label'] == 'Every 9 months'
