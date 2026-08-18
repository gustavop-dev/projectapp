"""The bulk-settle endpoint: one abono POST distributed across several
expected incomes. Covers the 201 contract (refreshed parents + children +
the movement with its allocations), the 409 vanished-ids contract, the 400
business errors in Spanish, the serializer-level payload rules and the
payment_status filter reading shared children like any other liquid child.
"""
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

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


def detail_url(record):
    return f'/api/accounting/incomes/{record.pk}/detail/'


class TestIncomeDetailNamesTheMovement:
    """The reparto read from the income side, not the pocket's.

    Until now an income could only say how much it was paid; which movement
    paid it — and whether that payment was shared with other incomes — existed
    solely on the pocket ledger.
    """

    def test_a_shared_abono_names_the_whole_transfer_and_its_siblings(
        self, super_client,
    ):
        covered = make_expected()
        partial = make_expected(concept='Kore - Fase 3', total='300000.00')
        settle = super_client.post(
            BULK_SETTLE_URL,
            payload([(covered.pk, '500000.00'), (partial.pk, '100000.00')],
                    '600000.00'),
            format='json',
        )
        assert settle.status_code == 201, settle.data

        response = super_client.get(detail_url(covered))

        assert response.status_code == 200
        child = response.data['liquid'][0]
        movement = child['movement']
        assert movement['is_shared'] is True
        assert movement['allocation_count'] == 2
        # The distinction the ficha is after: the movement carries the WHOLE
        # transfer, the child carries only the part imputed to this income.
        assert movement['amount'] == '600000.00'
        assert child['total_amount'] == '500000.00'
        # And the sibling is nameable from here, which is the point of opening
        # the reparto from an income at all.
        assert [entry['concept'] for entry in movement['allocations']] == [
            'Kore - Fase 2', 'Kore - Fase 3',
        ]
        assert [entry['amount'] for entry in movement['allocations']] == [
            '500000.00', '100000.00',
        ]

    def test_a_single_income_abono_is_not_flagged_as_shared(
        self, super_client,
    ):
        alone = make_expected()
        settle = super_client.post(
            BULK_SETTLE_URL,
            payload([(alone.pk, '200000.00')], '200000.00'),
            format='json',
        )
        assert settle.status_code == 201, settle.data

        movement = super_client.get(
            detail_url(alone),
        ).data['liquid'][0]['movement']

        assert movement['is_shared'] is False
        assert movement['allocation_count'] == 1

    def test_a_child_that_never_touched_the_pocket_reports_no_movement(
        self, super_client,
    ):
        expected = make_expected()
        IncomeRecord.objects.create(
            concept='Liquidación a socios',
            kind=IncomeRecord.Kind.LIQUID,
            period_date='2026-08-15',
            total_amount=Decimal('500000.00'),
            gustavo_amount=Decimal('250000.00'),
            carlos_amount=Decimal('250000.00'),
            destination=IncomeRecord.Destination.PARTNERS,
            expected_income=expected,
        )

        child = super_client.get(detail_url(expected)).data['liquid'][0]

        # None, not an empty dict: "no pasó por el bolsillo" has to stay
        # distinguishable from "movimiento sin datos".
        assert child['movement'] is None
        assert child['total_amount'] == '500000.00'

    def test_the_detail_queries_do_not_scale_with_the_siblings(
        self, super_client,
    ):
        """An abono with three siblings must cost the same as one with two.

        Asserted as an equality between two shapes rather than a hardcoded
        number: the absolute drifts with any unrelated annotation, the
        equality only breaks when the prefetch actually regresses.
        """
        small = make_expected(concept='Chico')
        small_pair = make_expected(concept='Chico 2', total='100000.00')
        super_client.post(
            BULK_SETTLE_URL,
            payload([(small.pk, '500000.00'), (small_pair.pk, '100000.00')],
                    '600000.00'),
            format='json',
        )

        big = make_expected(concept='Grande')
        big_b = make_expected(concept='Grande 2', total='100000.00')
        big_c = make_expected(concept='Grande 3', total='100000.00')
        super_client.post(
            BULK_SETTLE_URL,
            payload(
                [(big.pk, '500000.00'), (big_b.pk, '100000.00'),
                 (big_c.pk, '100000.00')],
                '700000.00',
            ),
            format='json',
        )

        with CaptureQueriesContext(connection) as two_siblings:
            super_client.get(detail_url(small))
        with CaptureQueriesContext(connection) as three_siblings:
            super_client.get(detail_url(big))

        assert len(three_siblings) == len(two_siblings)


class TestIncomeListStaysLean:
    def test_the_list_row_does_not_carry_the_movement_payload(
        self, super_client,
    ):
        """The nested movement belongs to the detail endpoint only.

        `IncomeRecordSerializer` is shared with this list, the create/update
        responses and the MCP get_income handler; growing it would cost two
        queries per liquid row on every page to answer a question none of
        them ask.
        """
        expected = make_expected()
        super_client.post(
            BULK_SETTLE_URL,
            payload([(expected.pk, '500000.00')], '500000.00'),
            format='json',
        )

        rows = super_client.get(INCOMES_URL).data['results']

        assert rows, 'the list should return the abono rows'
        assert all('movement' not in row for row in rows)
        # The raw pk stays, though — the expenses panel reads it.
        assert any(row.get('pocket_movement') for row in rows)
