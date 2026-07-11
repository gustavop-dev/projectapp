"""Business logic for the accounting module.

Every mutation goes through create_record/update_record/delete_record:
the same function mutates, writes the AccountingChangeLog row and
enqueues the email notification (the established convention — explicit
logging in services, not signals).

Pocket <-> income/expense sync invariant: exactly two one-way sync
writers exist. `_sync_pocket` (record -> movement) and `_sync_from_pocket`
(movement -> record) each write the other side with plain ORM
create()/save(update_fields=...) and never re-enter the service pipeline,
so ping-pong loops are impossible by construction.
"""
import logging
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum

from content.api_errors import ProposalActionError
from content.utils import format_cop_email, today_bogota
from content.models import (
    AccountingChangeLog,
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCardStatement,
    CreditCardTransaction,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    Ledger,
    MerchantAlias,
    PocketMovement,
    RecurringPayment,
)
from content.serializers.accounting import month_label, month_period, split_half

logger = logging.getLogger(__name__)

EntityType = AccountingChangeLog.EntityType
Action = AccountingChangeLog.Action

ENTITY_MODELS = {
    EntityType.INCOME: IncomeRecord,
    EntityType.EXPENSE: ExpenseRecord,
    EntityType.HOSTING: HostingRecord,
    EntityType.POCKET: PocketMovement,
    EntityType.RECURRING: RecurringPayment,
    EntityType.ADS: AdsSpendRecord,
    EntityType.CARD_SNAPSHOT: CardBalanceSnapshot,
    EntityType.STATEMENT: CreditCardStatement,
    EntityType.STATEMENT_TX: CreditCardTransaction,
    EntityType.MERCHANT_ALIAS: MerchantAlias,
}

TRACKED_FIELDS = {
    EntityType.INCOME: [
        ('concept', 'Concepto'),
        ('kind', 'Tipo'),
        ('ledger', 'Contabilidad'),
        ('period_date', 'Período'),
        ('destination', 'Destino'),
        ('total_amount', 'Monto total'),
        ('gustavo_amount', 'Monto Gustavo'),
        ('carlos_amount', 'Monto Carlos'),
        ('expected_income', 'Ingreso esperado'),
        ('notes', 'Notas'),
    ],
    EntityType.EXPENSE: [
        ('concept', 'Concepto'),
        ('ledger', 'Contabilidad'),
        ('period_date', 'Período'),
        ('category', 'Categoría'),
        ('total_amount', 'Monto total'),
        ('gustavo_amount', 'Monto Gustavo'),
        ('carlos_amount', 'Monto Carlos'),
        ('notes', 'Notas'),
    ],
    EntityType.HOSTING: [
        ('client_name', 'Cliente'),
        ('client_email', 'Email del cliente'),
        ('client_contact_name', 'Contacto del cliente'),
        ('client_identification', 'Identificación del cliente'),
        ('domain_url', 'Dominio'),
        ('monthly_value', 'Valor mensual'),
        ('payment_modality', 'Modalidad de pago'),
        ('benefit', 'Beneficio'),
        ('valid_from', 'Vigente desde'),
        ('valid_to', 'Vigente hasta'),
        ('cycles_count', 'Ciclos'),
        ('payment_per_cycle', 'Pago por ciclo'),
        ('total_paid', 'Total pagado'),
        ('is_active', 'Activo'),
        ('notes', 'Notas'),
    ],
    EntityType.POCKET: [
        ('concept', 'Concepto'),
        ('movement_date', 'Fecha'),
        ('direction', 'Tipo'),
        ('amount', 'Valor'),
        ('notes', 'Notas'),
    ],
    EntityType.RECURRING: [
        ('name', 'Nombre'),
        ('price', 'Precio'),
        ('currency', 'Moneda'),
        ('cop_equivalent', 'Equivalente COP'),
        ('payment_method', 'Método de pago'),
        ('frequency', 'Frecuencia'),
        ('billing_day', 'Día de cobro'),
        ('cost_type', 'Tipo de costo'),
        ('is_active', 'Activo'),
        ('notes', 'Notas'),
    ],
    EntityType.ADS: [
        ('spend_date', 'Fecha'),
        ('platform', 'Plataforma'),
        ('origin_card', 'Tarjeta origen'),
        ('amount', 'Valor'),
        ('notes', 'Notas'),
    ],
    EntityType.CARD_SNAPSHOT: [
        ('snapshot_date', 'Fecha'),
        ('card_name', 'Tarjeta'),
        ('available_amount', 'Disponible'),
        ('debt_amount', 'Deuda'),
        ('notes', 'Notas'),
    ],
    EntityType.STATEMENT: [
        ('card_name', 'Tarjeta'),
        ('period_date', 'Período'),
        ('status', 'Estado'),
        ('purchases_total', 'Total compras'),
        ('previous_balance', 'Saldo anterior'),
        ('payments_total', 'Pagos y abonos'),
        ('interest_and_fees', 'Intereses y comisiones'),
        ('closing_balance', 'Saldo de cierre'),
        ('minimum_payment', 'Pago mínimo'),
        ('due_date', 'Fecha límite de pago'),
        ('notes', 'Notas'),
    ],
    EntityType.STATEMENT_TX: [
        ('transaction_date', 'Fecha'),
        ('raw_description', 'Descripción'),
        ('merchant_name', 'Comercio'),
        ('category', 'Categoría'),
        ('amount', 'Valor'),
        ('original_amount', 'Valor original'),
        ('original_currency', 'Moneda original'),
        ('installment_number', 'Cuota'),
        ('installments_total', 'Total cuotas'),
        ('is_identified', 'Identificado'),
        ('notes', 'Notas'),
    ],
    EntityType.MERCHANT_ALIAS: [
        ('match_text', 'Texto de coincidencia'),
        ('merchant_name', 'Comercio'),
        ('default_category', 'Categoría por defecto'),
        ('notes', 'Notas'),
    ],
    EntityType.SETTINGS: [
        ('notification_recipients', 'Destinatarios de notificación'),
        ('notifications_enabled', 'Notificaciones activas'),
        ('card_reminder_enabled', 'Recordatorio de deuda de tarjetas'),
        ('hosting_expiry_reminder_enabled', 'Avisos de vencimiento de hostings'),
        ('usd_exchange_rate', 'Tasa de cambio USD'),
    ],
}


