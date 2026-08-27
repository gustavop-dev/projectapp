"""Lifecycle, duplicate drafts and bulk actions for recurring payments.

These writes deliberately bypass the generic accounting notification email.
They still create one audit row per changed recurring payment, but pausing a
subscription or silencing its reminder must not generate the noise those
actions exist to control.
"""
from django.db import transaction
from django.utils import timezone

from content.api_errors import ProposalActionError
from content.models import AccountingChangeLog, RecurringPayment
from content.services.accounting_service import (
    log_entity_diff,
    snapshot_values,
)
from content.services.recurring_schedule import next_charge_date
from content.utils import today_bogota


ENTITY = AccountingChangeLog.EntityType.RECURRING


class RecurringLifecycleError(ProposalActionError):
    """Lifecycle error carrying the exact rows a client must reconcile."""

    def __init__(self, message, *, record_ids=None, field='conflicting_ids', **kwargs):
        super().__init__(message, **kwargs)
        self.record_ids = sorted(set(record_ids or []))
        self.field = field


def build_duplicate_draft(payment, *, today=None):
    """Return a create-form prefill without persisting a copy.

    The stored anchor may be years old. A duplicate starts from the next
    occurrence calculated today instead, so the form never presents a stale
    historical date as the next charge of the new service.
    """
    today = today or today_bogota()
    next_due = next_charge_date(payment, today)
    requires_anchor = (
        next_due is None
        and payment.frequency != RecurringPayment.Frequency.MONTHLY
    )
    return {
        'name': payment.name,
        'price': format(payment.price, 'f'),
        'currency': payment.currency,
        'payment_method': payment.payment_method,
        'frequency': payment.frequency,
        'custom_months': payment.custom_months,
        'billing_day': payment.billing_day,
        'cycle_anchor_date': next_due.isoformat() if next_due else None,
        'cost_type': payment.cost_type,
        'category': payment.category_id,
        'is_active': True,
        'notes': '',
        'schedule_requires_anchor': requires_anchor,
        'schedule_notice': (
            'La fecha de referencia se recalculó con la próxima ocurrencia del original.'
            if next_due else
            'El original no tiene una próxima fecha calculable. Define una fecha de referencia antes de guardar.'
        ),
    }


def _save_diff(payment, old_values, user, update_fields):
    payment.save(update_fields=[*update_fields, 'updated_at'])
    log_entity_diff(ENTITY, payment, old_values, user)
    return payment


def set_active(payment, *, active, user):
    """Set active state idempotently; archived rows must be restored first."""
    if active and payment.is_archived:
        raise RecurringLifecycleError(
            'Un pago recurrente archivado no se puede activar.',
            record_ids=[payment.pk],
            code='recurring_archived',
            hint='Restáuralo primero; volverá inactivo para que puedas revisarlo.',
        )
    if payment.is_active == active:
        return payment
    old_values = snapshot_values(payment, ENTITY)
    payment.is_active = active
    return _save_diff(payment, old_values, user, ['is_active'])


def archive(payment, *, user):
    """Archive and pause a recurring payment without erasing its settings."""
    if payment.is_archived:
        return payment
    old_values = snapshot_values(payment, ENTITY)
    payment.is_archived = True
    payment.archived_at = timezone.now()
    payment.is_active = False
    return _save_diff(
        payment, old_values, user,
        ['is_archived', 'archived_at', 'is_active'],
    )


def restore(payment, *, user):
    """Restore as inactive so a cancelled service never resumes silently."""
    if not payment.is_archived:
        return payment
    old_values = snapshot_values(payment, ENTITY)
    payment.is_archived = False
    payment.archived_at = None
    payment.is_active = False
    return _save_diff(
        payment, old_values, user,
        ['is_archived', 'archived_at', 'is_active'],
    )


def set_reminder_mute(payment, *, muted, until, user):
    """Silence or resume notices while preserving the ordinary edit path."""
    if payment.is_archived:
        raise RecurringLifecycleError(
            'Los pagos archivados no generan avisos.',
            record_ids=[payment.pk],
            code='recurring_archived',
            hint='Restáuralo antes de cambiar su configuración de avisos.',
        )
    desired_until = until if muted else None
    if (
        payment.reminders_muted == muted
        and payment.reminders_muted_until == desired_until
    ):
        return payment
    old_values = snapshot_values(payment, ENTITY)
    payment.reminders_muted = muted
    payment.reminders_muted_until = desired_until
    return _save_diff(
        payment, old_values, user,
        ['reminders_muted', 'reminders_muted_until'],
    )


@transaction.atomic
def bulk_apply(record_ids, *, action, user):
    """Apply one lifecycle action to a complete, locked selection.

    Missing or archived conflicts are checked before the first mutation, so a
    stale browser selection can never produce a partially updated batch.
    """
    unique_ids = list(dict.fromkeys(record_ids))
    records = list(
        RecurringPayment.objects.select_for_update().filter(pk__in=unique_ids)
    )
    by_id = {record.pk: record for record in records}
    missing = [record_id for record_id in unique_ids if record_id not in by_id]
    if missing:
        raise RecurringLifecycleError(
            'Algunos pagos recurrentes seleccionados ya no existen.',
            record_ids=missing,
            field='missing_ids',
            code='records_not_found',
            hint='Actualiza la lista y vuelve a intentar la acción.',
        )

    ordered = [by_id[record_id] for record_id in unique_ids]
    if action == 'activate':
        archived = [record.pk for record in ordered if record.is_archived]
        if archived:
            raise RecurringLifecycleError(
                'La selección contiene pagos recurrentes archivados.',
                record_ids=archived,
                code='recurring_archived',
                hint='Restáuralos antes de activarlos.',
            )

    writers = {
        'activate': lambda record: set_active(record, active=True, user=user),
        'deactivate': lambda record: set_active(record, active=False, user=user),
        'archive': lambda record: archive(record, user=user),
    }
    writer = writers[action]
    updated = []
    for record in ordered:
        before = (
            record.is_active,
            record.is_archived,
            record.archived_at,
        )
        writer(record)
        after = (
            record.is_active,
            record.is_archived,
            record.archived_at,
        )
        if before != after:
            updated.append(record)
    return updated
