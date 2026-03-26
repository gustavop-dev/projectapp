from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_payments_hosting'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='payment_milestones',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Development payment milestones from proposal section 4 (admin-visible only).',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='hosting_tiers',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Hosting billing tiers from proposal (semiannual/quarterly/monthly with pricing).',
            ),
        ),
    ]
