"""Settle → linked cuenta de cobro sync: fully paid income marks it paid."""
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import Document, ExpenseRecord, IncomeRecord
from content.services import accounting_service, accounting_settlement_service
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify') as notify:
        yield notify


def make_expected(**overrides):
    fields = {
        'concept': 'Kore - Inicio 40%',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-07-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_linked_cuenta(income, status=Document.CommercialStatus.ISSUED):
    return Document.objects.create(
        document_type=get_collection_account_document_type(),
        title='Cuenta de cobro — Kore',
        commercial_status=status,
        income_record=income,
        total=income.total_amount,
    )


def settlement(**overrides):
    data = {
        'concept': 'Kore - Inicio 40%',
        'period_date': '2026-07-15',
        'destination': IncomeRecord.Destination.PARTNERS,
        'total_amount': Decimal('1000000.00'),
        'notes': '',
        'deductions': [],
        'expected_incomes': [],
    }
    data.update(overrides)
    return data


def test_full_settlement_marks_linked_cuenta_paid(superuser):
    income = make_expected()
    cuenta = make_linked_cuenta(income)

    accounting_settlement_service.settle_expected_income(
        income, settlement(), superuser,
    )

    cuenta.refresh_from_db()
    assert cuenta.commercial_status == Document.CommercialStatus.PAID


def test_partial_settlement_keeps_cuenta_issued(superuser):
    income = make_expected()
    cuenta = make_linked_cuenta(income)

    accounting_settlement_service.settle_expected_income(
        income, settlement(total_amount=Decimal('400000.00')), superuser,
    )

    cuenta.refresh_from_db()
    assert cuenta.commercial_status == Document.CommercialStatus.ISSUED


def test_cancelled_cuenta_is_never_revived(superuser):
    income = make_expected()
    cuenta = make_linked_cuenta(
        income, status=Document.CommercialStatus.CANCELLED,
    )

    accounting_settlement_service.settle_expected_income(
        income, settlement(), superuser,
    )

    cuenta.refresh_from_db()
    assert cuenta.commercial_status == Document.CommercialStatus.CANCELLED


def test_deduction_credit_completes_payment_and_syncs(superuser):
    income = make_expected()
    cuenta = make_linked_cuenta(income)

    accounting_settlement_service.settle_expected_income(
        income,
        settlement(
            total_amount=Decimal('992000.00'),
            deductions=[{
                'type': ExpenseRecord.DeductionType.GATEWAY_FEE,
                'detail': '',
                'amount': Decimal('8000.00'),
            }],
        ),
        superuser,
    )

    cuenta.refresh_from_db()
    assert cuenta.commercial_status == Document.CommercialStatus.PAID


def test_already_paid_cuenta_stays_paid_without_error(superuser):
    income = make_expected()
    cuenta = make_linked_cuenta(income, status=Document.CommercialStatus.PAID)

    accounting_settlement_service.settle_expected_income(
        income, settlement(), superuser,
    )

    cuenta.refresh_from_db()
    assert cuenta.commercial_status == Document.CommercialStatus.PAID
