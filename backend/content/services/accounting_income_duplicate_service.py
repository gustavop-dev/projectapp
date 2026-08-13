"""Prefill for duplicating an income — opening the next period of a charge.

Persists nothing. The panel opens its income form with this payload so the
date or the amount can be adjusted before confirming, and the record is then
created through the ordinary create endpoint: that is what keeps the audit
row, the pocket sync and the notification identical to any other income.

Two rules carry the intent of the action:

* the draft is always ``expected``, whatever the original was — duplicating a
  collected hosting to open its next cycle is the whole use case;
* nothing belonging to the original occurrence travels. Its settlement links,
  its cuenta de cobro, its deductions, its silenced calendar and its history
  all stay behind. Most of that is free (they are reverse relations, or fields
  the write serializer cannot set), so the draft simply omits them.
"""
from content.models import HostingRecord, IncomeRecord
from content.serializers.accounting import money_str
from content.utils import add_months

HOSTING_CYCLE = 'hosting_cycle'


def resolve_hosting_cycle_months(income):
    """Months of the hosting cycle behind this income, or None.

    An income does not record which hosting it belongs to — ``origin`` is a
    label, not a link — so the hosting is resolved by client, narrowed by
    project when the income has one. Only an unambiguous match counts: with no
    hosting, or with several disagreeing on the modality, proposing a date
    would be guessing, and a wrong date already filled in is worse than an
    empty one the operator is forced to complete.
    """
    if income.origin != IncomeRecord.Origin.HOSTING or not income.client_id:
        return None
    hostings = HostingRecord.objects.filter(
        is_active=True, client_id=income.client_id,
    )
    if income.project_id:
        hostings = hostings.filter(project_id=income.project_id)
    modalities = set(hostings.values_list('payment_modality', flat=True))
    if len(modalities) != 1:
        return None
    return HostingRecord.MODALITY_MONTHS.get(modalities.pop())


def next_period_date(income):
    """The date one cycle after this income's, or None when unknown.

    ``add_months`` clamps the day, so a charge on the 31st lands on the last
    day of a shorter month instead of overflowing into the next one.
    """
    months = resolve_hosting_cycle_months(income)
    if not months:
        return None
    return add_months(income.period_date, months)


def build_income_duplicate_draft(income):
    """Return the prefill for a new income copied from ``income``."""
    from accounts.services.proposal_client_service import (
        build_client_display_name,
    )

    period_date = next_period_date(income)
    return {
        'concept': income.concept,
        # Always pending, whatever the original was. Pocket is a liquid-only
        # destination server-side, so it resets along with the kind.
        'kind': IncomeRecord.Kind.EXPECTED,
        'destination': IncomeRecord.Destination.PARTNERS,
        'period_date': period_date.isoformat() if period_date else None,
        'period_date_source': HOSTING_CYCLE if period_date else None,
        'ledger': income.ledger,
        'client': income.client_id,
        # Same shape as the list rows: the form shows this as the label of the
        # client picker, and None keeps "sin cliente" distinct from a blank.
        'client_name': (
            build_client_display_name(income.client) if income.client_id else None
        ),
        'project': income.project_id,
        'project_name': income.project.name if income.project_id else None,
        'origin': income.origin,
        'total_amount': money_str(income.total_amount),
        'gustavo_amount': money_str(income.gustavo_amount),
        'carlos_amount': money_str(income.carlos_amount),
        'notes': income.notes,
    }