# ── Audit core ──

def display_value(instance, field_name):
    """Human-readable value of a field (choice display when available)."""
    display_getter = getattr(instance, f'get_{field_name}_display', None)
    if callable(display_getter):
        return str(display_getter())
    value = getattr(instance, field_name)
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Sí' if value else 'No'
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    if isinstance(value, Decimal):
        # Money field: audit rows and emails show COP formatting.
        return f'${format_cop_email(value)}'
    return str(value)


def snapshot_values(instance, entity_type):
    """Map of tracked field -> displayed value for diffing."""
    return {
        field: display_value(instance, field)
        for field, _label in TRACKED_FIELDS[entity_type]
    }


def compute_changes(entity_type, old_values, new_values):
    """Field-level diff as the JSON stored in AccountingChangeLog.changes."""
    return [
        {
            'field': field,
            'label': label,
            'old': old_values.get(field, ''),
            'new': new_values.get(field, ''),
        }
        for field, label in TRACKED_FIELDS[entity_type]
        if old_values.get(field, '') != new_values.get(field, '')
    ]


def object_repr(entity_type, instance):
    """Human-readable identity stored on the audit row."""
    if entity_type in (EntityType.INCOME, EntityType.EXPENSE, EntityType.POCKET):
        return instance.concept
    if entity_type == EntityType.HOSTING:
        return instance.client_name
    if entity_type == EntityType.RECURRING:
        return instance.name
    if entity_type == EntityType.ADS:
        return f'{instance.get_platform_display()} — {instance.spend_date}'
    if entity_type == EntityType.CARD_SNAPSHOT:
        return f'{instance.card_name} — {instance.snapshot_date}'
    if entity_type == EntityType.STATEMENT:
        return f'{instance.card_name} — {month_label(instance.period_date)}'
    if entity_type == EntityType.STATEMENT_TX:
        return instance.merchant_name or instance.raw_description
    if entity_type == EntityType.MERCHANT_ALIAS:
        return instance.match_text
    return 'Configuración contable'


