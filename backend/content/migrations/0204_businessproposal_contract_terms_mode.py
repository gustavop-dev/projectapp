from django.db import migrations, models


VIEW_MODE_CHOICES = [
    ('executive', 'Executive'),
    ('detailed', 'Detailed'),
    ('technical', 'Technical'),
    ('legal', 'Legal'),
    ('unknown', 'Unknown'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0203_hosting_nine_month_terms'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessproposal',
            name='show_contract_terms',
            field=models.BooleanField(
                default=True,
                help_text=(
                    'Whether Spanish public proposals expose the generic contract '
                    'terms module and its masked draft download.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='proposalviewevent',
            name='view_mode',
            field=models.CharField(
                choices=VIEW_MODE_CHOICES,
                default='unknown',
                help_text=(
                    'Whether the client viewed in executive, detailed, technical, '
                    'or legal mode.'
                ),
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='proposalsectionview',
            name='subsection_key',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Fragment key for technical document subsections or legal '
                    'contract clauses.'
                ),
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='proposalsectionview',
            name='view_mode',
            field=models.CharField(
                choices=VIEW_MODE_CHOICES,
                default='unknown',
                help_text=(
                    'Whether this section was viewed in executive, detailed, '
                    'technical, or legal mode.'
                ),
                max_length=20,
            ),
        ),
    ]
