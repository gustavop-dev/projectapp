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

The date is the one field that cannot simply be copied, and it is the reason
duplicating opens the form instead of writing the row. When the hosting cycle
can be resolved the draft proposes it; otherwise the date comes back empty and
``cycle_options`` gives the form the candidate dates to fill it with in one
click. Neither path ever guesses silently — a wrong date already filled in is
worse than an empty one the operator is forced to complete.
"""
from content.models import HostingRecord, IncomeRecord
from content.serializers.accounting import money_str
from content.utils import add_months

HOSTING_CYCLE = 'hosting_cycle'

# Cadences the form offers so the next period is one click away when the
# hosting lookup below cannot resolve one on its own — which is the normal
# case, not the exception: the book is written as free-text concepts, so most
# incomes carry no ``origin`` and no client for it to work from.
CYCLE_OPTION_MONTHS = (1, 3, 6, 12)


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


def build_cycle_options(income):
    """One candidate next date per offered cadence, counted from the original.

    The dates are computed here rather than in the panel for two reasons: the
    frontend carries no date library — every date advance in this module is
    server-side by design — and ``add_months`` clamps the day, so a charge on
    the 31st lands on the last day of a shorter month instead of overflowing.

    Offering the dates is deliberately not the same as proposing one. The
    operator is who knows the cadence, so nothing is filled in behind their
    back: this only spares them from computing the date by hand.
    """
    return [
        {
            'months': months,
            'date': add_months(income.period_date, months).isoformat(),
        }
        for months in CYCLE_OPTION_MONTHS
    ]


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
        # Always offered, including when the hosting cycle already proposed a
        # date: the operator may well disagree with it, and these count from
        # the original's date, never from the proposal.
        'cycle_options': build_cycle_options(income),
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
