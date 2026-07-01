"""Business logic for the accounting module.

Every mutation goes through create_record/update_record/delete_record:
the same function mutates, writes the AccountingChangeLog row and
enqueues the email notification (the established convention — explicit
logging in services, not signals).
"""
import logging
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from content.api_errors import ProposalActionError
from content.models import (
    AccountingChangeLog,
    AdsSpendRecord,
    CardBalanceSnapshot,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)
from content.serializers.accounting import month_label, month_period

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
}

TRACKED_FIELDS = {
    EntityType.INCOME: [
        ('concept', 'Concepto'),
        ('kind', 'Tipo'),
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
        ('period_date', 'Período'),
        ('category', 'Categoría'),
        ('paid_from', 'Pagado desde'),
        ('total_amount', 'Monto total'),
        ('gustavo_amount', 'Monto Gustavo'),
        ('carlos_amount', 'Monto Carlos'),
        ('notes', 'Notas'),
    ],
    EntityType.HOSTING: [
        ('client_name', 'Cliente'),
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
    EntityType.SETTINGS: [
        ('notification_recipients', 'Destinatarios de notificación'),
        ('notifications_enabled', 'Notificaciones activas'),
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

def _ensure_editable(entity_type, instance):
    if entity_type == EntityType.POCKET and instance.is_auto_managed:
        raise ProposalActionError(
            'Este movimiento del bolsillo es gestionado automáticamente por '
            'un ingreso o gasto vinculado.',
            code='auto_managed_movement',
            hint='Edita o elimina el ingreso/gasto que lo genera.',
        )


def create_record(entity_type, serializer, user):
    """Persist a validated write serializer, audit it and notify."""
    instance = serializer.save(created_by=user)
    _sync_pocket(entity_type, instance, user)
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
    _ensure_editable(entity_type, instance)
    old_values = snapshot_values(instance, entity_type)
    instance = serializer.save()
    _sync_pocket(entity_type, instance, user)
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


def delete_record(entity_type, instance, user):
    """Delete a record (and its auto pocket movement), audit and notify."""
    _ensure_editable(entity_type, instance)
    deleted_id = instance.pk
    deleted_repr = object_repr(entity_type, instance)
    old_values = snapshot_values(instance, entity_type)
    changes = [
        {'field': field, 'label': label, 'old': old_values[field], 'new': ''}
        for field, label in TRACKED_FIELDS[entity_type]
        if old_values[field] != ''
    ]

    linked_movement = None
    if entity_type in (EntityType.INCOME, EntityType.EXPENSE):
        linked_movement = instance.pocket_movement

    instance.delete()

    if linked_movement is not None:
        _log_pocket_removal(linked_movement, user)
        linked_movement.delete()

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

def _sync_pocket(entity_type, instance, user):
    if entity_type == EntityType.INCOME:
        _sync_movement(
            instance,
            wants_movement=(
                instance.kind == IncomeRecord.Kind.LIQUID
                and instance.destination == IncomeRecord.Destination.POCKET
            ),
            direction=PocketMovement.Direction.IN,
            concept=f'Ingreso: {instance.concept}',
            movement_date=instance.period_date,
            source_ref=f'income:{instance.pk}',
            user=user,
        )
    elif entity_type == EntityType.EXPENSE:
        _sync_movement(
            instance,
            wants_movement=(
                instance.paid_from == ExpenseRecord.PaidFrom.POCKET
            ),
            direction=PocketMovement.Direction.OUT,
            concept=f'Gasto: {instance.concept}',
            movement_date=instance.period_date,
            source_ref=f'expense:{instance.pk}',
            user=user,
        )


def _sync_movement(
    record, *, wants_movement, direction, concept, movement_date,
    source_ref, user,
):
    """Create/mirror/remove the auto-managed pocket movement of a record.

    Auto movements are audited (the pocket ledger history stays complete)
    but do NOT send their own email — the income/expense email covers it.
    """
    movement = record.pocket_movement

    if wants_movement and movement is None:
        movement = PocketMovement.objects.create(
            concept=concept,
            movement_date=movement_date,
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
        movement.concept = concept
        movement.movement_date = movement_date
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


def _log_pocket_removal(movement, user):
    old_values = snapshot_values(movement, EntityType.POCKET)
    log_accounting_change(
        entity_type=EntityType.POCKET,
        object_id=movement.pk,
        object_repr=movement.concept,
        action=Action.DELETED,
        changes=[
            {'field': field, 'label': label, 'old': old_values[field], 'new': ''}
            for field, label in TRACKED_FIELDS[EntityType.POCKET]
            if old_values[field] != ''
        ],
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
    inflow = _sum(
        queryset.filter(direction=PocketMovement.Direction.IN), 'amount',
    )
    outflow = _sum(
        queryset.filter(direction=PocketMovement.Direction.OUT), 'amount',
    )
    return inflow - outflow


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


def partner_totals(year):
    """Expected/liquid income, expenses and net per partner + company."""
    expected = _split_sums(IncomeRecord.objects.filter(
        kind=IncomeRecord.Kind.EXPECTED, period_date__year=year,
    ))
    liquid = _split_sums(IncomeRecord.objects.filter(
        kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
    ))
    expenses = _split_sums(
        ExpenseRecord.objects.filter(period_date__year=year),
    )
    return {
        party: {
            'expected': expected[party],
            'liquid': liquid[party],
            'expenses': expenses[party],
            'net': liquid[party] - expenses[party],
        }
        for party in ('gustavo', 'carlos', 'company')
    }


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
        ),
        'period_date', 'total_amount',
    )
    liquid_by_month = _totals_by_month(
        IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
        ),
        'period_date', 'total_amount',
    )
    expenses_by_month = _totals_by_month(
        ExpenseRecord.objects.filter(period_date__year=year),
        'period_date', 'total_amount',
    )

    breakdown = []
    for month in range(1, 13):
        from datetime import date

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


def recurring_monthly_cost():
    """Sum of active recurring payments prorated to a monthly COP cost."""
    return sum(
        (
            payment.monthly_cop_cost
            for payment in RecurringPayment.objects.filter(is_active=True)
        ),
        Decimal('0'),
    )


def latest_card_snapshots():
    """Newest snapshot per card name."""
    card_names = (
        CardBalanceSnapshot.objects
        .order_by()  # clear Meta ordering so DISTINCT applies to card_name only
        .values_list('card_name', flat=True)
        .distinct()
    )
    snapshots = []
    for name in card_names:
        snapshot = (
            CardBalanceSnapshot.objects
            .filter(card_name=name)
            .order_by('-snapshot_date', '-created_at')
            .first()
        )
        if snapshot:
            snapshots.append({
                'card_name': snapshot.card_name,
                'snapshot_date': snapshot.snapshot_date,
                'available_amount': snapshot.available_amount,
                'debt_amount': snapshot.debt_amount,
            })
    return snapshots


def dashboard_summary(year):
    """Single payload feeding the accounting dashboard."""
    expected_total = _sum(
        IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.EXPECTED, period_date__year=year,
        ),
        'total_amount',
    )
    liquid_total = _sum(
        IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, period_date__year=year,
        ),
        'total_amount',
    )
    expenses_total = _sum(
        ExpenseRecord.objects.filter(period_date__year=year), 'total_amount',
    )
    today = timezone.localdate()
    active_hostings = HostingRecord.objects.filter(is_active=True)

    return {
        'year': year,
        'expected_total': expected_total,
        'liquid_total': liquid_total,
        'difference': liquid_total - expected_total,
        'expenses_total': expenses_total,
        'expected_utility': expected_total - expenses_total,
        'liquid_utility': liquid_total - expenses_total,
        'pocket_balance': pocket_balance(),
        'partners': partner_totals(year),
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
            'active_count': active_hostings.count(),
            'monthly_income': _sum(active_hostings, 'monthly_value'),
            'total_paid': _sum(HostingRecord.objects.all(), 'total_paid'),
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
