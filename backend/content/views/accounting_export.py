"""Export endpoints for the accounting module (CSV / XLSX, superuser-only).

`export_accounting_records` reuses the exact same `_ENTITIES` config and
`_apply_filters` query params as the list endpoints, so an export always
matches what the panel shows for the same filters.
"""
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes

from content.api_errors import error_response
from content.models import CreditCardTransaction
from content.permissions import IsSuperUser
from content.services import accounting_export_service, accounting_history_service
from content.utils import today_bogota
from content.views.accounting import _ENTITIES, _apply_filters, base_queryset

XLSX_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Workbook sheets scoped to the requested year via their date field;
# sections without one (recurring) are exported in full.
_WORKBOOK_SECTIONS = (
    'income', 'expense', 'hosting', 'pocket', 'recurring', 'ads',
    'card_snapshot', 'statement',
)


def _xlsx_response(workbook, filename):
    response = HttpResponse(content_type=XLSX_CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


# The Historial subtabs are not `_ENTITIES` rows — they have no CRUD and
# their own filter vocabulary — so they build their queryset from the same
# service the list and the tab counts use.
_HISTORY_SECTIONS = {
    'email_log': accounting_history_service.email_log_queryset,
    'change_log': accounting_history_service.change_log_queryset,
}


@api_view(['GET'])
@permission_classes([IsSuperUser])
def export_accounting_records(request):
    section = request.query_params.get('section', '')
    if section not in _ENTITIES and section not in _HISTORY_SECTIONS:
        return error_response(
            "El parámetro 'section' no corresponde a una sección contable.",
            code='invalid_section',
            status=400,
        )
    export_format = request.query_params.get('file_format', 'csv')
    if export_format not in ('csv', 'xlsx'):
        return error_response(
            "El parámetro 'file_format' debe ser csv o xlsx.",
            code='invalid_format',
            status=400,
        )

    try:
        if section in _HISTORY_SECTIONS:
            queryset = _HISTORY_SECTIONS[section](request.query_params)
            if section == 'email_log':
                queryset = queryset.prefetch_related('targets')
        else:
            config = _ENTITIES[section]
            queryset = _apply_filters(
                base_queryset(config), request.query_params, config,
            )
    except ValueError as exc:
        return error_response(str(exc), code='invalid_filter', status=400)

    filename = accounting_export_service.export_filename(
        f'contabilidad_{section}', export_format,
    )
    if export_format == 'xlsx':
        workbook = accounting_export_service.write_xlsx(section, queryset)
        return _xlsx_response(workbook, filename)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return accounting_export_service.write_csv(response, section, queryset)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def export_accounting_workbook(request):
    raw_year = request.query_params.get('year') or str(today_bogota().year)
    try:
        year = int(raw_year)
    except (TypeError, ValueError):
        return error_response(
            "El parámetro 'year' debe ser un año válido.",
            code='invalid_year',
            status=400,
        )

    sections_querysets = {}
    for section in _WORKBOOK_SECTIONS:
        config = _ENTITIES[section]
        # base_queryset, not the raw manager: the income sheet's collection
        # state reads the paid_amount annotation.
        queryset = base_queryset(config)
        if config['date_field']:
            queryset = queryset.filter(
                **{f'{config["date_field"]}__year': year},
            )
        sections_querysets[section] = queryset

    # Statement lines live outside _ENTITIES (nested resource): year-scope
    # them through their parent statement.
    sections_querysets['statement_tx'] = (
        CreditCardTransaction.objects
        .filter(statement__period_date__year=year)
        .select_related('statement')
    )

    workbook = accounting_export_service.build_workbook(
        year, sections_querysets,
    )
    filename = accounting_export_service.export_filename(
        f'contabilidad_projectapp_{year}', 'xlsx',
    )
    return _xlsx_response(workbook, filename)
