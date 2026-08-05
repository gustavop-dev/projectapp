"""Income API: has_collection_account flag + cuenta id/number exposure."""
from decimal import Decimal

import pytest

from content.models import Document, IncomeRecord
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

pytestmark = pytest.mark.django_db


def make_income(kind=IncomeRecord.Kind.EXPECTED, **overrides):
    fields = {
        'concept': 'Kore - Inicio 40%',
        'kind': kind,
        'period_date': '2026-07-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_cuenta(income, status=Document.CommercialStatus.ISSUED):
    return Document.objects.create(
        document_type=get_collection_account_document_type(),
        title='Cuenta de cobro — Kore',
        public_number='PA-KORE-001',
        commercial_status=status,
        income_record=income,
        total=income.total_amount,
    )


def _row(response, income_id):
    return next(
        row for row in response.data['results'] if row['id'] == income_id
    )


def test_list_annotates_linked_and_unlinked_rows(super_client):
    linked = make_income()
    cuenta = make_cuenta(linked)
    bare = make_income(concept='Xpandia - Fase 2')

    response = super_client.get('/api/accounting/incomes/')

    assert response.status_code == 200
    linked_row = _row(response, linked.pk)
    assert linked_row['has_collection_account'] is True
    assert linked_row['collection_account_id'] == cuenta.pk
    assert linked_row['collection_account_number'] == 'PA-KORE-001'
    bare_row = _row(response, bare.pk)
    assert bare_row['has_collection_account'] is False
    assert bare_row['collection_account_id'] is None
    assert bare_row['collection_account_number'] is None


def test_retrieve_falls_back_without_annotation(super_client):
    income = make_income()
    cuenta = make_cuenta(income)

    response = super_client.get(f'/api/accounting/incomes/{income.pk}/')

    assert response.status_code == 200
    assert response.data['has_collection_account'] is True
    assert response.data['collection_account_id'] == cuenta.pk
    assert response.data['collection_account_number'] == 'PA-KORE-001'


def test_cancelled_cuenta_frees_the_income(super_client):
    income = make_income()
    make_cuenta(income, status=Document.CommercialStatus.CANCELLED)

    response = super_client.get('/api/accounting/incomes/')

    row = _row(response, income.pk)
    assert row['has_collection_account'] is False
    assert row['collection_account_id'] is None


def test_liquid_income_carries_the_flag_too(super_client):
    liquid = make_income(kind=IncomeRecord.Kind.LIQUID)
    cuenta = make_cuenta(liquid)

    response = super_client.get('/api/accounting/incomes/?kind=liquid')

    row = _row(response, liquid.pk)
    assert row['has_collection_account'] is True
    assert row['collection_account_id'] == cuenta.pk
