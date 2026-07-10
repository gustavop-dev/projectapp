"""
Tool registry for the Accounting MCP connector (módulo contable).

Exposes the personal-ledger accounting panel (/panel/accounting) over MCP:
per-ledger CRUD for the 7 record types, plus the dashboard summary, the audit
change-log, and settings.

This module is table-driven in the panel by `_ENTITIES` + `_apply_filters`
(content/views/accounting.py). The MCP reuses those exact structures and always
routes writes through `accounting_service.create_record/update_record/
delete_record` so the audit trail, notifications and pocket side-effects fire
identically to the panel.

Guardrails (mirror the panel):
- Every accounting endpoint is superuser-only; writes are attributed to the MCP
  actor (see content.mcp.actor), which must be an active superuser.
- Auto-managed pocket movements (income/expense-backed) are not editable or
  deletable — the service raises, and we surface it as ToolError.
- Split invariants are validated by the write serializer + model.
- This is sensitive financial data with a partner split; keep the connector
  inactive until you deliberately issue a token.

Each entry: {'name', 'description', 'input_schema', 'handler'}.
"""
from content.mcp.actor import mcp_actor
from content.mcp.protocol import ToolError
from content.models import AccountingChangeLog, AccountingSettings
from content.serializers.accounting import (
    AccountingChangeLogSerializer,
    AccountingSettingsSerializer,
)
from content.services import accounting_service
from content.utils import today_bogota
from content.views.accounting import (
    EntityType,
    _ENTITIES,
    _apply_filters,
    _parse_date,
)


def _serializer_errors_to_message(errors):
    import json
    return 'Datos inválidos: ' + json.dumps(errors, ensure_ascii=False, default=str)


def _str_params(arguments):
    """Coerce MCP arguments to the string form `_apply_filters` expects.

    The panel filters read query-string params: numbers arrive as strings and
    booleans as the literals 'true'/'false'. Normalize accordingly and drop
    None so unspecified filters are skipped.
    """
    params = {}
    for key, value in arguments.items():
        if value is None:
            continue
        if isinstance(value, bool):
            params[key] = 'true' if value else 'false'
        else:
            params[key] = str(value)
    return params


def _get_instance_or_error(key, record_id):
    model = _ENTITIES[key]['model']
    try:
        return model.objects.get(pk=int(record_id))
    except (model.DoesNotExist, TypeError, ValueError):
        raise ToolError(f'No existe un registro {key} con id={record_id}.')


# ── Generic per-ledger handlers (bound to a key via closures) ────────────────

def _make_list(key):
    def handler(arguments):
        config = _ENTITIES[key]
        queryset = config['model'].objects.all()
        params = _str_params(arguments)
        try:
            queryset = _apply_filters(queryset, params, config)
            meta = config.get('meta', lambda qs, p: {})(queryset, params)
        except ValueError as exc:
            raise ToolError(str(exc))
        if config.get('with_accumulated'):
            records = accounting_service.ads_with_accumulated(queryset)
        else:
            records = queryset
        data = config['read'](records, many=True).data
        return {'count': len(data), 'results': data, 'meta': meta}
    return handler


def _make_get(key):
    def handler(arguments):
        instance = _get_instance_or_error(key, arguments.get('record_id'))
        return _ENTITIES[key]['read'](instance).data
    return handler


def _make_create(key):
    def handler(arguments):
        config = _ENTITIES[key]
        data = {k: v for k, v in arguments.items() if k != 'record_id'}
        serializer = config['write'](data=data)
        if not serializer.is_valid():
            raise ToolError(_serializer_errors_to_message(serializer.errors))
        try:
            instance = accounting_service.create_record(
                config['entity_type'], serializer, mcp_actor(),
            )
        except ValueError as exc:
            raise ToolError(str(exc))
        return config['read'](instance).data
    return handler


