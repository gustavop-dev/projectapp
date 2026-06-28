from django.db import migrations, models


def bump_default_config_to_80(apps, schema_editor):
    """Raise existing default-config rows still on a previous default to 80%.

    Only rows currently holding a previous default (40 or 70) are touched, so any
    value an admin intentionally customized is left untouched.
    """
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    ProposalDefaultConfig.objects.filter(hosting_percent__in=[40, 70]).update(hosting_percent=80)


def revert_default_config_to_40(apps, schema_editor):
    ProposalDefaultConfig = apps.get_model('content', 'ProposalDefaultConfig')
    ProposalDefaultConfig.objects.filter(hosting_percent=80).update(hosting_percent=40)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0123_documentfolder_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessproposal',
            name='hosting_percent',
            field=models.PositiveIntegerField(default=80, help_text='Percentage of total investment charged for annual hosting.'),
        ),
        migrations.AlterField(
            model_name='proposaldefaultconfig',
            name='hosting_percent',
            field=models.PositiveSmallIntegerField(default=80),
        ),
        migrations.RunPython(bump_default_config_to_80, revert_default_config_to_40),
    ]
