"""Regression coverage for the production recurring-value repair."""
from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps

from content.models import AccountingSettings, RecurringPayment


pytestmark = pytest.mark.django_db
migration = import_module(
    'content.migrations.0208_recalculate_recurring_cop_equivalent',
)


def test_forward_recalculates_every_recurring_from_the_current_rate():
    settings = AccountingSettings.load()
    settings.usd_exchange_rate = Decimal('4000.00')
    settings.save()
    usd = RecurringPayment.objects.create(
        name='Chat-GPT', price=Decimal('200.00'), currency='USD',
    )
    cop = RecurringPayment.objects.create(
        name='Netflix', price=Decimal('39800.00'), currency='COP',
    )
    # Reproduce rows written by the old implementation without invoking the
    # new model save invariant.
    RecurringPayment.objects.filter(pk=usd.pk).update(
        cop_equivalent=Decimal('80000.00'),
    )
    RecurringPayment.objects.filter(pk=cop.pk).update(
        cop_equivalent=Decimal('1.00'),
    )

    migration.recalculate_recurring_cop_equivalents(apps, None)

    usd.refresh_from_db()
    cop.refresh_from_db()
    assert usd.cop_equivalent == Decimal('800000.00')
    assert cop.cop_equivalent == Decimal('39800.00')