def _make_update(key):
    def handler(arguments):
        config = _ENTITIES[key]
        instance = _get_instance_or_error(key, arguments.get('record_id'))
        data = {k: v for k, v in arguments.items() if k != 'record_id'}
        if not data:
            raise ToolError('No se indicó ningún campo para actualizar.')
        serializer = config['write'](instance, data=data, partial=True)
        if not serializer.is_valid():
            raise ToolError(_serializer_errors_to_message(serializer.errors))
        try:
            instance = accounting_service.update_record(
                config['entity_type'], instance, serializer, mcp_actor(),
            )
        except ValueError as exc:
            raise ToolError(str(exc))
        return config['read'](instance).data
    return handler


def _make_delete(key):
    def handler(arguments):
        config = _ENTITIES[key]
        instance = _get_instance_or_error(key, arguments.get('record_id'))
        record_id = instance.pk
        try:
            accounting_service.delete_record(
                config['entity_type'], instance, mcp_actor(),
            )
        except ValueError as exc:
            raise ToolError(str(exc))
        return {'deleted': True, 'id': record_id}
    return handler


# ── Non-CRUD handlers ────────────────────────────────────────────────────────

def get_dashboard(arguments):
    year_arg = arguments.get('year')
    try:
        year = int(year_arg) if year_arg else today_bogota().year
    except (TypeError, ValueError):
        raise ToolError("El parámetro 'year' debe ser un año válido.")
    return accounting_service.dashboard_summary(year)