def log_accounting_change(
    *,
    entity_type,
    object_id,
    object_repr,
    action,
    changes=None,
    actor=None,
):
    """Append an AccountingChangeLog row."""
    return AccountingChangeLog.objects.create(
        entity_type=entity_type,
        object_id=object_id,
        object_repr=object_repr[:255],
        action=action,
        changes=changes or [],
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        actor_username=getattr(actor, 'username', '') or '',
    )


def _notify(change_log):
    """Enqueue the change email; failures never break the mutation."""
    try:
        from content.tasks import send_accounting_change_email

        send_accounting_change_email(change_log.id)
    except Exception:
        logger.warning(
            'Could not enqueue accounting notification (change_log=%s)',
            change_log.id,
            exc_info=True,
        )


# ── Generic mutation pipeline ──

def _ensure_pocket_update_allowed(entity_type, instance, serializer):
    """Linked movements mirror an income/expense; their direction is fixed."""
    if entity_type != EntityType.POCKET or not instance.is_auto_managed:
        return
    new_direction = serializer.validated_data.get('direction')
    if new_direction and new_direction != instance.direction:
        raise ProposalActionError(
            'La dirección de un movimiento vinculado a un ingreso o gasto '
            'no se puede cambiar.',
            code='linked_direction_locked',
            hint='Elimina el movimiento y créalo de nuevo con la otra dirección.',
        )


def _pop_mirror_ledger(entity_type, serializer):
    """Extract the write-only pocket `ledger` field (not a model field)."""
    if entity_type != EntityType.POCKET:
        return None
    return serializer.validated_data.pop('ledger', None)


def create_record(entity_type, serializer, user):
    """Persist a validated write serializer, audit it and notify."""
    mirror_ledger = _pop_mirror_ledger(entity_type, serializer)
    with transaction.atomic():
        instance = serializer.save(created_by=user)
        _sync_pocket(entity_type, instance, user, is_create=True)
        if entity_type == EntityType.POCKET:
            _sync_from_pocket(instance, mirror_ledger, user, is_create=True)
    new_values = snapshot_values(instance, entity_type)
    changes = compute_changes(entity_type, {}, new_values)
    change_log = log_accounting_change(
        entity_type=entity_type,
        object_id=instance.pk,
        object_repr=object_repr(entity_type, instance),
        action=Action.CREATED,
        changes=changes,
        actor=user,
    )
    _notify(change_log)
    return instance


def update_record(entity_type, instance, serializer, user):
    """Apply a validated partial update, audit the diff and notify."""
    _ensure_pocket_update_allowed(entity_type, instance, serializer)
    mirror_ledger = _pop_mirror_ledger(entity_type, serializer)
    old_values = snapshot_values(instance, entity_type)
    with transaction.atomic():
        instance = serializer.save()
        _sync_pocket(entity_type, instance, user, is_create=False)
        if entity_type == EntityType.POCKET:
            _sync_from_pocket(instance, mirror_ledger, user, is_create=False)
    changes = compute_changes(
        entity_type, old_values, snapshot_values(instance, entity_type),
    )
    if changes:
        change_log = log_accounting_change(
            entity_type=entity_type,
            object_id=instance.pk,
            object_repr=object_repr(entity_type, instance),
            action=Action.UPDATED,
            changes=changes,
            actor=user,
        )
        _notify(change_log)
    return instance


def _deletion_changes(entity_type, old_values):
    """Diff payload for a deletion: every non-empty field as old -> ''."""
    return [
        {'field': field, 'label': label, 'old': old_values[field], 'new': ''}
        for field, label in TRACKED_FIELDS[entity_type]
        if old_values[field] != ''
    ]


