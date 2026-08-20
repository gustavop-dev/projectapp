from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta
from django.db import migrations, models


TWO_PLACES = Decimal('0.01')


def _replace_value(value, old, new):
    if isinstance(value, list):
        return [_replace_value(item, old, new) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_value(item, old, new)
            for key, item in value.items()
        }
    return new if value == old else value


def _migrate_project_tiers(Project, HostingSubscription, *, reverse=False):
    source = 'nine_month' if reverse else 'annual'
    target = 'annual' if reverse else 'nine_month'
    months = 12 if reverse else 9
    label = 'Anual' if reverse else 'Cada 9 meses'

    historical_project_ids = HostingSubscription.objects.filter(
        plan=source,
    ).filter(
        models.Q(status='cancelled') | models.Q(is_archived=True),
    ).values_list('project_id', flat=True)
    projects = Project.objects.exclude(status='archived').exclude(
        pk__in=historical_project_ids,
    )
    for project in projects.iterator():
        changed = False
        tiers = []
        for raw_tier in (project.hosting_tiers or []):
            tier = dict(raw_tier) if isinstance(raw_tier, dict) else raw_tier
            if isinstance(tier, dict) and tier.get('frequency') == source:
                tier['frequency'] = target
                tier['months'] = months
                tier['label'] = label
                if tier.get('effective_monthly') is not None:
                    tier['billing_amount'] = int(
                        Decimal(str(tier['effective_monthly'])) * months
                    )
                changed = True
            tiers.append(tier)
        if changed:
            project.hosting_tiers = tiers
            project.save(update_fields=['hosting_tiers'])


def migrate_to_nine_month(apps, schema_editor):
    HostingSubscription = apps.get_model('accounts', 'HostingSubscription')
    Payment = apps.get_model('accounts', 'Payment')
    Project = apps.get_model('accounts', 'Project')
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    subscriptions = HostingSubscription.objects.filter(
        is_archived=False,
        plan='annual',
        status__in=('pending', 'active', 'suspended'),
    )
    blocking_payment = Payment.objects.filter(
        subscription__in=subscriptions,
        status__in=('pending', 'processing'),
    ).filter(
        models.Q(status='processing')
        | models.Q(wompi_transaction_id__gt='')
        | models.Q(wompi_payment_link_id__gt='')
        | models.Q(wompi_payment_link_url__gt='')
    ).first()
    if blocking_payment:
        raise RuntimeError(
            'Cannot migrate annual hosting subscription while payment '
            f'{blocking_payment.pk} is processing or linked to Wompi.'
        )

    for subscription in subscriptions.iterator():
        subscription.plan = 'nine_month'
        subscription.billing_amount = (
            subscription.effective_monthly_amount * Decimal('9')
        ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        next_dates = []
        for payment in Payment.objects.filter(
            subscription_id=subscription.pk,
            status='pending',
            is_archived=False,
        ).iterator():
            period_end = (
                payment.billing_period_start
                + relativedelta(months=9)
                - relativedelta(days=1)
            )
            payment.amount = subscription.billing_amount
            payment.billing_period_end = period_end
            payment.description = (
                f'Hosting Cada 9 meses — {payment.billing_period_start} '
                f'a {period_end}'
            )
            payment.save(update_fields=[
                'amount', 'billing_period_end', 'description',
            ])
            next_dates.append(period_end + relativedelta(days=1))

        if next_dates:
            subscription.next_billing_date = max(next_dates)
        subscription.save(update_fields=[
            'plan', 'billing_amount', 'next_billing_date', 'updated_at',
        ])

    _migrate_project_tiers(Project, HostingSubscription)

    for tab in SavedFilterTab.objects.filter(
        view='accounting_hosting',
    ).iterator():
        if tab.is_seeded and (
            'monthly' in (tab.filters or {}).get('modalities', [])
            or 'monthly' in (tab.base_filters or {}).get('modalities', [])
        ):
            tab.delete()
            continue
        new_filters = _replace_value(tab.filters, 'annual', 'nine_month')
        new_base_filters = _replace_value(
            tab.base_filters, 'annual', 'nine_month',
        )
        fields = []
        if new_filters != tab.filters:
            tab.filters = new_filters
            fields.append('filters')
        if new_base_filters != tab.base_filters:
            tab.base_filters = new_base_filters
            fields.append('base_filters')
        if tab.is_seeded and tab.name == 'Anuales':
            tab.name = 'Cada 9 meses'
            fields.append('name')
        if fields:
            tab.save(update_fields=fields)


def migrate_back_to_annual(apps, schema_editor):
    HostingSubscription = apps.get_model('accounts', 'HostingSubscription')
    Payment = apps.get_model('accounts', 'Payment')
    Project = apps.get_model('accounts', 'Project')
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    subscriptions = HostingSubscription.objects.filter(
        is_archived=False,
        plan='nine_month',
        status__in=('pending', 'active', 'suspended'),
    )
    for subscription in subscriptions.iterator():
        subscription.plan = 'annual'
        subscription.billing_amount = (
            subscription.effective_monthly_amount * Decimal('12')
        ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        next_dates = []
        for payment in Payment.objects.filter(
            subscription_id=subscription.pk,
            status='pending',
            is_archived=False,
        ).iterator():
            period_end = (
                payment.billing_period_start
                + relativedelta(months=12)
                - relativedelta(days=1)
            )
            payment.amount = subscription.billing_amount
            payment.billing_period_end = period_end
            payment.description = (
                f'Hosting Anual — {payment.billing_period_start} a {period_end}'
            )
            payment.save(update_fields=[
                'amount', 'billing_period_end', 'description',
            ])
            next_dates.append(period_end + relativedelta(days=1))
        if next_dates:
            subscription.next_billing_date = max(next_dates)
        subscription.save(update_fields=[
            'plan', 'billing_amount', 'next_billing_date', 'updated_at',
        ])

    _migrate_project_tiers(
        Project, HostingSubscription, reverse=True,
    )
    for tab in SavedFilterTab.objects.filter(
        view='accounting_hosting',
    ).iterator():
        new_filters = _replace_value(tab.filters, 'nine_month', 'annual')
        new_base_filters = _replace_value(
            tab.base_filters, 'nine_month', 'annual',
        )
        fields = []
        if new_filters != tab.filters:
            tab.filters = new_filters
            fields.append('filters')
        if new_base_filters != tab.base_filters:
            tab.base_filters = new_base_filters
            fields.append('base_filters')
        if tab.is_seeded and tab.name == 'Cada 9 meses':
            tab.name = 'Anuales'
            fields.append('name')
        if fields:
            tab.save(update_fields=fields)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0203_hosting_nine_month_terms'),
        ('accounts', '0053_mysql_compatible_unique_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='hosting_tiers',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    'Hosting billing tiers from proposal '
                    '(quarterly/semiannual/nine-month with pricing).'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='hostingsubscription',
            name='plan',
            field=models.CharField(
                choices=[
                    ('quarterly', 'Trimestral'),
                    ('semiannual', 'Semestral'),
                    ('nine_month', 'Cada 9 meses'),
                ],
                default='quarterly',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='hostingsubscription',
            name='discount_percent',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Discount % based on the selected hosting plan.',
            ),
        ),
        migrations.RunPython(migrate_to_nine_month, migrate_back_to_annual),
    ]
