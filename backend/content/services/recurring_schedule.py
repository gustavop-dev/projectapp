"""When does a recurring payment get charged next?

Pure date arithmetic over a stored anchor. The anchor is any real charge of the
cycle; every future occurrence is derived from it, so there is no mutable "next
date" column to drift, to migrate, or to leave stale when a job fails.

Why an anchor and not just ``billing_day``: a day of the month cannot say
*which* month a quarterly or annual charge lands on. ``billing_day`` answers
"el 5 de cada mes" and nothing beyond monthly, which is why it stays as the
fallback for monthly records and why everything else needs the anchor.
"""
import calendar
from datetime import date


def add_months_clamped(anchor, months):
    """Shift ``anchor`` by whole months, clamping to the target month's length.

    Always call this with the ORIGINAL anchor and a total offset — never chain
    it from the previous result. Chaining loses the day permanently: a Jan-31
    monthly cycle would go 31 Jan -> 28 Feb -> 28 Mar and never recover the
    31st, whereas offsetting from the anchor gives 28 Feb -> 31 Mar. The same
    property is what keeps a 29-Feb annual anchor landing on 29 Feb in the next
    leap year instead of decaying to the 28th forever.
    """
    total = (anchor.year * 12 + anchor.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(anchor.day, last_day))


def next_monthly_occurrence(billing_day, today):
    """Next date landing on ``billing_day``, clamped, on or after ``today``."""
    def clamped(year, month):
        return min(billing_day, calendar.monthrange(year, month)[1])

    if today.day <= clamped(today.year, today.month):
        return date(today.year, today.month, clamped(today.year, today.month))
    year = today.year + (today.month // 12)
    month = today.month % 12 + 1
    return date(year, month, clamped(year, month))


def next_charge_date(payment, today):
    """First charge of ``payment`` on or after ``today``, or None if unknown.

    None is a legitimate answer, not a failure: a non-monthly payment without
    an anchor has no computable schedule, so it is excluded from the calendar
    rather than guessed at. The panel surfaces that as "sin fecha de cobro" so
    it reads as something to fill in, not as silence.
    """
    anchor = payment.cycle_anchor_date
    if anchor is None:
        if payment.frequency == payment.Frequency.MONTHLY and payment.billing_day:
            return next_monthly_occurrence(payment.billing_day, today)
        return None
    if anchor >= today:
        return anchor

    step = max(payment.frequency_months, 1)
    # Jump straight to the neighbourhood of today instead of stepping a cycle
    # at a time: an old anchor with a monthly cycle would otherwise loop for
    # every month since it was set.
    elapsed_months = (today.year - anchor.year) * 12 + (today.month - anchor.month)
    cycles = max(elapsed_months // step, 0)
    candidate = add_months_clamped(anchor, cycles * step)
    while candidate < today:
        cycles += 1
        candidate = add_months_clamped(anchor, cycles * step)
    return candidate
