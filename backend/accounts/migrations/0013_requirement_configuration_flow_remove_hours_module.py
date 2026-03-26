from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_project_hosting_start_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requirement',
            name='estimated_hours',
        ),
        migrations.RemoveField(
            model_name='requirement',
            name='module',
        ),
        migrations.AddField(
            model_name='requirement',
            name='configuration',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Role/privilege context for this requirement (e.g. "Only for admin role").',
            ),
        ),
        migrations.AddField(
            model_name='requirement',
            name='flow',
            field=models.TextField(
                blank=True,
                default='',
                help_text='User flow description within the software for this requirement.',
            ),
        ),
    ]
