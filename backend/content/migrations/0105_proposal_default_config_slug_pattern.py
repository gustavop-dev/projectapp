from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0104_business_proposal_slug_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposaldefaultconfig',
            name='default_slug_pattern',
            field=models.CharField(
                blank=True,
                default='{client_name}',
                help_text=(
                    'Template used to auto-generate the public slug when a seller '
                    'does not provide one at creation time. Placeholders: '
                    '{client_name}, {project_type}, {year}. The rendered value is '
                    'slugified and deduplicated with numeric suffixes.'
                ),
                max_length=200,
            ),
        ),
    ]
