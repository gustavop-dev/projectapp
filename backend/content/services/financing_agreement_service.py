"""Domain service for financing addenda, schedules, lifecycle, and audit."""

from __future__ import annotations

import hashlib
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from string import Formatter

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.services.proposal_client_service import build_client_display_name
from content.models import (
    CompanySettings,
    FinancingAgreement,
    FinancingAgreementEvent,
    FinancingAgreementNumberSequence,
    FinancingAgreementTemplate,
)
from content.services.contractor_identity import resolve_contractor_identity


INSTALLMENT_COUNT = 12
MAX_SIGNED_PDF_SIZE = 15 * 1024 * 1024
LATE_HOSTING_INCREASE_PERCENT = Decimal('1.00')


DEFAULT_FINANCING_TEMPLATE_MARKDOWN = """# OTROSÍ DE FINANCIACIÓN {agreement_number}

Entre los suscritos, **{client_full_name}**, identificado(a) con {client_id_type} No. {client_id_number}, en adelante **EL CONTRATANTE**, y **{contractor_full_name}**, identificado(a) con {contractor_id_type} No. {contractor_id_number}, en adelante **EL CONTRATISTA**, se celebra el presente otrosí al contrato **{original_contract_reference}**, suscrito el {original_contract_date}.

## PRIMERA. OBJETO

Las partes incorporan un mecanismo de financiación para el desarrollo e implementación de **{project_name}**, limitado al siguiente alcance aprobado:

> {financed_scope}

Este otrosí complementa el contrato original. Las cláusulas no modificadas conservan plena vigencia.

## SEGUNDA. VALOR Y SALDO FINANCIADO

El valor del ciclo es **{total_value}**. EL CONTRATANTE realiza un aporte inicial de **{initial_payment}** y el saldo financiado corresponde a **{financed_balance}**, a doce (12) meses y con interés ordinario del cero por ciento (0 %).

## TERCERA. CALENDARIO DE PAGOS

Cada cuota se paga dentro de los primeros cinco (5) días calendario del mes correspondiente, conforme al siguiente calendario:

{installment_schedule}

El pago de una cuota no extingue las cuotas anteriores que continúen pendientes.

## CUARTA. MORA Y AUMENTO DEL HOSTING

Por cada cuota que no sea pagada dentro de los primeros cinco (5) días calendario del mes correspondiente, el costo vigente del Hosting —actualmente **{hosting_value}** con periodicidad {hosting_period}— aumentará en un uno por ciento (1 %). Cada aumento es acumulativo, permanente y opera automáticamente desde el vencimiento, sin necesidad de requerimiento previo. Esta consecuencia no sustituye la obligación de pagar la cuota vencida ni las demás consecuencias legalmente procedentes que se pacten y resulten aplicables.

Las partes reconocen que esta condición distribuye el riesgo de impago asumido por EL CONTRATISTA al entregar y operar el producto antes de recuperar la totalidad del saldo financiado.

## QUINTA. MODALIDAD, EXCLUSIVIDAD Y CONTINUIDAD

La modalidad elegida es **{modality_label}**, vigente desde el {partnership_start_date} hasta el {partnership_end_date}.

{modality_terms}

Durante este periodo EL CONTRATISTA será la casa desarrolladora exclusiva del producto financiado para su desarrollo, mantenimiento, soporte, infraestructura, actualizaciones y continuidad técnica. La exclusividad se limita a este producto y no restringe iniciativas independientes de EL CONTRATANTE.

## SEXTA. CUSTODIA DEL CÓDIGO

EL CONTRATISTA conservará la custodia operativa de repositorios, versiones, respaldos, accesos e integridad del código durante la vigencia acordada. La custodia no transfiere a EL CONTRATISTA la propiedad intelectual ni autoriza una explotación distinta de la necesaria para ejecutar el contrato. La entrega material de repositorios se realizará al terminar la custodia y estar cumplidas las obligaciones pactadas, mediante acta.

## SÉPTIMA. CALCULADORA DE REQUERIMIENTOS

EL CONTRATANTE podrá describir en lenguaje natural una necesidad, su objetivo y el contexto esencial del producto. La calculadora devolverá una referencia de esfuerzo, trabajo, tiempo y rango de precio. El resultado es orientativo: sólo una cotización formal aprobada por ambas partes fija alcance, cronograma y precio definitivo.

## OCTAVA. PREVALENCIA Y REVISIÓN

En caso de contradicción, este otrosí prevalece únicamente sobre las materias que modifica expresamente. Los datos, valores y fechas aquí incorporados forman parte integral del acuerdo. El documento debe ser revisado por las partes y por su asesoría jurídica antes de firma.

Firmado en {contract_city}, el {contract_date}.

| EL CONTRATANTE | EL CONTRATISTA |
| --- | --- |
| {client_full_name} | {contractor_full_name} |
| {client_id_type} {client_id_number} | {contractor_id_type} {contractor_id_number} |
| {client_email} | {contractor_email} |
"""


