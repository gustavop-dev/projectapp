from django.db import migrations, models
from django.db.models import F

from content.services.proposal_service import ProposalService


SECTION_TYPE_CHOICES = [
    ('greeting', 'Greeting'),
    ('executive_summary', 'Executive Summary'),
    ('context_diagnostic', 'Context & Diagnostic'),
    ('conversion_strategy', 'Conversion Strategy'),
    ('design_ux', 'Design & UX'),
    ('creative_support', 'Creative Support'),
    ('development_stages', 'Development Stages'),
    ('process_methodology', 'Process Methodology'),
    ('functional_requirements', 'Functional Requirements'),
    ('timeline', 'Timeline'),
    ('investment', 'Investment'),
    ('proposal_summary', 'Proposal Summary'),
    ('final_note', 'Final Note'),
    ('next_steps', 'Next Steps'),
    ('technical_document', 'Technical Document'),
    ('value_added_modules', 'Value Added Modules'),
]


_DEFAULTS_BY_LANGUAGE = {}


def _defaults_index(language):
    if language not in _DEFAULTS_BY_LANGUAGE:
        _DEFAULTS_BY_LANGUAGE[language] = {
            cfg['section_type']: cfg
            for cfg in ProposalService.get_default_sections(language=language)
        }
    return _DEFAULTS_BY_LANGUAGE[language]


def _get_default_manual_module(language):
    fr_default = _defaults_index(language).get('functional_requirements')
    if not fr_default:
        return None
    for group in (fr_default.get('content_json') or {}).get('groups') or []:
        if group.get('id') == 'manual_module':
            return group
    return None


def backfill_value_added_modules(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    ProposalSection = apps.get_model('content', 'ProposalSection')

    for proposal in BusinessProposal.objects.all().only('id', 'language'):
        language = getattr(proposal, 'language', 'es') or 'es'
        defaults = _defaults_index(language)

        fr_section = ProposalSection.objects.filter(
            proposal_id=proposal.pk, section_type='functional_requirements',
        ).first()
        if fr_section:
            content_json = fr_section.content_json or {}
            groups = content_json.get('groups') or []
            existing_ids = {g.get('id') for g in groups if isinstance(g, dict)}
            if 'manual_module' not in existing_ids:
                manual_default = _get_default_manual_module(language)
                if manual_default:
                    groups.append(manual_default)
                    content_json['groups'] = groups
                    fr_section.content_json = content_json
                    fr_section.save(update_fields=['content_json'])

        already_has_section = ProposalSection.objects.filter(
            proposal_id=proposal.pk, section_type='value_added_modules',
        ).exists()
        if not already_has_section:
            ProposalSection.objects.filter(
                proposal_id=proposal.pk, order__gte=9,
            ).update(order=F('order') + 1)

            cfg = defaults.get('value_added_modules')
            if cfg:
                ProposalSection.objects.create(
                    proposal_id=proposal.pk,
                    section_type='value_added_modules',
                    title=cfg['title'],
                    order=cfg['order'],
                    is_enabled=True,
                    content_json=dict(cfg['content_json']),
                    is_wide_panel=cfg.get('is_wide_panel', False),
                )


def remove_value_added_modules(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalSection.objects.filter(section_type='value_added_modules').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0101_diagnostic_default_config'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalsection',
            name='section_type',
            field=models.CharField(choices=SECTION_TYPE_CHOICES, max_length=30),
        ),
        migrations.RunPython(backfill_value_added_modules, remove_value_added_modules),
    ]
