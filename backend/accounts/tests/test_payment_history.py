import pytest
from decimal import Decimal

from accounts.models import HostingSubscription, Payment, PaymentHistory, Project, UserProfile
from accounts.services.payment_history import record_payment_status_change
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRecordPaymentStatusChange:
    def test_skips_when_status_unchanged(self):
        user = User.objects.create_user(username='ph1@test.com', email='ph1@test.com', password='pass')
        project = Project.objects.create(name='P', client=user)
        sub = HostingSubscription.objects.create(
            project=project, plan='monthly',
            base_monthly_amount=Decimal('1'), discount_percent=0,
            effective_monthly_amount=Decimal('1'), billing_amount=Decimal('1'),
            start_date='2026-01-01',
            status=HostingSubscription.STATUS_ACTIVE,
        )
        pay = Payment.objects.create(
            subscription=sub, amount=Decimal('1'),
            billing_period_start='2026-01-01', billing_period_end='2026-01-31',
            due_date='2026-01-01', status=Payment.STATUS_PENDING,
        )

        record_payment_status_change(pay, Payment.STATUS_PENDING, Payment.STATUS_PENDING)

        assert PaymentHistory.objects.filter(payment=pay).count() == 0

    def test_creates_row_on_transition(self):
        user = User.objects.create_user(username='ph2@test.com', email='ph2@test.com', password='pass')
        UserProfile.objects.create(
            user=user, role=UserProfile.ROLE_CLIENT,
            is_onboarded=True, profile_completed=True,
        )
        project = Project.objects.create(name='P', client=user)
        sub = HostingSubscription.objects.create(
            project=project, plan='monthly',
            base_monthly_amount=Decimal('1'), discount_percent=0,
            effective_monthly_amount=Decimal('1'), billing_amount=Decimal('1'),
            start_date='2026-01-01',
            status=HostingSubscription.STATUS_ACTIVE,
        )
        pay = Payment.objects.create(
            subscription=sub, amount=Decimal('1'),
            billing_period_start='2026-01-01', billing_period_end='2026-01-31',
            due_date='2026-01-01', status=Payment.STATUS_PENDING,
        )

        record_payment_status_change(
            pay, Payment.STATUS_PENDING, Payment.STATUS_PROCESSING, source='api',
        )

        h = PaymentHistory.objects.get(payment=pay)
        assert h.from_status == Payment.STATUS_PENDING
        assert h.to_status == Payment.STATUS_PROCESSING
        assert h.source == 'api'
