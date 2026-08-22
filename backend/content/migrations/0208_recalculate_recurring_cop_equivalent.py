from decimal import Decimal

from django.db import migrations, models


def recalculate_recurring_cop_equivalents(apps, schema_editor):
    """Repair every cached equivalent using the configured current rate."""
    AccountingSettings = apps.get_model('content', 'AccountingSettings')
    RecurringPayment = apps.get_model('content', 'RecurringPayment')

    rate = AccountingSettings.objects.filter(pk=1).values_list(
        'usd_exchange_rate', flat=True,
    ).first() or Decimal('4000.00')
    changed = []
    for payment in RecurringPayment.objects.all().iterator(chunk_size=500):
        if payment.currency == 'USD':
            expected = (payment.price * rate).quantize(Decimal('0.01'))
        else:
            expected = payment.price.quantize(Decimal('0.01'))
        if payment.cop_equivalent != expected:
            payment.cop_equivalent = expected
            changed.append(payment)
    if changed:
        RecurringPayment.objects.bulk_update(
            changed, ['cop_equivalent'], batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0207_document_client_custom_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurringpayment',
            name='cop_equivalent',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                editable=False,
                max_digits=14,
            ),
        ),
        migrations.RunPython(
            recalculate_recurring_cop_equivalents,
            migrations.RunPython.noop,
        ),
    ]
