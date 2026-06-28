"""
Hosting billing calculations for multi-phase projects.

A project's hosting subscription bills the sum of all its activated phases at
a single frequency (monthly/quarterly/semiannual/annual). Each phase derives
its price from its own BusinessProposal. A phase that starts mid-cycle is
charged a prorated amount for the remaining days of the current billing cycle.
"""
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta

from accounts.models import HostingSubscription


def _q(value):
    """Quantize a value to whole COP, rounding half-up."""
    return Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def first_billing_date(delivery_date):
    """First hosting billing date for a new subscription.

    Hosting billing always starts on the 1st of a calendar month. The client
    receives a free hosting period from ``delivery_date`` (when they pay the
    project delivery) until this date, which is always at least one full month.

    Examples (delivery -> first billing): Jun 28 -> Aug 1; Jul 10 -> Sep 1;
    Jul 1 -> Aug 1. Anchoring on the 1st keeps every later cycle month-aligned.
    """
    target = delivery_date + relativedelta(months=1)
    if target.day != 1:
        target = target.replace(day=1) + relativedelta(months=1)
    return target


def phase_monthly_base(phase):
    """Monthly hosting base for one phase, derived from its proposal pricing."""
    bp = phase.business_proposal
    total = Decimal(str(getattr(bp, 'total_investment', None) or 0))
    percent = Decimal(str(getattr(bp, 'hosting_percent', 80) or 0))
    return _q(total * percent / Decimal('100') / Decimal('12'))


def plan_discount(phase, plan):
    """Discount percent that applies to a phase at a given plan."""
    bp = phase.business_proposal
    if plan == HostingSubscription.PLAN_QUARTERLY:
        return Decimal(str(getattr(bp, 'hosting_discount_quarterly', 0) or 0))
    if plan == HostingSubscription.PLAN_SEMIANNUAL:
        return Decimal(str(getattr(bp, 'hosting_discount_semiannual', 0) or 0))
    if plan == HostingSubscription.PLAN_ANNUAL:
        return Decimal(str(getattr(bp, 'hosting_discount_annual', 0) or 0))
    return Decimal('0')


def phase_billing_amount(phase, plan):
    """Full billing amount for one phase at a given plan/frequency."""
    months = HostingSubscription.PLAN_MONTHS.get(plan, 1)
    factor = (Decimal('100') - plan_discount(phase, plan)) / Decimal('100')
    return _q(phase_monthly_base(phase) * Decimal(months) * factor)


def phase_tiers(phase):
    """The billing tiers for one phase (client breakdown table), one per plan.

    Iterates over every plan in PLAN_CHOICES so a newly added frequency (e.g.
    annual) is surfaced automatically without touching this function.
    """
    plan_labels = dict(HostingSubscription.PLAN_CHOICES)
    tiers = []
    for plan, _label in HostingSubscription.PLAN_CHOICES:
        months = HostingSubscription.PLAN_MONTHS[plan]
        amount = phase_billing_amount(phase, plan)
        tiers.append({
            'frequency': plan,
            'label': plan_labels.get(plan, plan),
            'months': months,
            'discount_percent': int(plan_discount(phase, plan)),
            'monthly_equivalent': int(_q(amount / Decimal(months))),
            'billing_amount': int(amount),
        })
    return tiers


def activated_phases(project):
    """Phases already incorporated into the recurring subscription billing."""
    return (
        project.phases.filter(hosting_activated_at__isnull=False)
        .select_related('business_proposal')
    )


def project_billing_amount(project, plan):
    """Recurring billing amount for a project = sum of activated phases."""
    return sum(
        (phase_billing_amount(p, plan) for p in activated_phases(project)),
        Decimal('0'),
    )


def prorated_amount(phase, plan, join_date, cycle_start, cycle_end):
    """
    Prorated charge for a phase that joins the subscription mid-cycle.

    Charged at the FULL (undiscounted) rate: the frequency discount only
    rewards committing to a whole prepaid cycle, so a partial catch-up does
    not earn it.

    daily rate = undiscounted cycle amount / days in the current cycle
    charge     = daily rate * days remaining from join_date to cycle_end

    Returns Decimal('0') when the join falls outside the cycle.
    """
    months = HostingSubscription.PLAN_MONTHS.get(plan, 1)
    full = phase_monthly_base(phase) * Decimal(months)
    cycle_days = (cycle_end - cycle_start).days + 1
    remaining_days = (cycle_end - join_date).days + 1
    if cycle_days <= 0 or remaining_days <= 0:
        return Decimal('0')
    remaining_days = min(remaining_days, cycle_days)
    return _q(full * Decimal(remaining_days) / Decimal(cycle_days))
