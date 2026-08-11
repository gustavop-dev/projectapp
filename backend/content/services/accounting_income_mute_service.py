"""Silence (or resume) the payment-calendar notices of one expected income.

Its own service rather than the generic update path for one concrete reason:
``accounting_service.update_record`` notifies, so muting a receivable through
a plain PATCH would email both partners every time — the exact noise the
calendar exists to remove. Here the audit row is written by hand and no
notification is enqueued, so the action is recorded and silent, which are both
required: "¿por qué nunca me avisaron de esto?" has to be answerable.
"""
from content.models import AccountingChangeLog
from content.services.accounting_service import (
    compute_changes,
    log_accounting_change,
    object_repr,
    snapshot_values,
)

ENTITY = AccountingChangeLog.EntityType.INCOME


def set_income_reminder_mute(income, *, muted, until, user):
    """Apply the mute and audit the diff. Returns the updated income."""
    old_values = snapshot_values(income, ENTITY)
    income.reminders_muted = muted
    # An unmute always clears the resume date: leaving it behind would make a
    # later mute silently inherit a stale deadline.
    income.reminders_muted_until = until if muted else None
    income.save(update_fields=[
        'reminders_muted', 'reminders_muted_until', 'updated_at',
    ])

    changes = compute_changes(ENTITY, old_values, snapshot_values(income, ENTITY))
    if changes:
        log_accounting_change(
            entity_type=ENTITY,
            object_id=income.pk,
            object_repr=object_repr(ENTITY, income),
            action=AccountingChangeLog.Action.UPDATED,
            changes=changes,
            actor=user,
        )
    return income