KNOWN_PLACEHOLDERS = frozenset({
    'agreement_number',
    'client_full_name',
    'client_id_type',
    'client_id_number',
    'client_email',
    'client_phone',
    'client_company',
    'contractor_full_name',
    'contractor_id_type',
    'contractor_id_number',
    'contractor_email',
    'original_contract_reference',
    'original_contract_date',
    'project_name',
    'financed_scope',
    'total_value',
    'initial_payment',
    'financed_balance',
    'installment_schedule',
    'hosting_value',
    'hosting_period',
    'modality_label',
    'modality_terms',
    'partnership_start_date',
    'partnership_end_date',
    'contract_city',
    'contract_date',
})

MANDATORY_PLACEHOLDERS = frozenset({
    'agreement_number',
    'client_full_name',
    'client_id_type',
    'client_id_number',
    'contractor_full_name',
    'contractor_id_type',
    'contractor_id_number',
    'original_contract_reference',
    'original_contract_date',
    'project_name',
    'financed_scope',
    'financed_balance',
    'installment_schedule',
    'hosting_value',
    'modality_label',
    'modality_terms',
    'partnership_end_date',
})


class FinancingAgreementValidationError(ValueError):
    def __init__(self, errors, *, code='invalid_financing_agreement'):
        self.errors = errors
        self.code = code
        super().__init__(str(errors))


class FinancingAgreementTransitionError(RuntimeError):
    def __init__(self, detail, *, code='invalid_transition'):
        self.detail = detail
        self.code = code
        super().__init__(detail)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def default_first_installment_date() -> date:
    current = timezone.localdate()
    return add_months(current.replace(day=1), 1)


def calculate_financed_balance(total_value, initial_payment) -> Decimal:
    total = Decimal(str(total_value or 0)).quantize(Decimal('0.01'))
    initial = Decimal(str(initial_payment or 0)).quantize(Decimal('0.01'))
    if total < 0:
        raise FinancingAgreementValidationError({
            'total_value': ['El valor total no puede ser negativo.'],
        })
    if initial < 0:
        raise FinancingAgreementValidationError({
            'initial_payment': ['El aporte inicial no puede ser negativo.'],
        })
    if initial > total:
        raise FinancingAgreementValidationError({
            'initial_payment': ['El aporte inicial no puede superar el valor total.'],
        })
    return total - initial


def build_installment_schedule(balance, first_due_date) -> list[dict]:
    balance = Decimal(str(balance or 0)).quantize(Decimal('0.01'))
    if balance <= 0:
        return []
    first_due_date = first_due_date or default_first_installment_date()
    if first_due_date.day not in range(1, 6):
        raise FinancingAgreementValidationError({
            'first_installment_date': [
                'La primera cuota debe vencer entre los días 1 y 5 del mes.',
            ],
        })
    base_amount = (balance / INSTALLMENT_COUNT).quantize(
        Decimal('0.01'),
        rounding=ROUND_DOWN,
    )
    last_amount = balance - (base_amount * (INSTALLMENT_COUNT - 1))
    return [
        {
            'number': index + 1,
            'due_date': add_months(first_due_date, index).isoformat(),
            'amount': format(
                last_amount if index == INSTALLMENT_COUNT - 1 else base_amount,
                '.2f',
            ),
        }
        for index in range(INSTALLMENT_COUNT)
    ]