def delete_record(entity_type, instance, user):
    """Delete a record and its linked counterpart, audit and notify.

    A linked pocket movement and its income/expense are one money event:
    deleting either side hard-deletes the other (an orphan would silently
    diverge the pocket balance from the records).
    """
    deleted_id = instance.pk
    deleted_repr = object_repr(entity_type, instance)
    old_values = snapshot_values(instance, entity_type)
    changes = _deletion_changes(entity_type, old_values)

    linked_movement = None
    linked_record = None
    linked_record_type = None
    if entity_type in (EntityType.INCOME, EntityType.EXPENSE):
        linked_movement = instance.pocket_movement
    elif entity_type == EntityType.POCKET:
        # Capture before deleting: the record FK is SET_NULL on delete.
        linked_record = instance.linked_record
        if linked_record is not None:
            linked_record_type = (
                EntityType.INCOME
                if isinstance(linked_record, IncomeRecord)
                else EntityType.EXPENSE
            )

    with transaction.atomic():
        instance.delete()
        if linked_movement is not None:
            _log_pocket_removal(linked_movement, user)
            linked_movement.delete()
        if linked_record is not None:
            _log_record_removal(linked_record_type, linked_record, user)
            linked_record.delete()

    change_log = log_accounting_change(
        entity_type=entity_type,
        object_id=deleted_id,
        object_repr=deleted_repr,
        action=Action.DELETED,
        changes=changes,
        actor=user,
    )
    _notify(change_log)


# ── Income/Expense ↔ Pocket side effects ──

def _sync_pocket(entity_type, instance, user, *, is_create):
    if entity_type == EntityType.INCOME:
        _sync_movement(
            instance,
            wants_movement=(
                instance.kind == IncomeRecord.Kind.LIQUID
                and instance.destination == IncomeRecord.Destination.POCKET
            ),
            direction=PocketMovement.Direction.IN,
            source_ref=f'income:{instance.pk}',
            user=user,
        )
    elif entity_type == EntityType.EXPENSE:
        # Every new expense draws from the pocket. Historical expenses
        # (created before the linkage existed) stay unlinked: updating
        # one never creates a movement retroactively.
        _sync_movement(
            instance,
            wants_movement=is_create or instance.pocket_movement is not None,
            direction=PocketMovement.Direction.OUT,
            source_ref=f'expense:{instance.pk}',
            user=user,
        )


def _sync_movement(record, *, wants_movement, direction, source_ref, user):
    """Create/mirror/remove the linked pocket movement of a record.

    Linked movements are audited (the pocket ledger history stays complete)
    but do NOT send their own email — the income/expense email covers it.
    The concept mirrors the record verbatim (no prefix) so edits stay
    invertible from the pocket side.
    """
    movement = record.pocket_movement

    if wants_movement and movement is None:
        movement = PocketMovement.objects.create(
            concept=record.concept,
            movement_date=record.period_date,
            direction=direction,
            amount=record.total_amount,
            source_ref=source_ref,
            created_by=user if getattr(user, 'is_authenticated', False) else None,
        )
        record.pocket_movement = movement
        record.save(update_fields=['pocket_movement', 'updated_at'])
        log_accounting_change(
            entity_type=EntityType.POCKET,
            object_id=movement.pk,
            object_repr=movement.concept,
            action=Action.CREATED,
            changes=compute_changes(
                EntityType.POCKET, {},
                snapshot_values(movement, EntityType.POCKET),
            ),
            actor=user,
        )
    elif wants_movement and movement is not None:
        old_values = snapshot_values(movement, EntityType.POCKET)
        movement.concept = record.concept
        # The record only carries month granularity; a same-month period
        # keeps the exact day chosen on the pocket side.
        period = record.period_date
        if (movement.movement_date.year, movement.movement_date.month) != (
            period.year, period.month,
        ):
            movement.movement_date = period
        movement.amount = record.total_amount
        movement.save(update_fields=[
            'concept', 'movement_date', 'amount', 'updated_at',
        ])
        changes = compute_changes(
            EntityType.POCKET, old_values,
            snapshot_values(movement, EntityType.POCKET),
        )
        if changes:
            log_accounting_change(
                entity_type=EntityType.POCKET,
                object_id=movement.pk,
                object_repr=movement.concept,
                action=Action.UPDATED,
                changes=changes,
                actor=user,
            )
    elif not wants_movement and movement is not None:
        _log_pocket_removal(movement, user)
        record.pocket_movement = None
        record.save(update_fields=['pocket_movement', 'updated_at'])
        movement.delete()


