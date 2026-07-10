"""CSV/XLSX export for the accounting module.

Sections mirror the `_ENTITIES` keys of content.views.accounting; each
one declares its Spanish headers and how to read every cell from a
record (field name or callable). Search parity note: server-side `q`
uses icontains over the section's search_fields, matching the panel's
client-side substring filter closely enough for exports.
"""
import csv
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from content.services.accounting_service import dashboard_summary
from content.utils import today_bogota

MONEY_FORMAT = '#,##0'
HEADER_FONT = Font(bold=True)

EXPORT_SECTIONS = {
    'income': {
        'title': 'Ingresos',
        'columns': [
            ('Concepto', 'concept'),
            ('Tipo', lambda r: r.get_kind_display()),
            ('Contabilidad', lambda r: r.get_ledger_display()),
            ('Mes', 'period_date'),
            ('Total', 'total_amount'),
            ('Gustavo', 'gustavo_amount'),
            ('Carlos', 'carlos_amount'),
            ('Destino', lambda r: r.get_destination_display()),
            ('Notas', 'notes'),
        ],
    },
    'expense': {
        'title': 'Gastos',
        'columns': [
            ('Concepto', 'concept'),
            ('Categoría', lambda r: r.get_category_display()),
            ('Contabilidad', lambda r: r.get_ledger_display()),
            ('Mes', 'period_date'),
            ('Total', 'total_amount'),
            ('Gustavo', 'gustavo_amount'),
            ('Carlos', 'carlos_amount'),
            ('Notas', 'notes'),
        ],
    },
    'hosting': {
        'title': 'Hostings',
        'columns': [
            ('Cliente', 'client_name'),
            ('Dominio', 'domain_url'),
            ('Valor mensual', 'monthly_value'),
            ('Modalidad', lambda r: r.get_payment_modality_display()),
            ('Vigente desde', 'valid_from'),
            ('Vigente hasta', 'valid_to'),
            ('Ciclos', 'cycles_count'),
            ('Pago por ciclo', 'payment_per_cycle'),
            ('Total pagado', 'total_paid'),
            ('Activo', lambda r: 'Sí' if r.is_active else 'No'),
            ('Notas', 'notes'),
        ],
    },
    'pocket': {
        'title': 'Bolsillo',
        'columns': [
            ('Concepto', 'concept'),
            ('Fecha', 'movement_date'),
            ('Tipo', lambda r: r.get_direction_display()),
            ('Valor', 'amount'),
            ('Notas', 'notes'),
        ],
    },
    'recurring': {
        'title': 'Recurrentes',
        'columns': [
            ('Nombre', 'name'),
            ('Precio', 'price'),
            ('Moneda', 'currency'),
            ('Equivalente COP', 'cop_equivalent'),
            ('Método de pago', lambda r: r.get_payment_method_display()),
            ('Frecuencia', lambda r: r.get_frequency_display()),
            ('Día de cobro', 'billing_day'),
            ('Tipo de costo', lambda r: r.get_cost_type_display()),
            ('Activo', lambda r: 'Sí' if r.is_active else 'No'),
            ('Notas', 'notes'),
        ],
    },
    'ads': {
        'title': 'Ads',
        'columns': [
            ('Fecha', 'spend_date'),
            ('Plataforma', lambda r: r.get_platform_display()),
            ('Tarjeta origen', 'origin_card'),
            ('Valor', 'amount'),
            ('Notas', 'notes'),
        ],
    },
    'card_snapshot': {
        'title': 'Tarjetas',
        'columns': [
            ('Tarjeta', 'card_name'),
            ('Fecha', 'snapshot_date'),
            ('Disponible', 'available_amount'),
            ('Deuda', 'debt_amount'),
            ('Notas', 'notes'),
        ],
    },
}


def _cell(record, accessor):
    if callable(accessor):
        return accessor(record)
    return getattr(record, accessor)


def iter_rows(section_key, queryset):
    """Yield one list of cell values per record."""
    columns = EXPORT_SECTIONS[section_key]['columns']
    for record in queryset:
        yield [_cell(record, accessor) for _header, accessor in columns]


def section_headers(section_key):
    return [header for header, _accessor in EXPORT_SECTIONS[section_key]['columns']]


def write_csv(response, section_key, queryset):
    """Write the section as CSV into an HttpResponse (BOM for Excel)."""
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(section_headers(section_key))
    for row in iter_rows(section_key, queryset):
        writer.writerow(row)
    return response