def normalize_installment_schedule(schedule, balance) -> list[dict]:
    errors = {}
    if not isinstance(schedule, list) or len(schedule) != INSTALLMENT_COUNT:
        raise FinancingAgreementValidationError({
            'installment_schedule': ['El calendario debe contener exactamente 12 cuotas.'],
        })

    normalized = []
    dates = []
    amounts = []
    for index, raw_item in enumerate(schedule):
        if not isinstance(raw_item, dict):
            errors.setdefault('installment_schedule', []).append(
                f'La cuota {index + 1} tiene un formato inválido.',
            )
            continue
        raw_date = raw_item.get('due_date')
        try:
            due_date = date.fromisoformat(str(raw_date))
        except (TypeError, ValueError):
            errors.setdefault('installment_schedule', []).append(
                f'La fecha de la cuota {index + 1} no es válida.',
            )
            continue
        try:
            amount = Decimal(str(raw_item.get('amount'))).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError, ValueError):
            errors.setdefault('installment_schedule', []).append(
                f'El valor de la cuota {index + 1} no es válido.',
            )
            continue
        if due_date.day not in range(1, 6):
            errors.setdefault('installment_schedule', []).append(
                f'La cuota {index + 1} debe vencer entre los días 1 y 5.',
            )
        if amount <= 0:
            errors.setdefault('installment_schedule', []).append(
                f'La cuota {index + 1} debe tener un valor positivo.',
            )
        dates.append(due_date)
        amounts.append(amount)
        normalized.append({
            'number': index + 1,
            'due_date': due_date.isoformat(),
            'amount': format(amount, '.2f'),
        })

    if errors:
        raise FinancingAgreementValidationError(errors)
    if dates != sorted(dates) or len(set(dates)) != INSTALLMENT_COUNT:
        raise FinancingAgreementValidationError({
            'installment_schedule': [
                'Las fechas deben ser únicas y estar en orden ascendente.',
            ],
        })
    expected = Decimal(str(balance or 0)).quantize(Decimal('0.01'))
    if sum(amounts, Decimal('0.00')) != expected:
        raise FinancingAgreementValidationError({
            'installment_schedule': [
                f'Las cuotas deben sumar exactamente {format(expected, ".2f")}.',
            ],
        })
    return normalized


