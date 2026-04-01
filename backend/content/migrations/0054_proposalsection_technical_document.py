# Generated manually for technical_document section type + backfill

from django.db import migrations, models

from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON


def backfill_technical_sections(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    for proposal in BusinessProposal.objects.all().only('id', 'client_name'):
        if ProposalSection.objects.filter(
            proposal_id=proposal.pk, section_type='technical_document'
        ).exists():
            continue
        ProposalSection.objects.create(
            proposal_id=proposal.pk,
            section_type='technical_document',
            title='🔧 Documento técnico',
            order=13,
            is_enabled=True,
            content_json=dict(EMPTY_TECHNICAL_DOCUMENT_JSON),
            is_wide_panel=True,
        )


def remove_technical_sections(apps, schema_editor):
    ProposalSection = apps.get_model('content', 'ProposalSection')
    ProposalSection.objects.filter(section_type='technical_document').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0053_alter_businessproposal_market_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalsection',
            name='section_type',
            field=models.CharField(
                choices=[
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
                ],
                max_length=30,
            ),
        ),
        migrations.RunPython(backfill_technical_sections, remove_technical_sections),
    ]
