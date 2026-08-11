"""Tests for the shared notice cadence (15/7/due-day + optional repeat)."""
from datetime import date, timedelta

from content.services.accounting_notice_cadence import (
    is_notice_due,
    milestone_index,
)

DUE = date(2026, 9, 1)
INCOME_MILESTONES = (15, 7, 0)
HOSTING_MILESTONES = (15, 7)


def due(days_left, last_sent_days_left=None, milestones=INCOME_MILESTONES,
        repeat_every_days=14):
    """Is a notice due when the date is `days_left` away?

    `last_sent_days_left` expresses the previous notice the same way — how far
    the date was when it went out — which is how the cadence itself reasons.
    """
    today = DUE - timedelta(days=days_left)
    last_sent = (
        None if last_sent_days_left is None
        else DUE - timedelta(days=last_sent_days_left)
    )
    return is_notice_due(
        target_date=DUE,
        last_sent_at=last_sent,
        today=today,
        milestones=milestones,
        repeat_every_days=repeat_every_days,
    )


class TestMilestoneIndex:
    def test_bands_for_an_income(self):
        reached = [milestone_index(d, INCOME_MILESTONES) for d in (16, 15, 8, 7, 1, 0, -1)]
        assert reached == [0, 1, 1, 2, 2, 3, 3]

    def test_the_due_day_shares_the_band_with_the_days_after_it(self):
        # Narrowing this band to days_left < 0 would silently drop the notice
        # on the date itself, which is one of the three the operator asked for.
        assert milestone_index(0, INCOME_MILESTONES) == 3
        assert milestone_index(-30, INCOME_MILESTONES) == 3

    def test_bands_for_a_hosting(self):
        reached = [milestone_index(d, HOSTING_MILESTONES) for d in (16, 15, 8, 7, -5)]
        assert reached == [0, 1, 1, 2, 2]


class TestPreviousNotices:
    def test_silent_before_the_window(self):
        assert due(16) is False

    def test_first_notice_at_15_days(self):
        assert due(15) is True

    def test_no_repeat_inside_the_same_band(self):
        assert due(12, last_sent_days_left=15) is False

    def test_second_notice_when_crossing_7_days(self):
        assert due(7, last_sent_days_left=15) is True

    def test_third_notice_on_the_due_day(self):
        assert due(0, last_sent_days_left=7) is True


class TestResilience:
    def test_a_record_created_late_announces_itself_immediately(self):
        # Born at 3 days out: it fires now rather than staying silent for
        # having missed its own 15-day milestone.
        assert due(3, last_sent_days_left=None) is True

    def test_a_record_created_after_the_date_announces_itself_immediately(self):
        assert due(-40, last_sent_days_left=None) is True

    def test_a_missed_milestone_still_fires_once_the_job_returns(self):
        # Consumer down from 12 days out until 3 days past the date: the run
        # that comes back fires once, in the band it is actually in.
        assert due(-3, last_sent_days_left=12) is True


class TestOverdueRepeat:
    def test_silent_the_day_after_the_due_day_notice(self):
        assert due(-1, last_sent_days_left=0) is False

    def test_repeats_after_a_fortnight(self):
        assert due(-14, last_sent_days_left=0) is True

    def test_weekly_setting_repeats_after_a_week(self):
        assert due(-7, last_sent_days_left=0, repeat_every_days=7) is True
        assert due(-6, last_sent_days_left=0, repeat_every_days=7) is False

    def test_without_a_repeat_the_cadence_stops_at_the_due_day(self):
        # This is what keeps a recurring payment from nagging about a cycle
        # nobody is chasing.
        assert due(-60, last_sent_days_left=0, repeat_every_days=None) is False
