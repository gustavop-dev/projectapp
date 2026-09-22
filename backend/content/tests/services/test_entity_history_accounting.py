"""Every accounting aggregate writes a durable revision for a business edit."""

from datetime import date
from decimal import Decimal

import pytest

from content.models import (
    AccountingSettings,
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCard,
    CreditCardStatement,
    CreditCardTransaction,
    EntityHistory,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    MerchantAlias,
    NotificationRecipient,
    PocketMovement,
    RecurringPayment,
)


pytestmark = pytest.mark.django_db


def make_income():
    return IncomeRecord.objects.create(
        concept='Cobro inicial', kind=IncomeRecord.Kind.EXPECTED,
        period_date=date(2026, 9, 1), total_amount=Decimal('100.00'),
        gustavo_amount=Decimal('50.00'), carlos_amount=Decimal('50.00'),
    )


def make_expense():
    return ExpenseRecord.objects.create(
        concept='Costo inicial', period_date=date(2026, 9, 1),
        total_amount=Decimal('100.00'), gustavo_amount=Decimal('50.00'),
        carlos_amount=Decimal('50.00'),
    )


def make_hosting():
    return HostingRecord.objects.create(
        client_name='Cliente inicial', monthly_value=Decimal('100.00'),
    )


def make_pocket():
    return PocketMovement.objects.create(
        concept='Movimiento inicial', movement_date=date(2026, 9, 1),
        direction=PocketMovement.Direction.IN, amount=Decimal('100.00'),
    )


def make_recurring():
    return RecurringPayment.objects.create(
        name='Suscripción inicial', price=Decimal('100.00'),
        cop_equivalent=Decimal('100.00'), frequency=RecurringPayment.Frequency.MONTHLY,
    )


def make_ads():
    return AdsSpendRecord.objects.create(
        spend_date=date(2026, 9, 1), amount=Decimal('100.00'),
    )


def make_card_snapshot():
    return CardBalanceSnapshot.objects.create(
        snapshot_date=date(2026, 9, 1), card_name='Tarjeta inicial',
        available_amount=Decimal('400.00'), debt_amount=Decimal('100.00'),
    )


def make_credit_card():
    return CreditCard.objects.create(name='Tarjeta catálogo', credit_limit=Decimal('1000.00'))


def make_statement():
    return CreditCardStatement.objects.create(
        card_name='Tarjeta extracto', period_date=date(2026, 9, 1),
        purchases_total=Decimal('100.00'),
    )


def make_statement_tx():
    statement = make_statement()
    return CreditCardTransaction.objects.create(
        statement=statement, transaction_date=date(2026, 9, 1),
        raw_description='COMERCIO INICIAL', amount=Decimal('100.00'),
    )


def make_merchant_alias():
    return MerchantAlias.objects.create(
        match_text='COMERCIO INICIAL', merchant_name='Comercio inicial',
    )


def make_notification_recipient():
    return NotificationRecipient.objects.create(email='initial@example.test')


def make_settings():
    return AccountingSettings.load()


ACCOUNTING_EDITS = [
    ('income', make_income, 'concept', 'Cobro actualizado'),
    ('expense', make_expense, 'concept', 'Costo actualizado'),
    ('hosting', make_hosting, 'client_name', 'Cliente actualizado'),
    ('pocket', make_pocket, 'concept', 'Movimiento actualizado'),
    ('recurring', make_recurring, 'name', 'Suscripción actualizada'),
    ('ads', make_ads, 'amount', Decimal('200.00')),
    ('card_snapshot', make_card_snapshot, 'debt_amount', Decimal('200.00')),
    ('credit_card', make_credit_card, 'credit_limit', Decimal('2000.00')),
    ('statement', make_statement, 'purchases_total', Decimal('200.00')),
    ('statement_tx', make_statement_tx, 'merchant_name', 'Comercio actualizado'),
    ('merchant_alias', make_merchant_alias, 'merchant_name', 'Alias actualizado'),
    ('notification_recipient', make_notification_recipient, 'is_active', False),
    ('settings', make_settings, 'notifications_enabled', False),
]


@pytest.mark.parametrize(
    'entity_type,factory,field,new_value', ACCOUNTING_EDITS,
    ids=[case[0] for case in ACCOUNTING_EDITS],
)
def test_accounting_edit_creates_revision_for_registered_entity(
    entity_type, factory, field, new_value,
):
    """Fails if a registered accounting record accepts an edit without durable history."""
    record = factory()
    history = EntityHistory.objects.get(entity_type=entity_type, object_id=record.pk)
    before = history.entries.count()
    setattr(record, field, new_value)
    record.save(update_fields=[field])

    assert history.entries.count() == before + 1
    assert field in [change['field'] for change in history.entries.first().changed_fields]