def _date_es(value) -> str:
    if not value:
        return '________________'
    months = (
        '', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
        'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    )
    return f'{value.day} de {months[value.month]} de {value.year}'


def _money(value, currency='COP') -> str:
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return '________________'
    integer, decimals = f'{amount:.2f}'.split('.')
    grouped = f'{int(integer):,}'.replace(',', '.')
    return f'$ {grouped},{decimals} {currency}'


def _plain_markdown(value) -> str:
    text = str(value or '').strip()
    if not text:
        return '________________'
    return text.replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def _extract_placeholders(markdown_text) -> set[str]:
    try:
        fields = {
            field_name
            for _, field_name, _, _ in Formatter().parse(markdown_text or '')
            if field_name
        }
    except ValueError as exc:
        raise FinancingAgreementValidationError({
            'contract_markdown': [f'La plantilla contiene llaves inválidas: {exc}.'],
        }) from exc
    unknown = fields - KNOWN_PLACEHOLDERS
    if unknown:
        raise FinancingAgreementValidationError({
            'contract_markdown': [
                'Marcadores no reconocidos: ' + ', '.join(sorted(unknown)) + '.',
            ],
        })
    return fields


def validate_template_markdown(markdown_text, *, require_core=True):
    if not (markdown_text or '').strip():
        raise FinancingAgreementValidationError({
            'contract_markdown': ['El texto del otrosí no puede estar vacío.'],
        })
    fields = _extract_placeholders(markdown_text)
    if require_core:
        missing = MANDATORY_PLACEHOLDERS - fields
        if missing:
            raise FinancingAgreementValidationError({
                'contract_markdown': [
                    'El otrosí debe conservar estos marcadores obligatorios: '
                    + ', '.join(sorted(missing))
                    + '.',
                ],
            })
    return fields


def _schedule_markdown(schedule, currency):
    if not schedule:
        return '| Cuota | Vencimiento | Valor |\n| --- | --- | --- |\n| — | — | — |'
    rows = ['| Cuota | Vencimiento | Valor |', '| --- | --- | --- |']
    for item in schedule:
        due_date = date.fromisoformat(item['due_date'])
        rows.append(
            f'| {item["number"]} | {_date_es(due_date)} | '
            f'{_money(item["amount"], currency)} |',
        )
    return '\n'.join(rows)


def _modality_terms(agreement):
    if agreement.modality == FinancingAgreement.Modality.FIVE_YEAR:
        return (
            'La alianza incluye un paquete de sesenta (60) horas que se renueva '
            'cada mes desde la salida a producción, no es acumulable y se usa '
            'para requerimientos aprobados según disponibilidad. Además, permite '
            'hasta dos ciclos separados de financiación de doce (12) meses. El '
            'segundo sólo podrá aprobarse cuando el primero haya sido pagado en su '
            'totalidad y EL CONTRATISTA complete una nueva evaluación manual de '
            'riesgo. Su calendario deberá terminar dentro de la vigencia original '
            'de cinco años y no reiniciará ni extenderá la exclusividad.'
        )
    return (
        'La alianza permite un único ciclo de financiación de doce (12) meses y '
        'no incluye paquete mensual de horas. Los requerimientos posteriores se '
        'evalúan y cotizan de forma independiente.'
    )


def agreement_placeholder_values(agreement, *, draft=False):
    company = CompanySettings.load()
    contractor_type, contractor_number = resolve_contractor_identity(
        company.contractor_nit,
        company.contractor_cedula,
        blank='________________',
    )
    number = agreement.number or ('BORRADOR' if draft else '________________')
    return {
        'agreement_number': number,
        'client_full_name': _plain_markdown(agreement.client_full_name),
        'client_id_type': _plain_markdown(agreement.client_id_type),
        'client_id_number': _plain_markdown(agreement.client_id_number),
        'client_email': _plain_markdown(agreement.client_email),
        'client_phone': _plain_markdown(agreement.client_phone),
        'client_company': _plain_markdown(agreement.client_company),
        'contractor_full_name': _plain_markdown(company.contractor_full_name),
        'contractor_id_type': _plain_markdown(contractor_type),
        'contractor_id_number': _plain_markdown(contractor_number),
        'contractor_email': _plain_markdown(company.contractor_email),
        'original_contract_reference': _plain_markdown(
            agreement.original_contract_reference,
        ),
        'original_contract_date': _date_es(agreement.original_contract_date),
        'project_name': _plain_markdown(agreement.project_name),
        'financed_scope': _plain_markdown(agreement.financed_scope),
        'total_value': _money(agreement.total_value, agreement.currency),
        'initial_payment': _money(agreement.initial_payment, agreement.currency),
        'financed_balance': _money(agreement.financed_balance, agreement.currency),
        'installment_schedule': _schedule_markdown(
            agreement.installment_schedule,
            agreement.currency,
        ),
        'hosting_value': _money(agreement.hosting_value, agreement.currency),
        'hosting_period': agreement.get_hosting_period_display().lower(),
        'modality_label': agreement.get_modality_display(),
        'modality_terms': _modality_terms(agreement),
        'partnership_start_date': _date_es(agreement.partnership_start_date),
        'partnership_end_date': _date_es(agreement.partnership_end_date),
        'contract_city': _plain_markdown(company.contract_city),
        'contract_date': _date_es(timezone.localdate()),
    }


def resolve_agreement_markdown(agreement, *, draft=False, require_core=True):
    markdown_text = agreement.contract_markdown or ''
    validate_template_markdown(markdown_text, require_core=require_core)
    return markdown_text.format(**agreement_placeholder_values(agreement, draft=draft))


def _snapshot_client(client):
    full_name = build_client_display_name(client)
    if client.nit:
        id_type, id_number = 'NIT', client.nit
    elif client.cedula:
        id_type, id_number = 'C.C.', client.cedula
    else:
        id_type, id_number = '', ''
    return {
        'client_full_name': full_name,
        'client_company': client.company_name or '',
        'client_id_type': id_type,
        'client_id_number': id_number,
        'client_email': '' if client.is_email_placeholder else (client.user.email or ''),
        'client_phone': client.phone or '',
    }


AUDIT_FIELDS = (
    'number', 'client_id', 'source_proposal_id', 'source_project_id',
    'client_full_name', 'client_company', 'client_id_type', 'client_id_number',
    'client_email', 'client_phone', 'original_contract_reference',
    'original_contract_date', 'project_name', 'financed_scope', 'modality',
    'cycle_number', 'previous_agreement_id', 'partnership_start_date',
    'partnership_end_date', 'currency', 'total_value', 'initial_payment',
    'financed_balance', 'hosting_value', 'hosting_period',
    'installment_schedule', 'template_id', 'template_version', 'status',
    'signed_document_sha256', 'signed_document_size', 'is_archived',
)


def _audit_state(agreement):
    state = {}
    for field in AUDIT_FIELDS:
        value = getattr(agreement, field)
        if isinstance(value, (Decimal, date)):
            value = str(value)
        state[field] = value
    return state


def _record_event(agreement, event_type, actor, before=None, details=None):
    return FinancingAgreementEvent.objects.create(
        agreement=agreement,
        event_type=event_type,
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        before_state=before or {},
        after_state=_audit_state(agreement),
        details=details or {},
    )


def _validate_source_links(client, proposal, project):
    errors = {}
    if client.role != client.ROLE_CLIENT:
        errors['client_id'] = ['Selecciona un perfil con rol de cliente.']
    if client.archived_at:
        errors['client_id'] = ['El cliente está archivado y no admite nuevos otrosíes.']
    if proposal and proposal.client_id != client.pk:
        errors['source_proposal_id'] = [
            'La propuesta seleccionada no pertenece al cliente.',
        ]
    if project and project.client_id != client.user_id:
        errors['source_project_id'] = [
            'El proyecto seleccionado no pertenece al cliente.',
        ]
    if errors:
        raise FinancingAgreementValidationError(errors)


def _required_create_fields(data):
    errors = {}
    for field, label in (
        ('original_contract_reference', 'la referencia del contrato original'),
        ('original_contract_date', 'la fecha del contrato original'),
        ('project_name', 'el nombre del proyecto o producto'),
        ('financed_scope', 'el alcance financiado'),
        ('modality', 'la modalidad'),
        ('partnership_start_date', 'la fecha de inicio de la alianza'),
    ):
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors[field] = [f'Indica {label}.']
    if errors:
        raise FinancingAgreementValidationError(errors)


def _prepare_financials(data, *, existing=None):
    financial_changed = existing is None or any(
        key in data for key in ('total_value', 'initial_payment')
    )
    total = data.get('total_value', getattr(existing, 'total_value', 0))
    initial = data.get('initial_payment', getattr(existing, 'initial_payment', 0))
    balance = calculate_financed_balance(total, initial)
    data['total_value'] = Decimal(str(total or 0)).quantize(Decimal('0.01'))
    data['initial_payment'] = Decimal(str(initial or 0)).quantize(Decimal('0.01'))
    data['financed_balance'] = balance

    schedule_supplied = 'installment_schedule' in data
    first_due = data.pop('first_installment_date', None)
    if schedule_supplied:
        data['installment_schedule'] = normalize_installment_schedule(
            data['installment_schedule'],
            balance,
        )
    elif financial_changed or first_due:
        if first_due is None and existing and existing.installment_schedule:
            first_due = date.fromisoformat(existing.installment_schedule[0]['due_date'])
        data['installment_schedule'] = build_installment_schedule(balance, first_due)


@transaction.atomic
def create_agreement(validated_data, *, actor):
    data = dict(validated_data)
    _required_create_fields(data)
    client = data['client']
    _validate_source_links(
        client,
        data.get('source_proposal'),
        data.get('source_project'),
    )
    template = data.get('template') or FinancingAgreementTemplate.get_default()
    if template is None:
        raise FinancingAgreementValidationError({
            'template_id': ['No existe una plantilla de financiación activa.'],
        })
    if not template.is_active:
        raise FinancingAgreementValidationError({
            'template_id': ['La plantilla seleccionada está inactiva.'],
        })
    _prepare_financials(data)
    if data['financed_balance'] <= 0:
        raise FinancingAgreementValidationError({
            'total_value': ['El saldo financiado debe ser mayor que cero.'],
        })
    if Decimal(str(data.get('hosting_value') or 0)) <= 0:
        raise FinancingAgreementValidationError({
            'hosting_value': ['Indica el costo vigente del Hosting.'],
        })
    modality = data['modality']
    start_date = data['partnership_start_date']
    years = 5 if modality == FinancingAgreement.Modality.FIVE_YEAR else 3
    data['partnership_end_date'] = add_years(start_date, years)
    data.update(_snapshot_client(client))
    supplied_snapshot = {
        key: validated_data[key]
        for key in (
            'client_full_name', 'client_company', 'client_id_type',
            'client_id_number', 'client_email', 'client_phone',
        )
        if key in validated_data
    }
    data.update(supplied_snapshot)
    data['template'] = template
    data['template_version'] = template.version
    data['contract_markdown'] = data.get('contract_markdown') or template.content_markdown
    data['cycle_number'] = 1
    data['created_by'] = actor
    data['updated_by'] = actor
    agreement = FinancingAgreement.objects.create(**data)
    _record_event(agreement, 'created', actor)
    return agreement


@transaction.atomic
def update_draft(agreement, validated_data, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status != FinancingAgreement.Status.DRAFT or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'Sólo un borrador activo puede editarse.',
            code='agreement_locked',
        )
    before = _audit_state(agreement)
    data = dict(validated_data)
    new_client = data.get('client', agreement.client)
    proposal = data.get('source_proposal', agreement.source_proposal)
    project = data.get('source_project', agreement.source_project)
    _validate_source_links(new_client, proposal, project)

    client_changed = new_client.pk != agreement.client_id
    supplied_snapshot = {
        key: data[key]
        for key in (
            'client_full_name', 'client_company', 'client_id_type',
            'client_id_number', 'client_email', 'client_phone',
        )
        if key in data
    }
    if client_changed:
        data.update(_snapshot_client(new_client))
        data.update(supplied_snapshot)

    new_modality = data.get('modality', agreement.modality)
    new_start = data.get('partnership_start_date', agreement.partnership_start_date)
    if agreement.cycle_number == 2:
        if new_modality != FinancingAgreement.Modality.FIVE_YEAR:
            raise FinancingAgreementValidationError({
                'modality': ['El segundo ciclo sólo existe en la alianza de cinco años.'],
            })
        if new_start != agreement.partnership_start_date:
            raise FinancingAgreementValidationError({
                'partnership_start_date': [
                    'El segundo ciclo conserva la vigencia original de la alianza.',
                ],
            })
        data['partnership_end_date'] = agreement.partnership_end_date
    elif 'modality' in data or 'partnership_start_date' in data:
        years = 5 if new_modality == FinancingAgreement.Modality.FIVE_YEAR else 3
        data['partnership_end_date'] = add_years(new_start, years)

    if 'template' in data:
        template = data['template']
        if not template.is_active:
            raise FinancingAgreementValidationError({
                'template_id': ['La plantilla seleccionada está inactiva.'],
            })
        data['template_version'] = template.version
        if 'contract_markdown' not in data:
            data['contract_markdown'] = template.content_markdown

    _prepare_financials(data, existing=agreement)
    for field, value in data.items():
        setattr(agreement, field, value)
    agreement.updated_by = actor
    agreement.save()
    _record_event(agreement, 'updated', actor, before=before)
    return agreement


def _ready_errors(agreement):
    errors = {}
    for field, label in (
        ('client_full_name', 'el nombre legal del cliente'),
        ('client_id_type', 'el tipo de identificación del cliente'),
        ('client_id_number', 'la identificación del cliente'),
        ('client_email', 'el correo del cliente'),
        ('original_contract_reference', 'la referencia del contrato original'),
        ('project_name', 'el proyecto o producto'),
        ('financed_scope', 'el alcance financiado'),
    ):
        if not str(getattr(agreement, field) or '').strip():
            errors[field] = [f'Completa {label} antes de marcar el otrosí como listo.']
    company = CompanySettings.load()
    contractor_type, contractor_number = company.contractor_identity
    if not company.contractor_full_name:
        errors['company_settings'] = ['Configura el nombre legal del contratista.']
    if not contractor_type or not contractor_number:
        errors['company_settings'] = ['Configura el NIT o la cédula del contratista.']
    if agreement.financed_balance <= 0:
        errors['financed_balance'] = ['El saldo financiado debe ser mayor que cero.']
    if agreement.hosting_value <= 0:
        errors['hosting_value'] = ['El costo vigente del Hosting debe ser mayor que cero.']
    if agreement.partnership_end_date <= agreement.partnership_start_date:
        errors['partnership_start_date'] = ['La vigencia de la alianza no es válida.']
    if errors:
        raise FinancingAgreementValidationError(errors)


def validate_agreement_ready(agreement):
    _ready_errors(agreement)
    _validate_source_links(
        agreement.client,
        agreement.source_proposal,
        agreement.source_project,
    )
    normalized = normalize_installment_schedule(
        agreement.installment_schedule,
        agreement.financed_balance,
    )
    last_due = date.fromisoformat(normalized[-1]['due_date'])
    if last_due > agreement.partnership_end_date:
        raise FinancingAgreementValidationError({
            'installment_schedule': [
                'La última cuota debe vencer dentro de la vigencia original de la alianza.',
            ],
        })
    validate_template_markdown(agreement.contract_markdown, require_core=True)
    agreement.installment_schedule = normalized


def _next_number():
    year = timezone.localdate().year
    try:
        sequence = FinancingAgreementNumberSequence.objects.select_for_update().get(
            year=year,
        )
    except FinancingAgreementNumberSequence.DoesNotExist:
        try:
            # Isolate the possible first-row race in a savepoint. Catching the
            # IntegrityError in the outer transition transaction would leave
            # that transaction unusable before we can lock the winning row.
            with transaction.atomic():
                FinancingAgreementNumberSequence.objects.create(year=year)
        except IntegrityError:
            pass
        sequence = FinancingAgreementNumberSequence.objects.select_for_update().get(
            year=year,
        )
    sequence.last_number += 1
    sequence.save(update_fields=['last_number', 'updated_at'])
    return f'OFIN-{year}-{sequence.last_number:03d}'


@transaction.atomic
def mark_ready(agreement, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status != FinancingAgreement.Status.DRAFT or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'Sólo un borrador activo puede marcarse como listo.',
        )
    validate_agreement_ready(agreement)
    before = _audit_state(agreement)
    if not agreement.number:
        agreement.number = _next_number()
    agreement.resolved_contract_markdown = resolve_agreement_markdown(
        agreement,
        draft=False,
        require_core=True,
    )
    agreement.resolved_contract_sha256 = hashlib.sha256(
        agreement.resolved_contract_markdown.encode('utf-8'),
    ).hexdigest()
    agreement.status = FinancingAgreement.Status.READY
    agreement.ready_at = timezone.now()
    agreement.ready_by = actor
    agreement.updated_by = actor
    agreement.save()
    _record_event(agreement, 'marked_ready', actor, before=before)
    return agreement


@transaction.atomic
def reopen_draft(agreement, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status != FinancingAgreement.Status.READY or agreement.signed_document:
        raise FinancingAgreementTransitionError(
            'Sólo un otrosí listo y aún no firmado puede volver a borrador.',
        )
    before = _audit_state(agreement)
    agreement.status = FinancingAgreement.Status.DRAFT
    agreement.resolved_contract_markdown = ''
    agreement.resolved_contract_sha256 = ''
    agreement.ready_at = None
    agreement.ready_by = None
    agreement.updated_by = actor
    agreement.save()
    _record_event(agreement, 'reopened', actor, before=before)
    return agreement


def validate_signed_pdf(uploaded_file):
    errors = {}
    if uploaded_file is None:
        errors['signed_document'] = ['Adjunta el PDF firmado.']
    else:
        filename = str(getattr(uploaded_file, 'name', '') or '')
        content_type = str(getattr(uploaded_file, 'content_type', '') or '').lower()
        if not filename.lower().endswith('.pdf'):
            errors['signed_document'] = ['El archivo debe tener extensión .pdf.']
        if content_type and content_type not in ('application/pdf', 'application/x-pdf'):
            errors['signed_document'] = ['El tipo de archivo debe ser PDF.']
        if getattr(uploaded_file, 'size', 0) > MAX_SIGNED_PDF_SIZE:
            errors['signed_document'] = ['El PDF no puede superar 15 MB.']
        header = uploaded_file.read(5)
        uploaded_file.seek(0)
        if header != b'%PDF-':
            errors['signed_document'] = ['El archivo no contiene una cabecera PDF válida.']
    if errors:
        raise FinancingAgreementValidationError(errors, code='invalid_signed_pdf')


@transaction.atomic
def register_signed_pdf(agreement, uploaded_file, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status != FinancingAgreement.Status.READY or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'El PDF firmado sólo puede registrarse desde un otrosí listo.',
        )
    validate_signed_pdf(uploaded_file)
    before = _audit_state(agreement)
    payload = uploaded_file.read()
    uploaded_file.seek(0)
    digest = hashlib.sha256(payload).hexdigest()
    agreement.signed_document.save('signed-agreement.pdf', uploaded_file, save=False)
    agreement.signed_document_sha256 = digest
    agreement.signed_document_size = len(payload)
    agreement.status = FinancingAgreement.Status.ACTIVE
    agreement.activated_at = timezone.now()
    agreement.activated_by = actor
    agreement.updated_by = actor
    agreement.save()
    _record_event(
        agreement,
        'signed_pdf_registered',
        actor,
        before=before,
        details={
            'original_filename': str(uploaded_file.name),
            'sha256': digest,
            'size': len(payload),
        },
    )
    return agreement


@transaction.atomic
def complete_agreement(agreement, *, actor, note):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status != FinancingAgreement.Status.ACTIVE or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'Sólo un otrosí activo puede marcarse como completado.',
        )
    note = str(note or '').strip()
    if not note:
        raise FinancingAgreementValidationError({
            'completion_note': [
                'Registra la certificación manual de pago íntegro.',
            ],
        })
    before = _audit_state(agreement)
    agreement.status = FinancingAgreement.Status.COMPLETED
    agreement.completed_at = timezone.now()
    agreement.completed_by = actor
    agreement.completion_note = note
    agreement.updated_by = actor
    agreement.save()
    _record_event(
        agreement,
        'completed',
        actor,
        before=before,
        details={'certification': note},
    )
    return agreement


@transaction.atomic
def cancel_agreement(agreement, *, actor, reason):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status not in {
        FinancingAgreement.Status.DRAFT,
        FinancingAgreement.Status.READY,
        FinancingAgreement.Status.ACTIVE,
    } or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'Este otrosí ya no admite cancelación.',
        )
    reason = str(reason or '').strip()
    if not reason:
        raise FinancingAgreementValidationError({
            'cancellation_reason': ['Explica por qué se cancela el otrosí.'],
        })
    before = _audit_state(agreement)
    agreement.status = FinancingAgreement.Status.CANCELLED
    agreement.cancelled_at = timezone.now()
    agreement.cancelled_by = actor
    agreement.cancellation_reason = reason
    agreement.updated_by = actor
    agreement.save()
    _record_event(
        agreement,
        'cancelled',
        actor,
        before=before,
        details={'reason': reason},
    )
    return agreement


