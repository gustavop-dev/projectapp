from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models


CURRENT_PROPOSAL_STATUSES = (
    'draft', 'sent', 'viewed', 'negotiating', 'expired',
)
TWO_PLACES = Decimal('0.01')


def _canonical_tiers(owner, language, hosting_plan, *, reverse=False):
    plan = dict(hosting_plan or {})
    stored = {
        tier.get('frequency'): dict(tier)
        for tier in (plan.get('billingTiers') or [])
        if isinstance(tier, dict)
    }

    source = 'nine_month' if reverse else 'annual'
    target = 'annual' if reverse else 'nine_month'
    if source in stored and target not in stored:
        stored[target] = stored[source]

    english = language == 'en'
    if reverse:
        definitions = (
            ('annual', 12, 'Annual' if english else 'Anual',
             'Best value' if english else 'Máximo descuento',
             getattr(owner, 'hosting_discount_nine_month', 40)),
            ('semiannual', 6, 'Semiannual' if english else 'Semestral',
             '20% off' if english else '20% dcto',
             getattr(owner, 'hosting_discount_semiannual', 20)),
            ('quarterly', 3, 'Quarterly' if english else 'Trimestral',
             '10% off' if english else '10% dcto',
             getattr(owner, 'hosting_discount_quarterly', 10)),
        )
    else:
        definitions = (
            ('nine_month', 9,
             'Every 9 months' if english else 'Cada 9 meses',
             'Best value' if english else 'Máximo descuento',
             getattr(owner, 'hosting_discount_nine_month', 40)),
            ('semiannual', 6, 'Semiannual' if english else 'Semestral',
             '20% off' if english else '20% dcto',
             getattr(owner, 'hosting_discount_semiannual', 20)),
            ('quarterly', 3, 'Quarterly' if english else 'Trimestral',
             '10% off' if english else '10% dcto',
             getattr(owner, 'hosting_discount_quarterly', 10)),
        )

    tiers = []
    for frequency, months, label, default_badge, discount in definitions:
        previous = stored.get(frequency) or {}
        tiers.append({
            'frequency': frequency,
            'months': months,
            'discountPercent': discount,
            'label': label,
            'badge': previous.get('badge', default_badge),
        })
    plan['billingTiers'] = tiers
    if not reverse:
        plan.pop('annualLabel', None)
        plan.pop('annualPrice', None)
    return plan


def _update_section(section, owner, language, *, reverse=False):
    content = dict(section.content_json or {})
    content['hostingPlan'] = _canonical_tiers(
        owner, language, content.get('hostingPlan'), reverse=reverse,
    )
    section.content_json = content
    section.save(update_fields=['content_json'])


def migrate_to_nine_month(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    ProposalSection = apps.get_model('content', 'ProposalSection')
    HostingRecord = apps.get_model('content', 'HostingRecord')

    current_proposals = BusinessProposal.objects.filter(
        is_active=True,
        status__in=CURRENT_PROPOSAL_STATUSES,
    )
    for proposal in current_proposals.iterator():
        sections = ProposalSection.objects.filter(
            proposal_id=proposal.pk,
            section_type='investment',
        )
        for section in sections.iterator():
            _update_section(section, proposal, proposal.language)

    for config in ProposalDefaultConfig.objects.all().iterator():
        sections_json = []
        changed = False
        for raw_section in (config.sections_json or []):
            section = dict(raw_section) if isinstance(raw_section, dict) else raw_section
            if isinstance(section, dict) and section.get('section_type') == 'investment':
                content = dict(section.get('content_json') or {})
                content['hostingPlan'] = _canonical_tiers(
                    config, config.language, content.get('hostingPlan'),
                )
                section['content_json'] = content
                changed = True
            sections_json.append(section)
        if changed:
            config.sections_json = sections_json
            config.save(update_fields=['sections_json'])

    for hosting in HostingRecord.objects.filter(
        is_active=True,
        payment_modality='annual',
    ).iterator():
        current_cycle = hosting.payment_per_cycle or (
            hosting.monthly_value * Decimal('12')
        )
        hosting.payment_modality = 'nine_month'
        hosting.payment_per_cycle = (
            current_cycle * Decimal('9') / Decimal('12')
        ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        hosting.save(update_fields=['payment_modality', 'payment_per_cycle'])


def migrate_back_to_annual(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    ProposalSection = apps.get_model('content', 'ProposalSection')
    HostingRecord = apps.get_model('content', 'HostingRecord')

    current_proposals = BusinessProposal.objects.filter(
        is_active=True,
        status__in=CURRENT_PROPOSAL_STATUSES,
    )
    for proposal in current_proposals.iterator():
        for section in ProposalSection.objects.filter(
            proposal_id=proposal.pk,
            section_type='investment',
        ).iterator():
            _update_section(
                section, proposal, proposal.language, reverse=True,
            )

    for config in ProposalDefaultConfig.objects.all().iterator():
        sections_json = []
        changed = False
        for raw_section in (config.sections_json or []):
            section = dict(raw_section) if isinstance(raw_section, dict) else raw_section
            if isinstance(section, dict) and section.get('section_type') == 'investment':
                content = dict(section.get('content_json') or {})
                content['hostingPlan'] = _canonical_tiers(
                    config, config.language, content.get('hostingPlan'),
                    reverse=True,
                )
                section['content_json'] = content
                changed = True
            sections_json.append(section)
        if changed:
            config.sections_json = sections_json
            config.save(update_fields=['sections_json'])

    for hosting in HostingRecord.objects.filter(
        is_active=True,
        payment_modality='nine_month',
    ).iterator():
        hosting.payment_modality = 'annual'
        hosting.payment_per_cycle = (
            hosting.payment_per_cycle * Decimal('12') / Decimal('9')
        ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        hosting.save(update_fields=['payment_modality', 'payment_per_cycle'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0202_income_pocket_movement_fk'),
    ]

    operations = [
        migrations.RenameField(
            model_name='businessproposal',
            old_name='hosting_discount_annual',
            new_name='hosting_discount_nine_month',
        ),
        migrations.RenameField(
            model_name='proposaldefaultconfig',
            old_name='hosting_discount_annual',
            new_name='hosting_discount_nine_month',
        ),
        migrations.AlterField(
            model_name='businessproposal',
            name='hosting_percent',
            field=models.PositiveIntegerField(
                default=60,
                help_text=(
                    'Percentage of total investment used as the hosting price '
                    'reference before monthly proration.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='businessproposal',
            name='hosting_discount_nine_month',
            field=models.PositiveIntegerField(
                default=40,
                help_text='Default discount % for nine-month hosting payments.',
            ),
        ),
        migrations.AlterField(
            model_name='hostingrecord',
            name='payment_modality',
            field=models.CharField(
                choices=[
                    ('quarterly', 'Trimestral'),
                    ('semiannual', 'Semestral'),
                    ('nine_month', 'Cada 9 meses'),
                ],
                default='quarterly',
                max_length=12,
            ),
        ),
        migrations.RunPython(migrate_to_nine_month, migrate_back_to_annual),
    ]