def _default_split(ledger, total):
    """Partner split applied to records mirrored from the pocket side."""
    if ledger == Ledger.GUSTAVO:
        return total, Decimal('0')
    if ledger == Ledger.CARLOS:
        return Decimal('0'), total
    return split_half(total)


def _sync_from_pocket(movement, mirror_ledger, user, *, is_create):
    """Create/mirror the income/expense record of a pocket movement.

    Counterpart of `_sync_movement`. Writes the record with plain ORM
    calls — never through create_record/update_record — so the two sync
    writers cannot re-enter each other. Setting `pocket_movement` at
    creation also keeps a later `_sync_movement` for that record in its
    idempotent mirror branch (no duplicate movements).
    Mirrored records are audited without their own email — the pocket
    email covers the user action.
    """
    linked = movement.linked_record

    if linked is None:
        if not is_create:
            # Historical movement created before the linkage existed.
            return
        ledger = mirror_ledger or Ledger.COMPANY
        gustavo, carlos = _default_split(ledger, movement.amount)
        common = {
            'concept': movement.concept,
            'period_date': movement.movement_date.replace(day=1),
            'ledger': ledger,
            'total_amount': movement.amount,
            'gustavo_amount': gustavo,
            'carlos_amount': carlos,
            'source_ref': f'pocket:{movement.pk}',
            'pocket_movement': movement,
            'created_by': (
                user if getattr(user, 'is_authenticated', False) else None
            ),
        }
        if movement.direction == PocketMovement.Direction.IN:
            record_type = EntityType.INCOME
            record = IncomeRecord.objects.create(
                kind=IncomeRecord.Kind.LIQUID,
                destination=IncomeRecord.Destination.POCKET,
                **common,
            )
        else:
            record_type = EntityType.EXPENSE
            record = ExpenseRecord.objects.create(
                category=(
                    ExpenseRecord.Category.BUSINESS
                    if ledger == Ledger.COMPANY
                    else ExpenseRecord.Category.PERSONAL
                ),
                **common,
            )
        log_accounting_change(
            entity_type=record_type,
            object_id=record.pk,
            object_repr=object_repr(record_type, record),
            action=Action.CREATED,
            changes=compute_changes(
                record_type, {}, snapshot_values(record, record_type),
            ),
            actor=user,
        )
        return

    record_type = (
        EntityType.INCOME
        if isinstance(linked, IncomeRecord)
        else EntityType.EXPENSE
    )
    old_values = snapshot_values(linked, record_type)
    linked.concept = movement.concept
    update_fields = ['concept', 'updated_at']
    if (linked.period_date.year, linked.period_date.month) != (
        movement.movement_date.year, movement.movement_date.month,
    ):
        linked.period_date = movement.movement_date.replace(day=1)
        update_fields.append('period_date')
    ledger = mirror_ledger or linked.ledger
    if movement.amount != linked.total_amount or ledger != linked.ledger:
        # The pocket modal has no split editor: amount/ledger edits from
        # the pocket side reset the split to the ledger default. Custom
        # splits are edited from the Ingresos/Gastos tabs.
        gustavo, carlos = _default_split(ledger, movement.amount)
        linked.ledger = ledger
        linked.total_amount = movement.amount
        linked.gustavo_amount = gustavo
        linked.carlos_amount = carlos
        update_fields += [
            'ledger', 'total_amount', 'gustavo_amount', 'carlos_amount',
        ]
    linked.save(update_fields=update_fields)
    changes = compute_changes(
        record_type, old_values, snapshot_values(linked, record_type),
    )
    if changes:
        log_accounting_change(
            entity_type=record_type,
            object_id=linked.pk,
            object_repr=object_repr(record_type, linked),
            action=Action.UPDATED,
            changes=changes,
            actor=user,
        )


def _log_pocket_removal(movement, user):
    old_values = snapshot_values(movement, EntityType.POCKET)
    log_accounting_change(
        entity_type=EntityType.POCKET,
        object_id=movement.pk,
        object_repr=movement.concept,
        action=Action.DELETED,
        changes=_deletion_changes(EntityType.POCKET, old_values),
        actor=user,
    )


