"""Tests for multi-phase hosting billing: per-phase costs, summed activation,
and prorated phase onboarding.

Covers:
- accounts.services.hosting_billing: phase_billing_amount, project_billing_amount,
  prorated_amount
- project_subscription_view POST: subscription sums started phases only
- accounts.tasks._onboard_due_phases: prorated catch-up payment + billing recompute
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import HostingSubscription, Payment, Project, ProjectPhase, UserProfile
from accounts.services import hosting_billing
from accounts.tasks import _onboard_due_phases

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='client@mp.com', email='client@mp.com', password='clientpass1',
        first_name='Carla', last_name='Mora',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@mp.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Multi Phase Project', client=client_user, status=Project.STATUS_ACTIVE,
    )


def _proposal(total):
    """A BusinessProposal pinned to 40% hosting / 10% / 20% discounts.

    hosting_percent is set explicitly (not left to the model default) so the
    billing-math assertions below stay stable regardless of the production
    default.
    """
    from content.models import BusinessProposal
    return BusinessProposal.objects.create(
        title=f'Proposal {total}', client_name='Test', total_investment=Decimal(total),
        hosting_percent=40,
    )


def _phase(project, total, order, start_date=None, activated_at=None):
    return ProjectPhase.objects.create(
        project=project, business_proposal=_proposal(total), order=order,
        hosting_start_date=start_date, hosting_activated_at=activated_at,
    )


# ===========================================================================
# hosting_billing service
# ===========================================================================

class TestHostingBilling:
    def test_phase_billing_amount_per_frequency(self, project):
        # total 12,000,000 * 40% / 12 = 400,000 monthly base
        phase = _phase(project, 12_000_000, order=1)
        assert hosting_billing.phase_billing_amount(phase, 'monthly') == Decimal('400000')
        # quarterly: 400000 * 3 * 0.90
        assert hosting_billing.phase_billing_amount(phase, 'quarterly') == Decimal('1080000')
        # semiannual: 400000 * 6 * 0.80
        assert hosting_billing.phase_billing_amount(phase, 'semiannual') == Decimal('1920000')

    def test_project_billing_amount_sums_only_activated_phases(self, project):
        _phase(project, 12_000_000, order=1, activated_at=date(2026, 1, 1))
        _phase(project, 6_000_000, order=2)  # not activated
        # only the activated phase counts: 1,920,000
        assert hosting_billing.project_billing_amount(project, 'semiannual') == Decimal('1920000')

    def test_project_billing_amount_sums_all_activated(self, project):
        _phase(project, 12_000_000, order=1, activated_at=date(2026, 1, 1))
        _phase(project, 6_000_000, order=2, activated_at=date(2026, 1, 1))
        # 1,920,000 + 960,000
        assert hosting_billing.project_billing_amount(project, 'semiannual') == Decimal('2880000')

    def test_prorated_amount_partial_cycle(self, project):
        phase = _phase(project, 12_000_000, order=1)  # monthly amount 400,000
        # 10-day cycle, joining on day 6 -> 5 of 10 days remain -> half
        result = hosting_billing.prorated_amount(
            phase, 'monthly',
            join_date=date(2026, 1, 6),
            cycle_start=date(2026, 1, 1),
            cycle_end=date(2026, 1, 10),
        )
        assert result == Decimal('200000')

    def test_prorated_amount_zero_outside_cycle(self, project):
        phase = _phase(project, 12_000_000, order=1)
        result = hosting_billing.prorated_amount(
            phase, 'monthly',
            join_date=date(2026, 2, 1),
            cycle_start=date(2026, 1, 1),
            cycle_end=date(2026, 1, 10),
        )
        assert result == Decimal('0')

    def test_prorated_amount_ignores_frequency_discount(self, project):
        """Proration uses the full (undiscounted) rate, not the plan discount."""
        phase = _phase(project, 12_000_000, order=1)  # monthly base 400,000
        # A whole cycle on the semiannual plan -> the full undiscounted amount.
        result = hosting_billing.prorated_amount(
            phase, 'semiannual',
            join_date=date(2026, 1, 1),
            cycle_start=date(2026, 1, 1),
            cycle_end=date(2026, 1, 10),
        )
        # 400,000 * 6 months, NOT 1,920,000 (the 20%-discounted semiannual price)
        assert result == Decimal('2400000')
        assert result > hosting_billing.phase_billing_amount(phase, 'semiannual')


# ===========================================================================
# Multi-phase activation
# ===========================================================================

class TestMultiPhaseActivation:
    def _url(self, project):
        return f'/api/accounts/projects/{project.id}/subscription/'

    def test_activation_sums_started_phases(self, api_client, client_headers, project):
        _phase(project, 12_000_000, order=1)
        _phase(project, 6_000_000, order=2)
        resp = api_client.post(self._url(project), {'plan': 'semiannual'}, **client_headers)
        assert resp.status_code == 201
        assert Decimal(resp.json()['billing_amount']) == Decimal('2880000')

    def test_activation_excludes_future_phase(self, api_client, client_headers, project):
        _phase(project, 12_000_000, order=1)
        future = _phase(project, 6_000_000, order=2, start_date=date.today() + timedelta(days=90))
        resp = api_client.post(self._url(project), {'plan': 'semiannual'}, **client_headers)
        assert resp.status_code == 201
        assert Decimal(resp.json()['billing_amount']) == Decimal('1920000')
        future.refresh_from_db()
        assert future.hosting_activated_at is None

    def test_activation_rejects_when_no_started_phase(self, api_client, client_headers, project):
        _phase(project, 12_000_000, order=1, start_date=date.today() + timedelta(days=30))
        _phase(project, 6_000_000, order=2, start_date=date.today() + timedelta(days=30))
        resp = api_client.post(self._url(project), {'plan': 'semiannual'}, **client_headers)
        assert resp.status_code == 400


# ===========================================================================
# Phase onboarding cron (_onboard_due_phases)
# ===========================================================================

class TestPhaseOnboarding:
    def _active_subscription(self, project):
        return HostingSubscription.objects.create(
            project=project, plan=HostingSubscription.PLAN_SEMIANNUAL,
            base_monthly_amount=Decimal('400000'), discount_percent=0,
            effective_monthly_amount=Decimal('320000'), billing_amount=Decimal('1920000'),
            status=HostingSubscription.STATUS_ACTIVE,
            start_date=date(2026, 1, 1), next_billing_date=date(2026, 7, 1),
        )

    def test_onboards_due_phase_with_prorated_payment(self, project):
        _phase(project, 12_000_000, order=1, start_date=date(2026, 1, 1),
               activated_at=date(2026, 1, 1))
        phase2 = _phase(project, 6_000_000, order=2, start_date=date(2026, 3, 1))
        sub = self._active_subscription(project)

        count = _onboard_due_phases()

        assert count == 1
        phase2.refresh_from_db()
        sub.refresh_from_db()
        assert phase2.hosting_activated_at is not None
        # recurring total grew to include phase 2: 1,920,000 + 960,000
        assert sub.billing_amount == Decimal('2880000')
        # a prorated catch-up payment was created, charged at the full
        # (undiscounted) rate — phase 2 monthly base 200,000 * 6 = 1,200,000
        prorated = Payment.objects.filter(subscription=sub, description__icontains='prorrateado')
        assert prorated.count() == 1
        assert Decimal('0') < prorated.first().amount < Decimal('1200000')

    def test_skips_phase_without_subscription(self, project):
        phase = _phase(project, 6_000_000, order=1, start_date=date(2026, 3, 1))
        count = _onboard_due_phases()
        assert count == 0
        phase.refresh_from_db()
        assert phase.hosting_activated_at is None


# ===========================================================================
# Frequency change while the subscription is still pending
# ===========================================================================

class TestFrequencyChangeWhilePending:
    def _activate(self, api_client, headers, project, plan='quarterly'):
        return api_client.post(
            f'/api/accounts/projects/{project.id}/subscription/', {'plan': plan}, **headers,
        )

    def test_client_changes_plan_while_pending_realigns_first_payment(
        self, api_client, client_headers, project,
    ):
        _phase(project, 12_000_000, order=1)
        assert self._activate(api_client, client_headers, project, 'quarterly').status_code == 201

        resp = api_client.patch(
            f'/api/accounts/projects/{project.id}/subscription/',
            {'plan': 'semiannual'}, format='json', **client_headers,
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()['billing_amount']) == Decimal('1920000')
        # the unpaid first payment is realigned to the new frequency
        sub = HostingSubscription.objects.get(project=project)
        first = Payment.objects.filter(subscription=sub).order_by('billing_period_start').first()
        assert first.amount == Decimal('1920000')

    def test_client_cannot_change_plan_after_active(
        self, api_client, client_headers, project,
    ):
        _phase(project, 12_000_000, order=1)
        self._activate(api_client, client_headers, project, 'quarterly')
        sub = HostingSubscription.objects.get(project=project)
        sub.status = HostingSubscription.STATUS_ACTIVE
        sub.save(update_fields=['status'])

        resp = api_client.patch(
            f'/api/accounts/projects/{project.id}/subscription/',
            {'plan': 'semiannual'}, format='json', **client_headers,
        )
        assert resp.status_code == 403


class TestFirstBillingDate:
    """Free month + always-bill-on-the-1st date logic (pure function)."""

    @pytest.mark.parametrize('delivery,expected', [
        (date(2026, 6, 28), date(2026, 8, 1)),   # mid-month -> 1st of following month
        (date(2026, 7, 10), date(2026, 9, 1)),   # early month, still >= 1 free month
        (date(2026, 7, 1), date(2026, 8, 1)),    # on the 1st -> exactly one free month
        (date(2026, 12, 15), date(2027, 2, 1)),  # year rollover
    ])
    def test_first_billing_date(self, delivery, expected):
        assert hosting_billing.first_billing_date(delivery) == expected


class TestAnnualPlan:
    """Annual (12-month) hosting plan: discount + billing amount."""

    def test_plan_discount_annual_uses_model_field(self, project):
        phase = _phase(project, 12_000_000, order=1)
        assert hosting_billing.plan_discount(
            phase, HostingSubscription.PLAN_ANNUAL,
        ) == Decimal('40')

    def test_annual_billing_amount(self, project):
        # monthly base 12,000,000 * 40% / 12 = 400,000; annual = 400,000 * 12 * 0.60
        phase = _phase(project, 12_000_000, order=1)
        assert hosting_billing.phase_billing_amount(
            phase, HostingSubscription.PLAN_ANNUAL,
        ) == Decimal('2880000')