def list_change_logs(arguments):
    logs = AccountingChangeLog.objects.select_related('actor').all()
    try:
        if arguments.get('entity_type'):
            logs = logs.filter(entity_type=arguments['entity_type'])
        if arguments.get('object_id'):
            logs = logs.filter(object_id=arguments['object_id'])
        if arguments.get('action'):
            logs = logs.filter(action=arguments['action'])
        if arguments.get('actor'):
            logs = logs.filter(actor_username__icontains=arguments['actor'])
        if arguments.get('date_from'):
            logs = logs.filter(created_at__date__gte=_parse_date(arguments['date_from'], 'date_from'))
        if arguments.get('date_to'):
            logs = logs.filter(created_at__date__lte=_parse_date(arguments['date_to'], 'date_to'))
    except ValueError as exc:
        raise ToolError(str(exc))

    total = logs.count()
    try:
        page = max(1, int(arguments.get('page', 1) or 1))
    except (TypeError, ValueError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size
    num_pages = max(1, -(-total // page_size))
    data = AccountingChangeLogSerializer(logs[offset:offset + page_size], many=True).data
    return {'results': data, 'count': total, 'page': page, 'num_pages': num_pages}


def get_settings(arguments):
    return AccountingSettingsSerializer(AccountingSettings.load()).data


def update_settings(arguments):
    instance = AccountingSettings.load()
    serializer = AccountingSettingsSerializer(instance, data=arguments, partial=True)
    if not serializer.is_valid():
        raise ToolError(_serializer_errors_to_message(serializer.errors))
    try:
        instance = accounting_service.update_record(
            EntityType.SETTINGS, instance, serializer, mcp_actor(),
        )
    except ValueError as exc:
        raise ToolError(str(exc))
    return AccountingSettingsSerializer(instance).data


# ── Per-entity schema metadata (create/update fields + list filters) ─────────

# Create/update field schemas per ledger. The write serializer is the source of
# truth for validation; these are documented for the model's benefit.
_LEDGER_ENUM = ['company', 'gustavo', 'carlos']

_ENTITY_FIELDS = {
    'income': {
        'props': {
            'concept': {'type': 'string'},
            'kind': {'type': 'string', 'enum': ['expected', 'liquid']},
            'period_date': {'type': 'string', 'description': 'Periodo YYYY-MM.'},
            'total_amount': {'type': ['number', 'string']},
            'destination': {'type': 'string', 'enum': ['partners', 'pocket']},
            'ledger': {'type': 'string', 'enum': _LEDGER_ENUM},
            'gustavo_amount': {'type': ['number', 'string']},
            'carlos_amount': {'type': ['number', 'string']},
            'notes': {'type': 'string'},
        },
        'required': ['concept', 'kind', 'period_date', 'total_amount'],
    },
    'expense': {
        'props': {
            'concept': {'type': 'string'},
            'period_date': {'type': 'string', 'description': 'Periodo YYYY-MM.'},
            'total_amount': {'type': ['number', 'string']},
            'category': {'type': 'string', 'enum': ['business', 'personal']},
            'ledger': {'type': 'string', 'enum': _LEDGER_ENUM},
            'gustavo_amount': {'type': ['number', 'string']},
            'carlos_amount': {'type': ['number', 'string']},
            'notes': {'type': 'string'},
        },
        'required': ['concept', 'period_date', 'total_amount'],
    },
    'hosting': {
        'props': {
            'client_name': {'type': 'string'},
            'monthly_value': {'type': ['number', 'string']},
            'domain_url': {'type': 'string'},
            'payment_modality': {'type': 'string', 'enum': ['monthly', 'quarterly', 'semiannual', 'annual']},
            'benefit': {'type': 'string'},
            'valid_from': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'valid_to': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'cycles_count': {'type': 'integer'},
            'payment_per_cycle': {'type': ['number', 'string']},
            'total_paid': {'type': ['number', 'string']},
            'is_active': {'type': 'boolean'},
            'notes': {'type': 'string'},
        },
        'required': ['client_name', 'monthly_value'],
    },
    'pocket': {
        'props': {
            'concept': {'type': 'string'},
            'movement_date': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'direction': {'type': 'string', 'enum': ['in', 'out']},
            'amount': {'type': ['number', 'string']},
            'notes': {'type': 'string'},
        },
        'required': ['concept', 'movement_date', 'direction', 'amount'],
    },
    'recurring': {
        'props': {
            'name': {'type': 'string'},
            'price': {'type': ['number', 'string']},
            'currency': {'type': 'string', 'enum': ['COP', 'USD']},
            'cop_equivalent': {'type': ['number', 'string']},
            'payment_method': {'type': 'string', 'enum': ['cash', 'credit_card']},
            'frequency': {'type': 'string', 'enum': ['monthly', 'annual', 'biennial', 'triennial']},
            'billing_day': {'type': 'integer', 'minimum': 1, 'maximum': 31},
            'cost_type': {'type': 'string', 'enum': ['fixed', 'variable']},
            'is_active': {'type': 'boolean'},
            'notes': {'type': 'string'},
        },
        'required': ['name', 'price'],
    },
    'ads': {
        'props': {
            'spend_date': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'amount': {'type': ['number', 'string']},
            'platform': {'type': 'string', 'enum': ['facebook', 'google', 'other']},
            'origin_card': {'type': 'string'},
            'notes': {'type': 'string'},
        },
        'required': ['spend_date', 'amount'],
    },
    'card_snapshot': {
        'props': {
            'snapshot_date': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'card_name': {'type': 'string'},
            'available_amount': {'type': ['number', 'string']},
            'debt_amount': {'type': ['number', 'string']},
            'notes': {'type': 'string'},
        },
        'required': ['snapshot_date', 'card_name', 'available_amount', 'debt_amount'],
    },
}

_ENTITY_LABELS = {
    'income': 'ingresos',
    'expense': 'gastos',
    'hosting': 'hostings',
    'pocket': 'movimientos de pocket',
    'recurring': 'pagos recurrentes',
    'ads': 'gasto en ads',
    'card_snapshot': 'snapshots de tarjeta',
}


def _list_schema(key):
    config = _ENTITIES[key]
    props = {'q': {'type': 'string', 'description': 'Búsqueda de texto.'}}
    if config['date_field']:
        props.update({
            'year': {'type': 'integer'},
            'date_from': {'type': 'string', 'description': 'YYYY-MM-DD.'},
            'date_to': {'type': 'string', 'description': 'YYYY-MM-DD.'},
        })
    props.update({
        'amount_min': {'type': ['number', 'string']},
        'amount_max': {'type': ['number', 'string']},
    })
    for field in config.get('choice_filters', ()):
        props[field] = {'type': 'string', 'description': 'Uno o varios valores separados por coma.'}
    for field in config.get('bool_filters', ()):
        props[field] = {'type': 'boolean'}
    if config.get('has_split'):
        props['partner'] = {'type': 'string', 'enum': ['gustavo', 'carlos', 'projectapp', 'all']}
    return {'type': 'object', 'properties': props}


_RECORD_ID_PROP = {'record_id': {'type': 'integer', 'description': 'ID del registro.'}}


def _build_ledger_tools():
    tools = []
    for key, fields in _ENTITY_FIELDS.items():
        label = _ENTITY_LABELS[key]
        tools.append({
            'name': f'list_{key}',
            'description': f'Lista {label} con filtros (fechas, montos, categorías, búsqueda q).',
            'input_schema': _list_schema(key),
            'handler': _make_list(key),
        })
        tools.append({
            'name': f'get_{key}',
            'description': f'Devuelve un registro de {label} por id.',
            'input_schema': {'type': 'object', 'properties': _RECORD_ID_PROP, 'required': ['record_id']},
            'handler': _make_get(key),
        })
        tools.append({
            'name': f'create_{key}',
            'description': f'Crea un registro de {label}.',
            'input_schema': {
                'type': 'object',
                'properties': fields['props'],
                'required': fields['required'],
            },
            'handler': _make_create(key),
        })
        tools.append({
            'name': f'update_{key}',
            'description': f'Actualiza (parcial) un registro de {label}. Envía record_id + campos.',
            'input_schema': {
                'type': 'object',
                'properties': {**_RECORD_ID_PROP, **fields['props']},
                'required': ['record_id'],
            },
            'handler': _make_update(key),
        })
        tools.append({
            'name': f'delete_{key}',
            'description': f'Elimina un registro de {label}. Los movimientos de pocket auto-gestionados no se pueden borrar.',
            'input_schema': {'type': 'object', 'properties': _RECORD_ID_PROP, 'required': ['record_id']},
            'handler': _make_delete(key),
        })
    return tools


_NON_CRUD_TOOLS = [
    {
        'name': 'get_dashboard',
        'description': (
            'Resumen contable del año: totales, split de socios, breakdown '
            'mensual, balance de pocket, costo recurrente, ads, hostings y '
            'últimos snapshots de tarjeta. Param opcional: year.'
        ),
        'input_schema': {'type': 'object', 'properties': {'year': {'type': 'integer'}}},
        'handler': get_dashboard,
    },
    {
        'name': 'list_change_logs',
        'description': (
            'Auditoría de cambios (paginada, 20/pág). Filtros: entity_type, '
            'object_id, action (created/updated/deleted), actor, date_from, '
            'date_to, page.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'entity_type': {'type': 'string'},
                'object_id': {'type': 'integer'},
                'action': {'type': 'string', 'enum': ['created', 'updated', 'deleted']},
                'actor': {'type': 'string'},
                'date_from': {'type': 'string'},
                'date_to': {'type': 'string'},
                'page': {'type': 'integer', 'default': 1},
            },
        },
        'handler': list_change_logs,
    },
    {
        'name': 'get_settings',
        'description': 'Devuelve la configuración contable (destinatarios de notificación, recordatorio de tarjeta).',
        'input_schema': {'type': 'object', 'properties': {}},
        'handler': get_settings,
    },
    {
        'name': 'update_settings',
        'description': (
            'Actualiza (parcial) la configuración contable: notification_recipients '
            '(lista de emails), notifications_enabled, card_reminder_enabled.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'notification_recipients': {'type': 'array', 'items': {'type': 'string'}},
                'notifications_enabled': {'type': 'boolean'},
                'card_reminder_enabled': {'type': 'boolean'},
            },
        },
        'handler': update_settings,
    },
]

ACCOUNTING_TOOLS = _build_ledger_tools() + _NON_CRUD_TOOLS
