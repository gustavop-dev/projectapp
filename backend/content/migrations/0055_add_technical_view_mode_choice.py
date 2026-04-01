# Generated manually — add 'technical' to proposal tracking view_mode choices

from django.db import migrations, models


VIEW_MODE_CHOICES = [
    ('executive', 'Executive'),
    ('detailed', 'Detailed'),
    ('technical', 'Technical'),
    ('unknown', 'Unknown'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0054_proposalsection_technical_document'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposalviewevent',
            name='view_mode',
            field=models.CharField(
                choices=VIEW_MODE_CHOICES,
                default='unknown',
                help_text='Whether the client viewed in executive, detailed, or technical mode.',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='proposalsectionview',
            name='view_mode',
            field=models.CharField(
                choices=VIEW_MODE_CHOICES,
                default='unknown',
                help_text='Whether this section was viewed in executive, detailed, or technical mode.',
                max_length=20,
            ),
        ),
    ]
