"""Shared "is this notice due today?" rule for the accounting calendar.

Pure date arithmetic: no models, no DB, no settings. Three entities announce a
date on the same shape of schedule — a few descending milestones before it, and
optionally a repeating reminder once it passes — so the rule lives here once:

    expected incomes      milestones (15, 7, 0), repeat every 7 or 14 days
    recurring payments    milestones (15, 7, 0), no repeat
    hosting expiry        milestones (15, 7),    repeat every 5 days

The hosting cadence predates this module and its behaviour is preserved
bit-for-bit; ``hosting_expiry_service`` delegates here, and its test file is the
executable proof of the equivalence.

Two properties the callers depend on:

* **A missed run is not a missed notice.** Everything is derived from today's
  ``days_left``, never from how many times the job ran. If the consumer is down
  from 12 days out until 3 days past the date, the next run still fires once,
  in the band it is actually in.
* **A record created late announces itself immediately** instead of staying
  silent because it was born after its own milestone.
"""


def milestone_index(days_left, milestones):
    """How many descending milestones have been reached at ``days_left``.

    With ``milestones=(15, 7, 0)``:
        days_left > 15  -> 0   (outside the window)
        15 .. 8         -> 1   (first notice)
        7 .. 1          -> 2   (second notice)
        <= 0            -> 3   (the day itself, and every day after)

    The due date and the days after it share the last band on purpose: entering
    the band is the "vence hoy" notice, and the repeat interval governs from
    there. Narrowing that band to ``days_left < 0`` would silently drop the
    notice on the date itself.
    """
    return sum(1 for milestone in milestones if days_left <= milestone)


def is_notice_due(*, target_date, last_sent_at, today, milestones,
                  repeat_every_days=None):
    """Whether ``target_date`` should be announced today.

    ``last_sent_at`` is the last day this record was announced, or None when it
    never was (a fresh record, or one whose date moved and was re-armed).
    ``repeat_every_days=None`` means the cadence stops once the final milestone
    has been announced — which is what makes a recurring payment go quiet after
    its charge day instead of nagging about a cycle nobody is chasing.
    """
    reached = milestone_index((target_date - today).days, milestones)
    if reached == 0:
        return False
    if last_sent_at is None:
        return True
    reached_at_last_sent = milestone_index(
        (target_date - last_sent_at).days, milestones,
    )
    if reached > reached_at_last_sent:
        # A new milestone was crossed since the last notice.
        return True
    if reached == len(milestones) and repeat_every_days:
        return (today - last_sent_at).days >= repeat_every_days
    return False