@transaction.atomic
def archive_agreement(agreement, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if agreement.status not in {
        FinancingAgreement.Status.COMPLETED,
        FinancingAgreement.Status.CANCELLED,
    } or agreement.is_archived:
        raise FinancingAgreementTransitionError(
            'Sólo un otrosí completado o cancelado puede archivarse.',
        )
    before = _audit_state(agreement)
    agreement.is_archived = True
    agreement.archived_at = timezone.now()
    agreement.archived_by = actor
    agreement.updated_by = actor
    agreement.save()
    _record_event(agreement, 'archived', actor, before=before)
    return agreement


@transaction.atomic
def restore_agreement(agreement, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().get(pk=agreement.pk)
    if not agreement.is_archived:
        raise FinancingAgreementTransitionError('El otrosí no está archivado.')
    before = _audit_state(agreement)
    agreement.is_archived = False
    agreement.archived_at = None
    agreement.archived_by = None
    agreement.updated_by = actor
    agreement.save()
    _record_event(agreement, 'restored', actor, before=before)
    return agreement


def can_create_second_cycle(agreement):
    if (
        agreement.modality != FinancingAgreement.Modality.FIVE_YEAR
        or agreement.cycle_number != 1
        or agreement.status != FinancingAgreement.Status.COMPLETED
        or agreement.is_archived
    ):
        return False
    annotated = getattr(agreement, 'has_second_cycle_annotated', None)
    if annotated is not None:
        return not annotated
    if 'second_cycle' in agreement._state.fields_cache:
        return agreement._state.fields_cache['second_cycle'] is None
    return not FinancingAgreement.objects.filter(
        previous_agreement_id=agreement.pk,
    ).exists()


@transaction.atomic
def create_second_cycle(agreement, *, actor):
    agreement = FinancingAgreement.objects.select_for_update().select_related(
        'client', 'client__user', 'source_proposal', 'source_project',
    ).get(pk=agreement.pk)
    if not can_create_second_cycle(agreement):
        raise FinancingAgreementTransitionError(
            'El segundo ciclo exige una alianza de cinco años, primer ciclo '
            'completado y ausencia de otro ciclo previo.',
            code='second_cycle_unavailable',
        )
    template = FinancingAgreementTemplate.get_default()
    if template is None:
        raise FinancingAgreementValidationError({
            'template_id': ['No existe una plantilla de financiación activa.'],
        })
    now = timezone.now()
    second = FinancingAgreement.objects.create(
        client=agreement.client,
        source_proposal=agreement.source_proposal,
        source_project=agreement.source_project,
        client_full_name=agreement.client_full_name,
        client_company=agreement.client_company,
        client_id_type=agreement.client_id_type,
        client_id_number=agreement.client_id_number,
        client_email=agreement.client_email,
        client_phone=agreement.client_phone,
        original_contract_reference=agreement.original_contract_reference,
        original_contract_date=agreement.original_contract_date,
        project_name=agreement.project_name,
        financed_scope='',
        modality=FinancingAgreement.Modality.FIVE_YEAR,
        cycle_number=2,
        previous_agreement=agreement,
        partnership_start_date=agreement.partnership_start_date,
        partnership_end_date=agreement.partnership_end_date,
        currency=agreement.currency,
        total_value=Decimal('0.00'),
        initial_payment=Decimal('0.00'),
        financed_balance=Decimal('0.00'),
        hosting_value=agreement.hosting_value,
        hosting_period=agreement.hosting_period,
        installment_schedule=[],
        template=template,
        template_version=template.version,
        contract_markdown=template.content_markdown,
        second_cycle_approved_at=now,
        second_cycle_approved_by=actor,
        created_by=actor,
        updated_by=actor,
    )
    _record_event(
        agreement,
        'second_cycle_approved',
        actor,
        details={'second_agreement_id': second.pk},
    )
    _record_event(
        second,
        'created_second_cycle',
        actor,
        details={'previous_agreement_id': agreement.pk},
    )
    return second


def allowed_actions(agreement):
    if agreement.is_archived:
        actions = ['restore']
    elif agreement.status == FinancingAgreement.Status.DRAFT:
        actions = ['edit', 'download_draft', 'mark_ready', 'cancel']
    elif agreement.status == FinancingAgreement.Status.READY:
        actions = ['download_draft', 'reopen', 'upload_signed', 'cancel']
    elif agreement.status == FinancingAgreement.Status.ACTIVE:
        actions = ['download_signed', 'complete', 'cancel']
    elif agreement.status == FinancingAgreement.Status.COMPLETED:
        actions = ['download_signed']
        if can_create_second_cycle(agreement):
            actions.append('create_second_cycle')
        actions.append('archive')
    else:
        actions = ['download_signed'] if agreement.signed_document else []
        actions.append('archive')
    if agreement.signed_document and 'download_signed' not in actions:
        actions.append('download_signed')
    return actions
