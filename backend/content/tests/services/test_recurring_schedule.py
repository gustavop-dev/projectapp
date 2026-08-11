"""Tests for the recurring next-charge projection (anchor + frequency)."""
from datetime import date

from content.models import RecurringPayment
from content.services.recurring_schedule import (
    add_months_clamped,
    next_charge_date,
    next_monthly_occurrence,
)

TODAY = date(2026, 8, 11)


class FakePayment:
    """Only the four attributes the projection reads."""

    Frequency = RecurringPayment.Frequency

    def __init__(self, frequency='monthly', anchor=None, billing_day=None,
                 custom_months=None):
        self.frequency = frequency
        self.cycle_anchor_date = anchor
        self.billing_day = billing_day
        self.custom_months = custom_months

    @property
    def frequency_months(self):
        if self.frequency == 'custom':
            return self.custom_months or 1
        return RecurringPayment.FREQUENCY_MONTHS.get(self.frequency, 1)


class TestAddMonthsClamped:
    def test_clamps_onto_a_shorter_month(self):
        assert add_months_clamped(date(2026, 1, 31), 1) == date(2026, 2, 28)

    def test_the_day_is_recovered_because_offsets_run_from_the_anchor(self):
        # Chaining (28 feb + 1 month) would give 28 mar and lose the 31st for
        # good; offsetting from the anchor restores it.
        anchor = date(2026, 1, 31)
        assert add_months_clamped(anchor, 2) == date(2026, 3, 31)
        assert add_months_clamped(anchor, 3) == date(2026, 4, 30)

    def test_crosses_the_year_boundary(self):
        assert add_months_clamped(date(2026, 11, 15), 3) == date(2027, 2, 15)


class TestNextChargeDate:
    def test_a_future_anchor_is_itself_the_next_charge(self):
        payment = FakePayment(anchor=date(2026, 9, 5))
        assert next_charge_date(payment, TODAY) == date(2026, 9, 5)

    def test_an_anchor_landing_today_is_the_next_charge(self):
        payment = FakePayment(anchor=TODAY)
        assert next_charge_date(payment, TODAY) == TODAY

    def test_monthly_projects_forward_from_an_old_anchor(self):
        payment = FakePayment(anchor=date(2024, 3, 20))
        assert next_charge_date(payment, TODAY) == date(2026, 8, 20)

    def test_monthly_rolls_to_next_month_once_the_day_has_passed(self):
        payment = FakePayment(anchor=date(2024, 3, 5))
        assert next_charge_date(payment, TODAY) == date(2026, 9, 5)

    def test_a_month_end_anchor_does_not_drift(self):
        payment = FakePayment(anchor=date(2026, 1, 31))
        assert next_charge_date(payment, date(2026, 2, 1)) == date(2026, 2, 28)
        assert next_charge_date(payment, date(2026, 3, 1)) == date(2026, 3, 31)

    def test_an_annual_leap_day_anchor_returns_to_29_february(self):
        payment = FakePayment(frequency='annual', anchor=date(2024, 2, 29))
        assert next_charge_date(payment, date(2025, 1, 1)) == date(2025, 2, 28)
        assert next_charge_date(payment, date(2028, 1, 1)) == date(2028, 2, 29)

    def test_quarterly_lands_on_the_cycle_not_the_next_month(self):
        payment = FakePayment(frequency='quarterly', anchor=date(2026, 1, 10))
        assert next_charge_date(payment, TODAY) == date(2026, 10, 10)

    def test_annual_projects_a_year_at_a_time(self):
        payment = FakePayment(frequency='annual', anchor=date(2023, 5, 2))
        assert next_charge_date(payment, TODAY) == date(2027, 5, 2)

    def test_custom_frequency_uses_its_own_month_count(self):
        payment = FakePayment(frequency='custom', custom_months=5,
                              anchor=date(2026, 1, 10))
        assert next_charge_date(payment, TODAY) == date(2026, 11, 10)


class TestWithoutAnAnchor:
    def test_monthly_falls_back_to_the_billing_day(self):
        payment = FakePayment(billing_day=20)
        assert next_charge_date(payment, TODAY) == date(2026, 8, 20)

    def test_the_billing_day_fallback_clamps_in_february(self):
        assert next_monthly_occurrence(31, date(2026, 2, 5)) == date(2026, 2, 28)

    def test_a_non_monthly_payment_has_no_computable_schedule(self):
        payment = FakePayment(frequency='annual', billing_day=20)
        assert next_charge_date(payment, TODAY) is None

    def test_a_monthly_payment_without_a_billing_day_has_none_either(self):
        assert next_charge_date(FakePayment(), TODAY) is None