def _log_record_removal(entity_type, record, user):
    """Silent DELETED audit row for a record cascaded from its movement."""
    old_values = snapshot_values(record, entity_type)
    log_accounting_change(
        entity_type=entity_type,
        object_id=record.pk,
        object_repr=object_repr(entity_type, record),
        action=Action.DELETED,
        changes=_deletion_changes(entity_type, old_values),
        actor=user,
    )


# ── Aggregations ──

def _sum(queryset, field):
    return queryset.aggregate(total=Sum(field))['total'] or Decimal('0')


def pocket_balance(as_of=None):
    """Current pocket balance: Sum(in) - Sum(out) up to `as_of`."""
    queryset = PocketMovement.objects.all()
    if as_of:
        queryset = queryset.filter(movement_date__lte=as_of)
    totals = queryset.aggregate(
        inflow=Sum('amount', filter=Q(direction=PocketMovement.Direction.IN)),
        outflow=Sum('amount', filter=Q(direction=PocketMovement.Direction.OUT)),
    )
    return (totals['inflow'] or Decimal('0')) - (totals['outflow'] or Decimal('0'))


def _split_sums(queryset):
    aggregate = queryset.aggregate(
        total=Sum('total_amount'),
        gustavo=Sum('gustavo_amount'),
        carlos=Sum('carlos_amount'),
    )
    total = aggregate['total'] or Decimal('0')
    gustavo = aggregate['gustavo'] or Decimal('0')
    carlos = aggregate['carlos'] or Decimal('0')
    return {
        'total': total,
        'gustavo': gustavo,
        'carlos': carlos,
        'company': total - gustavo - carlos,
    }


def _year_split_sums(year):
    """The three company-ledger aggregates every year summary derives from.

    Personal-ledger records never count toward company totals.
    """
    return {
        'expected': _split_sums(IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.EXPECTED, period_date__year=year,
            ledger=Ledger.COMPANY,
        )),
        'liquid': _split_sums(IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
            ledger=Ledger.COMPANY,
        )),
        'expenses': _split_sums(ExpenseRecord.objects.filter(
            period_date__year=year, ledger=Ledger.COMPANY,
        )),
    }


def _personal_sums(year):
    """Per-partner totals of their personal-ledger records."""
    result = {}
    for party in (Ledger.GUSTAVO, Ledger.CARLOS):
        result[str(party)] = {
            'expected': _sum(IncomeRecord.objects.filter(
                kind=IncomeRecord.Kind.EXPECTED, period_date__year=year,
                ledger=party,
            ), 'total_amount'),
            'liquid': _sum(IncomeRecord.objects.filter(
                kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
                ledger=party,
            ), 'total_amount'),
            'expenses': _sum(ExpenseRecord.objects.filter(
                period_date__year=year, ledger=party,
            ), 'total_amount'),
        }
    return result


def _build_partner_totals(sums, personal):
    """Partner cards combine company participation + personal ledger.

    The `company` card is the company ledger itself (its full totals),
    not the per-row unassigned residue.
    """
    totals = {}
    for party in ('gustavo', 'carlos'):
        participation = {
            key: sums[key][party]
            for key in ('expected', 'liquid', 'expenses')
        }
        own = personal[party]
        totals[party] = {
            'expected': participation['expected'] + own['expected'],
            'liquid': participation['liquid'] + own['liquid'],
            'expenses': participation['expenses'] + own['expenses'],
            'net': (
                participation['liquid'] + own['liquid']
                - participation['expenses'] - own['expenses']
            ),
            'participation': participation,
            'personal': own,
        }
    totals['company'] = {
        'expected': sums['expected']['total'],
        'liquid': sums['liquid']['total'],
        'expenses': sums['expenses']['total'],
        'net': sums['liquid']['total'] - sums['expenses']['total'],
    }
    return totals


def partner_totals(year):
    """Expected/liquid income, expenses and net per partner + company."""
    return _build_partner_totals(_year_split_sums(year), _personal_sums(year))


def _totals_by_month(queryset, date_field, amount_field):
    rows = (
        queryset
        .order_by()  # clear Meta ordering so GROUP BY stays month-only
        .values_list(f'{date_field}__month')
        .annotate(total=Sum(amount_field))
    )
    return {month: (total or Decimal('0')) for month, total in rows}


