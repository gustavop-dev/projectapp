"""API tests for the covered period of hosting incomes.

A hosting income is a service window, not a point payment: with
``origin=hosting`` the write serializer demands ``period_start``,
``period_end`` and ``period_cadence``, and derives ``period_date`` from the
start so every ordering, KPI and filter keeps its single axis. Legacy hosting
rows predate the fields — a partial PATCH that touches neither the origin nor
the period must keep working, while the panel form always sends ``origin``
and therefore completes the period on the first edit (gradual backfill).
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from content.models import IncomeRecord
from content.services import accounting_service

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mute_notifications():
    with patch.object(accounting_service, '_notify'):
        yield


def hosting_payload(**overrides):
    payload = {
        'concept': 'Acme - Hosting anual',
        'kind': 'expected',
        'origin': 'hosting',
        'period_start': '2026-08-15',
        'period_end': '2027-08-14',
        'period_cadence': 'annual',
        'total_amount': '550000.00',
    }
    payload.update(overrides)
    return payload


CREATE_URL = '/api/accounting/incomes/create/'


def record_url(record):
    return f'/api/accounting/incomes/{record.pk}/update/'


class TestCreateHosting:
    def test_persists_the_window_and_derives_period_date_from_its_start(
        self, super_client,
    ):
        response = super_client.post(CREATE_URL, hosting_payload(), format='json')

        assert response.status_code == 201, response.data
        record = IncomeRecord.objects.get()
        assert record.period_start == date(2026, 8, 15)
        assert record.period_end == date(2027, 8, 14)
        assert record.period_cadence == 'annual'
        assert record.period_date == date(2026, 8, 15)

    def test_month_shorthand_starts_the_window_on_day_one(self, super_client):
        """The exact-day toggle applies to the start: 'YYYY-MM' → day 1."""
        response = super_client.post(
            CREATE_URL,
            hosting_payload(period_start='2026-08', period_end='2026-09-14'),
            format='json',
        )

        assert response.status_code == 201, response.data
        record = IncomeRecord.objects.get()
        assert record.period_start == date(2026, 8, 1)
        assert record.period_date == date(2026, 8, 1)

    def test_missing_window_is_rejected_field_by_field(self, super_client):
        no_start = super_client.post(
            CREATE_URL,
            hosting_payload(period_start=None, period_end=None, period_cadence=''),
            format='json',
        )
        assert no_start.status_code == 400
        assert 'period_start' in no_start.data

        no_end = super_client.post(
            CREATE_URL, hosting_payload(period_end=None), format='json',
        )
        assert no_end.status_code == 400
        assert 'period_end' in no_end.data

        no_cadence = super_client.post(
            CREATE_URL, hosting_payload(period_cadence=''), format='json',
        )
        assert no_cadence.status_code == 400
        assert 'period_cadence' in no_cadence.data

    def test_the_end_must_come_after_the_start(self, super_client):
        response = super_client.post(
            CREATE_URL,
            hosting_payload(period_start='2026-08-15', period_end='2026-08-15'),
            format='json',
        )

        assert response.status_code == 400
        assert 'period_end' in response.data

    def test_a_cadence_outside_the_catalog_is_rejected(self, super_client):
        response = super_client.post(
            CREATE_URL, hosting_payload(period_cadence='weekly'), format='json',
        )

        assert response.status_code == 400
        assert 'period_cadence' in response.data


class TestOtherOriginsKeepTheSingleDate:
    def test_a_development_income_needs_no_window(self, super_client):
        response = super_client.post(
            CREATE_URL,
            {
                'concept': 'Kore - Inicio 40%',
                'kind': 'expected',
                'origin': 'development',
                'period_date': '2026-02',
                'total_amount': '1160000.00',
            },
            format='json',
        )

        assert response.status_code == 201, response.data
        record = IncomeRecord.objects.get()
        assert record.period_start is None
        assert record.period_cadence == ''

    def test_a_stray_window_on_a_non_hosting_income_is_cleared(self, super_client):
        response = super_client.post(
            CREATE_URL,
            {
                'concept': 'Kore - Inicio 40%',
                'kind': 'expected',
                'origin': 'development',
                'period_date': '2026-02',
                'period_start': '2026-02-01',
                'period_end': '2026-03-01',
                'period_cadence': 'monthly',
                'total_amount': '1160000.00',
            },
            format='json',
        )

        assert response.status_code == 201, response.data
        record = IncomeRecord.objects.get()
        assert record.period_start is None
        assert record.period_end is None
        assert record.period_cadence == ''

    def test_a_non_hosting_income_still_requires_its_date(self, super_client):
        response = super_client.post(
            CREATE_URL,
            {
                'concept': 'Kore - Inicio 40%',
                'kind': 'expected',
                'total_amount': '1160000.00',
                # Sent so the refusal under test is the date's and not the
                # origin's, which is required on its own account.
                'origin': 'development',
            },
            format='json',
        )

        assert response.status_code == 400
        assert 'period_date' in response.data


class TestUpdate:
    def test_switching_away_from_hosting_drops_the_window(
        self, super_client, make_income,
    ):
        income = make_income(
            origin=IncomeRecord.Origin.HOSTING,
            period_start=date(2026, 8, 15),
            period_end=date(2027, 8, 14),
            period_cadence='annual',
        )

        response = super_client.patch(
            record_url(income), {'origin': 'development'}, format='json',
        )

        assert response.status_code == 200, response.data
        income.refresh_from_db()
        assert income.period_start is None
        assert income.period_end is None
        assert income.period_cadence == ''

    def test_editing_a_legacy_hosting_from_the_panel_demands_the_window(
        self, super_client, make_income,
    ):
        """The panel form always sends `origin`: gradual backfill on edit."""
        income = make_income(origin=IncomeRecord.Origin.HOSTING)

        response = super_client.patch(
            record_url(income),
            {'origin': 'hosting', 'total_amount': '1200000.00'},
            format='json',
        )

        assert response.status_code == 400
        assert 'period_start' in response.data

    def test_a_partial_patch_that_skips_the_period_keeps_working(
        self, super_client, make_income,
    ):
        """MCP `update_income` and bulk actions patch without `origin`."""
        income = make_income(origin=IncomeRecord.Origin.HOSTING)

        response = super_client.patch(
            record_url(income), {'total_amount': '1200000.00'}, format='json',
        )

        assert response.status_code == 200, response.data

    def test_moving_the_window_moves_period_date_with_it(
        self, super_client, make_income,
    ):
        income = make_income(
            origin=IncomeRecord.Origin.HOSTING,
            period_date=date(2026, 8, 15),
            period_start=date(2026, 8, 15),
            period_end=date(2027, 8, 14),
            period_cadence='annual',
        )

        response = super_client.patch(
            record_url(income),
            {'period_start': '2026-09-01', 'period_end': '2027-08-31'},
            format='json',
        )

        assert response.status_code == 200, response.data
        income.refresh_from_db()
        assert income.period_date == date(2026, 9, 1)


class TestRead:
    def test_the_list_exposes_the_window_and_its_label(
        self, super_client, make_income,
    ):
        make_income(
            origin=IncomeRecord.Origin.HOSTING,
            period_start=date(2026, 8, 15),
            period_end=date(2027, 8, 14),
            period_cadence='annual',
        )

        row = super_client.get('/api/accounting/incomes/').data['results'][0]

        assert row['period_start'] == '2026-08-15'
        assert row['period_end'] == '2027-08-14'
        assert row['period_cadence'] == 'annual'
        assert row['period_cadence_label'] == 'Anual'

    def test_no_cadence_reads_as_an_absence_not_a_blank(
        self, super_client, make_income,
    ):
        make_income()

        row = super_client.get('/api/accounting/incomes/').data['results'][0]

        assert row['period_cadence_label'] is None
