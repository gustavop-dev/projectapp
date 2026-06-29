from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models


def monthly_to_quarterly(apps, schema_editor):
    """Migrate any legacy month-to-month subscription to quarterly.

    Month-to-month hosting is no longer offered (minimum commitment is now
    quarterly). Existing 'monthly' subscriptions are moved to quarterly and
    granted the quarterly discount taken from their linked proposal (fallback
    10%), so the client's effective monthly rate drops while the cadence
    becomes every 3 months. Operator should notify the affected client.
    """
    HostingSubscription = apps.get_model('accounts', 'HostingSubscription')
    QUARTER_MONTHS = 3

    for sub in HostingSubscription.objects.filter(plan='monthly'):
        # Quarterly discount from phase 1's proposal, fallback 10%.
        q_disc = None
        project = getattr(sub, 'project', None)
        if project is not None:
            phase = project.phases.order_by('order').first()
            bp = getattr(phase, 'business_proposal', None) if phase else None
            if bp is not None:
                q_disc = getattr(bp, 'hosting_discount_quarterly', None)
        if q_disc is None:
            q_disc = 10

        base = Decimal(str(sub.base_monthly_amount or 0))
        factor = (Decimal('100') - Decimal(str(q_disc))) / Decimal('100')
        eff = (base * factor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        sub.plan = 'quarterly'
        sub.discount_percent = int(q_disc)
        sub.effective_monthly_amount = eff
        sub.billing_amount = (eff * QUARTER_MONTHS).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        )
        sub.save(update_fields=[
            'plan', 'discount_percent', 'effective_monthly_amount',
            'billing_amount',
        ])


def noop_reverse(apps, schema_editor):
    # Irreversible by design: 'monthly' is no longer an offered plan.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0034_hostingsubscription_plan_annual'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostingsubscription',
            name='plan',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('quarterly', 'Trimestral'),
                    ('semiannual', 'Semestral'),
                    ('annual', 'Anual'),
                ],
                default='quarterly',
            ),
        ),
        migrations.RunPython(monthly_to_quarterly, noop_reverse),
    ]
