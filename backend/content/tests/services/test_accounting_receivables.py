"""Manual accounts-receivable forecast behavior."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import AccountingChangeLog, IncomeRecord, Ledger
from content.services import accounting_service, accounting_settlement_service


@pytest.mark.django_db
def test_green_forecast_uses_original_amount_for_partially_paid_income(make_income):
    expected = make_income(
        total_amount=Decimal('1000.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )
    make_income(
        kind=IncomeRecord.Kind.LIQUID,
        total_amount=Decimal('400.00'),
        expected_income=expected,
    )

    summary = accounting_service.receivables_summary()

    assert summary['high_total'] == Decimal('1000.00')
    assert summary['by_confidence']['high']['paid_amount'] == Decimal('400.00')
    assert summary['by_confidence']['high']['pending_amount'] == Decimal('600.00')


@pytest.mark.django_db
def test_forecast_groups_selected_income_without_confidence(make_income):
    make_income(
        total_amount=Decimal('750.00'),
        is_receivable_candidate=True,
        collection_confidence='',
    )

    summary = accounting_service.receivables_summary()

    assert summary['by_confidence']['unclassified']['count'] == 1
    assert summary['by_confidence']['unclassified']['total_amount'] == Decimal('750.00')


@pytest.mark.django_db
def test_unselected_high_confidence_does_not_contribute_to_card(make_income):
    make_income(
        total_amount=Decimal('820.00'),
        is_receivable_candidate=False,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )

    summary = accounting_service.receivables_summary()

    assert summary['high_total'] == Decimal('0')


@pytest.mark.django_db
def test_forecast_excludes_fully_paid_candidate(make_income):
    expected = make_income(
        total_amount=Decimal('500.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )
    make_income(
        kind=IncomeRecord.Kind.LIQUID,
        total_amount=Decimal('500.00'),
        expected_income=expected,
    )

    summary = accounting_service.receivables_summary()

    assert summary['selected_count'] == 0
    assert summary['high_total'] == Decimal('0')


@pytest.mark.django_db
def test_fully_paid_income_cannot_be_selected_again(super_client, make_income):
    """Falla si un cobro cerrado vuelve a inflar la previsión manual."""
    income = make_income(
        total_amount=Decimal('500.00'),
        gustavo_amount=Decimal('250.00'),
        carlos_amount=Decimal('250.00'),
    )
    make_income(
        kind=IncomeRecord.Kind.LIQUID,
        total_amount=Decimal('500.00'),
        expected_income=income,
    )

    response = super_client.patch(
        f'/api/accounting/incomes/{income.pk}/update/',
        {'is_receivable_candidate': True},
        format='json',
    )

    income.refresh_from_db()
    assert response.status_code == 400
    assert 'is_receivable_candidate' in response.data
    assert income.is_receivable_candidate is False


@pytest.mark.django_db
def test_fully_paid_income_cannot_receive_collection_confidence(
    super_client, make_income,
):
    """Falla si asignar un color reabre un cobro cerrado en la previsión."""
    income = make_income(
        total_amount=Decimal('500.00'),
        gustavo_amount=Decimal('250.00'),
        carlos_amount=Decimal('250.00'),
    )
    make_income(
        kind=IncomeRecord.Kind.LIQUID,
        total_amount=Decimal('500.00'),
        expected_income=income,
    )

    response = super_client.patch(
        f'/api/accounting/incomes/{income.pk}/update/',
        {'collection_confidence': IncomeRecord.CollectionConfidence.HIGH},
        format='json',
    )

    income.refresh_from_db()
    assert response.status_code == 400
    assert 'is_receivable_candidate' in response.data
    assert income.is_receivable_candidate is False
    assert income.collection_confidence == ''


@pytest.mark.django_db
def test_dashboard_green_forecast_ignores_selected_year(make_income):
    make_income(
        period_date=date(2024, 1, 1),
        total_amount=Decimal('900.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )

    summary = accounting_service.dashboard_summary(2026)

    assert summary['receivables']['high_total'] == Decimal('900.00')


@pytest.mark.django_db
def test_confidence_assignment_persists_forecast_with_notification(
    super_client, make_income,
):
    income = make_income()

    with patch.object(accounting_service, '_notify') as notify:
        response = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {'collection_confidence': 'high'},
            format='json',
        )

    assert response.status_code == 200, response.data
    assert response.data['is_receivable_candidate'] is True
    assert response.data['collection_confidence_label'] == 'Cobro muy probable'
    log = AccountingChangeLog.objects.filter(
        entity_type=AccountingChangeLog.EntityType.INCOME,
        object_id=income.pk,
        action=AccountingChangeLog.Action.UPDATED,
    ).get()
    assert {change['field'] for change in log.changes} == {
        'is_receivable_candidate', 'collection_confidence',
    }
    notify.assert_called_once_with(log)


@pytest.mark.django_db
def test_candidate_can_remain_selected_without_confidence(super_client, make_income):
    income = make_income()

    with patch.object(accounting_service, '_notify'):
        response = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {'is_receivable_candidate': True},
            format='json',
        )

    assert response.status_code == 200, response.data
    assert response.data['is_receivable_candidate'] is True
    assert response.data['collection_confidence'] == ''


@pytest.mark.django_db
def test_manual_deselection_preserves_confidence(super_client, make_income):
    income = make_income(
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.MEDIUM,
    )

    with patch.object(accounting_service, '_notify'):
        response = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {'is_receivable_candidate': False},
            format='json',
        )

    assert response.status_code == 200, response.data
    assert response.data['is_receivable_candidate'] is False
    assert response.data['collection_confidence'] == 'medium'


@pytest.mark.django_db
def test_personal_income_cannot_be_selected(super_client, make_income):
    income = make_income(ledger=Ledger.GUSTAVO)

    response = super_client.patch(
        f'/api/accounting/incomes/{income.pk}/update/',
        {'is_receivable_candidate': True},
        format='json',
    )

    assert response.status_code == 400
    assert 'is_receivable_candidate' in response.data


@pytest.mark.django_db
def test_kind_change_preserves_confidence_history(
    super_client, make_income,
):
    income = make_income(
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.LOW,
    )

    with patch.object(accounting_service, '_notify'):
        response = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {'kind': IncomeRecord.Kind.LOST},
            format='json',
        )

    assert response.status_code == 200, response.data
    assert response.data['is_receivable_candidate'] is False
    assert response.data['collection_confidence'] == 'low'


@pytest.mark.django_db
def test_ledger_change_deselects_candidate(super_client, make_income):
    income = make_income(
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )

    with patch.object(accounting_service, '_notify'):
        response = super_client.patch(
            f'/api/accounting/incomes/{income.pk}/update/',
            {
                'ledger': Ledger.CARLOS,
                'gustavo_amount': Decimal('0.00'),
                'carlos_amount': income.total_amount,
            },
            format='json',
        )

    assert response.status_code == 200, response.data
    assert response.data['is_receivable_candidate'] is False
    assert response.data['collection_confidence'] == 'high'


@pytest.mark.django_db
def test_receivables_endpoint_returns_only_open_company_expected_rows(
    super_client, make_income,
):
    make_income(concept='Empresa abierta')
    make_income(concept='Personal', ledger=Ledger.CARLOS)
    make_income(concept='Líquido', kind=IncomeRecord.Kind.LIQUID)
    paid_expected = make_income(concept='Empresa pagada')
    make_income(
        concept='Pago completo', kind=IncomeRecord.Kind.LIQUID,
        expected_income=paid_expected, total_amount=paid_expected.total_amount,
    )

    response = super_client.get('/api/accounting/receivables/')

    assert response.status_code == 200
    assert [row['concept'] for row in response.data['results']] == ['Empresa abierta']
    assert response.data['summary']['selected_count'] == 0


@pytest.mark.django_db
def test_receivables_endpoint_rejects_non_superuser(admin_client):
    response = admin_client.get('/api/accounting/receivables/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_full_single_settlement_deselects_forecast(superuser, make_income):
    income = make_income(
        total_amount=Decimal('1000.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.HIGH,
    )

    with patch.object(accounting_service, '_notify'):
        accounting_settlement_service.settle_expected_income(
            income,
            {
                'concept': income.concept,
                'period_date': date(2026, 9, 3),
                'destination': IncomeRecord.Destination.PARTNERS,
                'total_amount': Decimal('1000.00'),
                'notes': '',
                'deductions': [],
                'expected_incomes': [],
            },
            superuser,
        )

    income.refresh_from_db()
    assert income.is_receivable_candidate is False
    assert income.collection_confidence == IncomeRecord.CollectionConfidence.HIGH


@pytest.mark.django_db
def test_full_bulk_settlement_deselects_forecast(superuser, make_income):
    income = make_income(
        total_amount=Decimal('1000.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.MEDIUM,
    )

    with patch.object(accounting_service, '_notify'):
        accounting_settlement_service.bulk_settle_expected_incomes(
            {
                'allocations': [
                    {'income_id': income.pk, 'amount': Decimal('1000.00')},
                ],
                'total_amount': Decimal('1000.00'),
                'period_date': date(2026, 9, 3),
                'notes': '',
            },
            superuser,
        )

    income.refresh_from_db()
    assert income.is_receivable_candidate is False


@pytest.mark.django_db
def test_partial_settlement_keeps_forecast_selected(superuser, make_income):
    income = make_income(
        total_amount=Decimal('1000.00'),
        is_receivable_candidate=True,
        collection_confidence=IncomeRecord.CollectionConfidence.LOW,
    )

    with patch.object(accounting_service, '_notify'):
        accounting_settlement_service.settle_expected_income(
            income,
            {
                'concept': income.concept,
                'period_date': date(2026, 9, 3),
                'destination': IncomeRecord.Destination.PARTNERS,
                'total_amount': Decimal('400.00'),
                'notes': '',
                'deductions': [],
                'expected_incomes': [],
            },
            superuser,
        )

    income.refresh_from_db()
    assert income.is_receivable_candidate is True
