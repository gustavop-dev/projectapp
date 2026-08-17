"""The bulk-settle endpoint: one abono POST distributed across several
expected incomes. Covers the 201 contract (refreshed parents + children +
the movement with its allocations), the 409 vanished-ids contract, the 400
business errors in Spanish, the serializer-level payload rules and the
payment_status filter reading shared children like any other liquid child.
"""
from decimal import Decimal

import pytest

from content.models import IncomeRecord, PocketMovement

pytestmark = pytest.mark.django_db

BULK_SETTLE_URL = '/api/accounting/incomes/bulk-settle/'
INCOMES_URL = '/api/accounting/incomes/'


def make_expected(concept='Kore - Fase 2', total='500000.00', **overrides):
    half = (Decimal(total) / 2).quantize(Decimal('0.01'))
    fields = {
        'concept': concept,
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-06-01',
        'total_amount': Decimal(total),
        'gustavo_amount': half,
        'carlos_amount': Decimal(total) - half,
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def payload(allocations, total, **overrides):
    data = {
        'allocations': [
            {'income_id': pk, 'amount': str(amount)}
            for pk, amount in allocations
        ],
        'total_amount': str(total),
        'period_date': '2026-08-15',
        'notes': 'Transferencia Bancolombia',
    }
    data.update(overrides)
    return data


class TestBulkSettleEndpoint:
    def test_registers_the_abono_and_returns_the_refreshed_rows(
        self, super_client,
    ):
        first = make_expected()
        second = make_expected(concept='Kore - Fase 3', total='300000.00')

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(first.pk, '500000.00'), (second.pk, '100000.00')],
                    '600000.00'),
            format='json',
        )

        assert response.status_code == 201, response.data
        assert response.data['updated'] == 2
        by_id = {row['id']: row for row in response.data['results']}
        assert by_id[first.pk]['payment_status'] == 'paid'
        assert by_id[second.pk]['payment_status'] == 'partial'
        assert response.data['movement']['amount'] == '600000.00'
        assert len(response.data['movement']['allocations']) == 2

    def test_the_results_carry_the_liquid_children(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '200000.00')], '200000.00'),
            format='json',
        )

        assert response.status_code == 201, response.data
        children = [
            row for row in response.data['results']
            if row['kind'] == 'liquid'
        ]
        assert len(children) == 1
        assert children[0]['expected_income'] == parent.pk
        assert children[0]['total_amount'] == '200000.00'

    def test_the_credit_child_travels_in_the_results(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '500000.00')], '650000.00'),
            format='json',
        )

        assert response.status_code == 201, response.data
        credits = [
            row for row in response.data['results']
            if row['concept'].startswith('Saldo a favor')
        ]
        assert len(credits) == 1
        assert credits[0]['expected_income'] is None
        assert credits[0]['total_amount'] == '150000.00'

    def test_a_vanished_id_answers_409_and_writes_nothing(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '100000.00'), (99999, '100000.00')],
                    '200000.00'),
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'records_not_found'
        assert response.data['missing_ids'] == [99999]
        assert PocketMovement.objects.count() == 0

    def test_a_business_rule_answers_400_in_spanish(self, super_client):
        parent = make_expected(total='300000.00')

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '400000.00')], '400000.00'),
            format='json',
        )

        assert response.status_code == 400
        assert 'supera su saldo pendiente' in response.data['error']
        assert PocketMovement.objects.count() == 0

    def test_requires_a_superuser(self, api_client):
        response = api_client.post(
            BULK_SETTLE_URL, payload([(1, '100.00')], '100.00'), format='json',
        )

        assert response.status_code in (401, 403)


class TestBulkSettlePayloadRules:
    def test_rejects_a_repeated_income(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '100000.00'), (parent.pk, '100000.00')],
                    '200000.00'),
            format='json',
        )

        assert response.status_code == 400
        assert 'repetidos' in str(response.data['allocations'])

    def test_rejects_a_distribution_above_the_total(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '300000.00')], '200000.00'),
            format='json',
        )

        assert response.status_code == 400
        assert 'no puede superar' in str(response.data['total_amount'])

    def test_rejects_an_empty_distribution(self, super_client):
        response = super_client.post(
            BULK_SETTLE_URL, payload([], '200000.00'), format='json',
        )

        assert response.status_code == 400
        assert 'allocations' in response.data

    def test_rejects_a_zero_allocation(self, super_client):
        parent = make_expected()

        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(parent.pk, '0.00')], '100000.00'),
            format='json',
        )

        assert response.status_code == 400
        assert 'allocations' in response.data


class TestPaymentStatusAfterAbono:
    def test_the_filter_reads_shared_children_like_any_other(
        self, super_client,
    ):
        covered = make_expected()
        partial = make_expected(concept='Kore - Fase 3', total='300000.00')
        untouched = make_expected(concept='Kore - Fase 4', total='200000.00')
        response = super_client.post(
            BULK_SETTLE_URL,
            payload([(covered.pk, '500000.00'), (partial.pk, '100000.00')],
                    '600000.00'),
            format='json',
        )
        assert response.status_code == 201, response.data

        paid = super_client.get(INCOMES_URL, {'payment_status': 'paid'})
        partial_rows = super_client.get(
            INCOMES_URL, {'payment_status': 'partial'},
        )
        pending = super_client.get(INCOMES_URL, {'payment_status': 'pending'})

        assert [row['id'] for row in paid.data['results']] == [covered.pk]
        assert [row['id'] for row in partial_rows.data['results']] == [
            partial.pk,
        ]
        assert [row['id'] for row in pending.data['results']] == [
            untouched.pk,
        ]
