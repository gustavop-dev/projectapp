"""Tests for the import_accounting_2026 management command."""
import json
from decimal import Decimal

import pytest
from django.core import mail
from django.core.management import call_command

from content.models import (
    AdsSpendRecord,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)

FIXTURE = {
    'incomes_expected': [
        {
            'concept': 'Kore - Inicio 40%', 'period': '2026-02',
            'total_amount': '1160000.00', 'gustavo_amount': '580000.00',
            'carlos_amount': '580000.00', 'destination': 'partners',
            'notes': '',
        },
    ],
    'incomes_liquid': [
        {
            'concept': 'Kore - Inicio 40%', 'period': '2026-02',
            'total_amount': '1160000.00', 'gustavo_amount': '580000.00',
            'carlos_amount': '580000.00', 'destination': 'partners',
            'notes': '',
        },
        {
            'concept': 'Vastago (Fase 1) - Inicio 40%', 'period': '2026-04',
            'total_amount': '2123000.00', 'gustavo_amount': '0.00',
            'carlos_amount': '0.00', 'destination': 'pocket',
            'notes': 'Bolsillo ProjectApp según el Excel',
        },
    ],
    'expenses': [
        {
            'concept': 'Claude Code Marzo', 'period': '2026-03',
            'total_amount': '400000.00', 'gustavo_amount': '200000.00',
            'carlos_amount': '200000.00', 'category': 'business',
            'paid_from': 'partners', 'notes': '',
        },
    ],
    'hostings': [
        {
            'client_name': 'German - Kore', 'domain_url': 'https://korehealths.com/',
            'monthly_value': '91667.00', 'payment_modality': 'semiannual',
            'benefit': '', 'valid_from': '2026-03-02', 'valid_to': '2026-09-02',
            'cycles_count': 1, 'payment_per_cycle': '1100000.00',
            'total_paid': '1100000.00', 'is_active': True, 'notes': '',
        },
    ],
    'pocket_movements': [
        {
            'concept': 'Vastago (Fase 1) - Inicio 40%',
            'movement_date': '2026-04-29', 'direction': 'in',
            'amount': '2123000.00', 'notes': '',
        },
        {
            'concept': 'Registro & Matricula Mercantil',
            'movement_date': '2026-04-29', 'direction': 'out',
            'amount': '63000.00', 'notes': '',
        },
    ],
    'recurring_payments': [
        {
            'name': 'Claude Code 20x', 'price': '200.00', 'currency': 'USD',
            'cop_equivalent': '800000.00', 'payment_method': 'credit_card',
            'frequency': 'monthly', 'billing_day': 8, 'cost_type': 'fixed',
            'is_active': True, 'notes': '',
        },
    ],
    'ads_spend': [
        {
            'spend_date': '2026-01-17', 'platform': 'facebook',
            'origin_card': 'T.C 0655', 'amount': '146103.00', 'notes': '',
        },
        {
            'spend_date': '2026-04-08', 'platform': 'facebook',
            'origin_card': 'T.C 0655', 'amount': '66645.00', 'notes': '',
        },
        {
            'spend_date': '2026-04-08', 'platform': 'facebook',
            'origin_card': 'T.C 0655', 'amount': '66645.00',
            'notes': 'Segundo cargo del mismo día',
        },
    ],
    'card_snapshots': [
        {
            'snapshot_date': '2026-07-01', 'card_name': 'T.C 0064',
            'available_amount': '3849046.00', 'debt_amount': '4150954.00',
            'notes': '',
        },
    ],
}


@pytest.fixture
def fixture_file(tmp_path):
    path = tmp_path / 'accounting_2026.json'
    path.write_text(json.dumps(FIXTURE), encoding='utf-8')
    return str(path)


@pytest.mark.django_db
class TestImportAccounting2026:
    def test_imports_every_section(self, fixture_file):
        call_command('import_accounting_2026', '--file', fixture_file)
        assert IncomeRecord.objects.filter(kind='expected').count() == 1
        assert IncomeRecord.objects.filter(kind='liquid').count() == 2
        assert ExpenseRecord.objects.count() == 1
        assert HostingRecord.objects.count() == 1
        assert PocketMovement.objects.count() == 2
        assert RecurringPayment.objects.count() == 1
        # Duplicated ads rows (same date/amount/card) are both kept.
        assert AdsSpendRecord.objects.count() == 3

    def test_rerun_creates_zero_duplicates(self, fixture_file):
        call_command('import_accounting_2026', '--file', fixture_file)
        call_command('import_accounting_2026', '--file', fixture_file)
        assert IncomeRecord.objects.count() == 3
        assert AdsSpendRecord.objects.count() == 3
        assert PocketMovement.objects.count() == 2

    def test_edited_amount_updates_existing_row(self, fixture_file, tmp_path):
        call_command('import_accounting_2026', '--file', fixture_file)
        edited = json.loads(json.dumps(FIXTURE))
        edited['incomes_expected'][0]['total_amount'] = '1200000.00'
        edited_path = tmp_path / 'edited.json'
        edited_path.write_text(json.dumps(edited), encoding='utf-8')

        call_command('import_accounting_2026', '--file', str(edited_path))
        income = IncomeRecord.objects.get(kind='expected')
        assert income.total_amount == Decimal('1200000.00')
        assert IncomeRecord.objects.filter(kind='expected').count() == 1

    def test_links_liquid_to_expected_by_concept(self, fixture_file):
        call_command('import_accounting_2026', '--file', fixture_file)
        liquid = IncomeRecord.objects.get(
            kind='liquid', concept='Kore - Inicio 40%',
        )
        assert liquid.expected_income is not None
        assert liquid.expected_income.kind == 'expected'

    def test_links_pocket_income_to_ledger_movement(self, fixture_file):
        call_command('import_accounting_2026', '--file', fixture_file)
        pocket_income = IncomeRecord.objects.get(destination='pocket')
        assert pocket_income.pocket_movement is not None
        assert pocket_income.pocket_movement.amount == Decimal('2123000.00')

    def test_no_notification_emails_are_sent(
        self, fixture_file, accounting_settings,
    ):
        mail.outbox = []
        call_command('import_accounting_2026', '--file', fixture_file)
        assert mail.outbox == []

    def test_dry_run_writes_nothing(self, fixture_file):
        call_command('import_accounting_2026', '--file', fixture_file, '--dry-run')
        assert IncomeRecord.objects.count() == 0
        assert PocketMovement.objects.count() == 0