def _write_sheet(sheet, section_key, queryset):
    headers = section_headers(section_key)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = HEADER_FONT
    money_columns = set()
    for row in iter_rows(section_key, queryset):
        sheet.append(row)
        for index, value in enumerate(row, start=1):
            if isinstance(value, Decimal):
                money_columns.add(index)
    for index in money_columns:
        for cell in sheet.iter_cols(
            min_col=index, max_col=index, min_row=2,
        ):
            for c in cell:
                c.number_format = MONEY_FORMAT
    for index, header in enumerate(headers, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = max(
            14, len(header) + 4,
        )


def write_xlsx(section_key, queryset):
    """Return a single-sheet Workbook for the section."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = EXPORT_SECTIONS[section_key]['title']
    _write_sheet(sheet, section_key, queryset)
    return workbook


def _append_summary_block(sheet, title, rows):
    sheet.append([title])
    sheet[sheet.max_row][0].font = HEADER_FONT
    for label, value in rows:
        sheet.append([label, value])
        if isinstance(value, Decimal):
            sheet.cell(row=sheet.max_row, column=2).number_format = MONEY_FORMAT
    sheet.append([])


def build_workbook(year, sections_querysets):
    """Full accounting workbook: summary sheet + one sheet per section.

    `sections_querysets` maps section keys to their (already filtered)
    querysets so the view controls year scoping per section.
    """
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = 'Resumen'
    summary = dashboard_summary(year)

    _append_summary_block(summary_sheet, f'Resumen {year}', [
        ('Ingresos esperados', summary['expected_total']),
        ('Ingresos líquidos', summary['liquid_total']),
        ('Gastos', summary['expenses_total']),
        ('Utilidad esperada', summary['expected_utility']),
        ('Utilidad líquida', summary['liquid_utility']),
        ('Bolsillo ProjectApp', summary['pocket_balance']),
        ('Costo operativo mensual', summary['recurring_monthly_cost']),
    ])

    partner_labels = {
        'gustavo': 'Gustavo',
        'carlos': 'Carlos',
        'company': 'ProjectApp (Empresa)',
    }
    for key, label in partner_labels.items():
        partner = summary['partners'][key]
        _append_summary_block(summary_sheet, label, [
            ('Esperado', partner['expected']),
            ('Líquido', partner['liquid']),
            ('Gastos', partner['expenses']),
            ('Neto', partner['net']),
        ])

    summary_sheet.append(['Detalle mensual'])
    summary_sheet[summary_sheet.max_row][0].font = HEADER_FONT
    summary_sheet.append(['Mes', 'Esperado', 'Líquido', 'Gastos', 'Utilidad'])
    for cell in summary_sheet[summary_sheet.max_row]:
        cell.font = HEADER_FONT
    for month in summary['monthly']:
        summary_sheet.append([
            month['label'], month['expected'], month['liquid'],
            month['expenses'], month['utility'],
        ])
        for column in range(2, 6):
            summary_sheet.cell(
                row=summary_sheet.max_row, column=column,
            ).number_format = MONEY_FORMAT
    summary_sheet.append([])

    if summary['latest_card_snapshots']:
        summary_sheet.append(['Tarjetas (último registro)'])
        summary_sheet[summary_sheet.max_row][0].font = HEADER_FONT
        summary_sheet.append(['Tarjeta', 'Fecha', 'Disponible', 'Deuda'])
        for cell in summary_sheet[summary_sheet.max_row]:
            cell.font = HEADER_FONT
        for snapshot in summary['latest_card_snapshots']:
            summary_sheet.append([
                snapshot['card_name'], snapshot['snapshot_date'],
                snapshot['available_amount'], snapshot['debt_amount'],
            ])
            for column in (3, 4):
                summary_sheet.cell(
                    row=summary_sheet.max_row, column=column,
                ).number_format = MONEY_FORMAT

    summary_sheet.column_dimensions['A'].width = 28
    for letter in ('B', 'C', 'D', 'E'):
        summary_sheet.column_dimensions[letter].width = 16

    for section_key, queryset in sections_querysets.items():
        sheet = workbook.create_sheet(EXPORT_SECTIONS[section_key]['title'])
        _write_sheet(sheet, section_key, queryset)

    return workbook


def export_filename(stem, extension):
    return f'{stem}_{today_bogota().strftime("%Y%m%d")}.{extension}'
