"""API tests for the accounting CSV/XLSX export endpoints."""
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from content.models import CardBalanceSnapshot, IncomeRecord


def csv_lines(response):
    body = response.content.decode('utf-8')
    assert body.startswith('\ufeff')
    return [line for line in body.lstrip('\ufeff').splitlines() if line]


@pytest.mark.django_db
class TestExportRecords:
    def test_requires_superuser(self, admin_client):
        response = admin_client.get('/api/accounting/export/?section=income')
        assert response.status_code == 403

    def test_invalid_section_returns_400(self, super_client):
        response = super_client.get('/api/accounting/export/?section=nope')
        assert response.status_code == 400
        assert response.data['code'] == 'invalid_section'

    def test_invalid_format_returns_400(self, super_client):
        response = super_client.get(
            '/api/accounting/export/?section=income&file_format=pdf',
        )
        assert response.status_code == 400
        assert response.data['code'] == 'invalid_format'

    def test_csv_headers_in_spanish_and_bom(self, super_client, make_income):
        make_income(concept='Kore - Inicio 40%')
        response = super_client.get('/api/accounting/export/?section=income')
        assert response.status_code == 200
        assert response['Content-Type'].startswith('text/csv')
        assert 'contabilidad_income_' in response['Content-Disposition']
        lines = csv_lines(response)
        assert lines[0].split(',')[:4] == ['Concepto', 'Tipo', 'Contabilidad', 'Mes']
        assert 'Kore - Inicio 40%' in lines[1]

    def test_csv_respects_filters(self, super_client, make_income):
        make_income(
            concept='Company liquid', kind=IncomeRecord.Kind.LIQUID,
        )
        make_income(
            concept='Personal Tavo', kind=IncomeRecord.Kind.LIQUID,
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('100.00'),
            gustavo_amount=Decimal('100.00'),
            carlos_amount=Decimal('0.00'),
        )
        response = super_client.get(
            '/api/accounting/export/?section=income&kind=liquid&ledger=gustavo',
        )
        lines = csv_lines(response)
        assert len(lines) == 2  # header + 1 row
        assert 'Personal Tavo' in lines[1]

    def test_choice_filter_accepts_comma_multi(self, super_client, make_income):
        make_income(concept='A', kind=IncomeRecord.Kind.LIQUID)
        make_income(
            concept='B', kind=IncomeRecord.Kind.LIQUID,
            ledger=IncomeRecord.Ledger.CARLOS,
            total_amount=Decimal('10.00'),
            gustavo_amount=Decimal('0.00'),
            carlos_amount=Decimal('10.00'),
        )
        make_income(
            concept='C', kind=IncomeRecord.Kind.LIQUID,
            ledger=IncomeRecord.Ledger.GUSTAVO,
            total_amount=Decimal('10.00'),
            gustavo_amount=Decimal('10.00'),
            carlos_amount=Decimal('0.00'),
        )
        response = super_client.get(
            '/api/accounting/export/?section=income&ledger=gustavo,carlos',
        )
        lines = csv_lines(response)
        assert len(lines) == 3
        assert all('A,' not in line for line in lines[1:])

    def test_empty_export_has_only_header(self, super_client):
        response = super_client.get('/api/accounting/export/?section=expense')
        lines = csv_lines(response)
        assert len(lines) == 1

    def test_xlsx_export_opens_and_has_rows(self, super_client, make_income):
        make_income(concept='Ingreso XLSX')
        response = super_client.get(
            '/api/accounting/export/?section=income&file_format=xlsx',
        )
        assert response.status_code == 200
        assert response['Content-Disposition'].endswith('.xlsx"')
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook['Ingresos']
        assert sheet.cell(row=1, column=1).value == 'Concepto'
        assert sheet.cell(row=2, column=1).value == 'Ingreso XLSX'


@pytest.mark.django_db
class TestExportWorkbook:
    def test_requires_superuser(self, admin_client):
        response = admin_client.get('/api/accounting/export/workbook/')
        assert response.status_code == 403

    def test_invalid_year_returns_400(self, super_client):
        response = super_client.get('/api/accounting/export/workbook/?year=x')
        assert response.status_code == 400

    def test_workbook_contains_summary_and_section_sheets(
        self, super_client, make_income, make_expense,
    ):
        make_income(kind=IncomeRecord.Kind.LIQUID, concept='Ingreso 2026')
        make_expense(concept='Gasto 2026')
        CardBalanceSnapshot.objects.create(
            snapshot_date=date(2026, 6, 17), card_name='T.C 0064',
            available_amount=Decimal('100.00'), debt_amount=Decimal('900.00'),
        )
        response = super_client.get(
            '/api/accounting/export/workbook/?year=2026',
        )
        assert response.status_code == 200
        workbook = load_workbook(BytesIO(response.content))
        assert workbook.sheetnames == [
            'Resumen', 'Ingresos', 'Gastos', 'Hostings', 'Bolsillo',
            'Recurrentes', 'Ads', 'Tarjetas',
        ]
        assert workbook['Resumen'].cell(row=1, column=1).value == 'Resumen 2026'
        assert workbook['Tarjetas'].cell(row=2, column=1).value == 'T.C 0064'

    def test_workbook_scopes_sections_to_year(self, super_client, make_income):
        make_income(
            kind=IncomeRecord.Kind.LIQUID, concept='Viejo',
            period_date=date(2025, 5, 1),
        )
        response = super_client.get(
            '/api/accounting/export/workbook/?year=2026',
        )
        workbook = load_workbook(BytesIO(response.content))
        assert workbook['Ingresos'].max_row == 1