def monthly_breakdown(year):
    """Twelve rows of expected/liquid/expenses/utility for the dashboard."""
    expected_by_month = _totals_by_month(
        IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.EXPECTED, period_date__year=year,
            ledger=Ledger.COMPANY,
        ),
        'period_date', 'total_amount',
    )
    liquid_by_month = _totals_by_month(
        IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
            ledger=Ledger.COMPANY,
        ),
        'period_date', 'total_amount',
    )
    expenses_by_month = _totals_by_month(
        ExpenseRecord.objects.filter(
            period_date__year=year, ledger=Ledger.COMPANY,
        ),
        'period_date', 'total_amount',
    )

    breakdown = []
    for month in range(1, 13):
        month_date = date(year, month, 1)
        expected = expected_by_month.get(month, Decimal('0'))
        liquid = liquid_by_month.get(month, Decimal('0'))
        expenses = expenses_by_month.get(month, Decimal('0'))
        breakdown.append({
            'period': month_period(month_date),
            'label': month_label(month_date),
            'expected': expected,
            'liquid': liquid,
            'expenses': expenses,
            'expected_utility': expected - expenses,
            'utility': liquid - expenses,
        })
    return breakdown


def recurring_monthly_cost(queryset=None):
    """Sum of active recurring payments prorated to a monthly COP cost."""
    if queryset is None:
        queryset = RecurringPayment.objects.filter(is_active=True)
    return sum(
        (payment.monthly_cop_cost for payment in queryset),
        Decimal('0'),
    )


def latest_card_snapshots():
    """Newest snapshot per card name (single query, few rows per card)."""
    snapshots = []
    seen_cards = set()
    for snapshot in CardBalanceSnapshot.objects.order_by(
        'card_name', '-snapshot_date', '-created_at',
    ):
        if snapshot.card_name in seen_cards:
            continue
        seen_cards.add(snapshot.card_name)
        snapshots.append({
            'card_name': snapshot.card_name,
            'snapshot_date': snapshot.snapshot_date,
            'available_amount': snapshot.available_amount,
            'debt_amount': snapshot.debt_amount,
        })
    return snapshots


def dashboard_summary(year):
    """Single payload feeding the accounting dashboard."""
    sums = _year_split_sums(year)
    expected_total = sums['expected']['total']
    liquid_total = sums['liquid']['total']
    expenses_total = sums['expenses']['total']
    today = today_bogota()
    hostings = HostingRecord.objects.aggregate(
        active_count=Count('id', filter=Q(is_active=True)),
        monthly_income=Sum('monthly_value', filter=Q(is_active=True)),
        total_paid=Sum('total_paid'),
    )

    return {
        'year': year,
        'expected_total': expected_total,
        'liquid_total': liquid_total,
        'difference': liquid_total - expected_total,
        'expenses_total': expenses_total,
        'expected_utility': expected_total - expenses_total,
        'liquid_utility': liquid_total - expenses_total,
        'pocket_balance': pocket_balance(),
        'partners': _build_partner_totals(sums, _personal_sums(year)),
        'monthly': monthly_breakdown(year),
        'recurring_monthly_cost': recurring_monthly_cost(),
        'ads': {
            'year_total': _sum(
                AdsSpendRecord.objects.filter(spend_date__year=year),
                'amount',
            ),
            'current_month_total': _sum(
                AdsSpendRecord.objects.filter(
                    spend_date__year=today.year,
                    spend_date__month=today.month,
                ),
                'amount',
            ),
        },
        'hostings': {
            'active_count': hostings['active_count'] or 0,
            'monthly_income': hostings['monthly_income'] or Decimal('0'),
            'total_paid': hostings['total_paid'] or Decimal('0'),
        },
        'latest_card_snapshots': latest_card_snapshots(),
    }


def ads_with_accumulated(queryset):
    """Records ordered chronologically with a running `accumulated` sum."""
    records = list(queryset.order_by('spend_date', 'created_at', 'id'))
    running = Decimal('0')
    for record in records:
        running += record.amount
        record.accumulated = running
    return records
