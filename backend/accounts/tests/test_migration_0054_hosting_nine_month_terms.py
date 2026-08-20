from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model

from accounts.models import HostingSubscription, Payment, Project, SavedFilterTab


pytestmark = pytest.mark.django_db
migration = import_module('accounts.migrations.0054_hosting_nine_month_terms')
User = get_user_model()


def make_project(name='Proyecto'):
    user = User.objects.create_user(
        username=f'{name.lower()}@example.com',
        email=f'{name.lower()}@example.com',
    )
    return Project.objects.create(name=name, client=user)


def make_annual_subscription(project):
    return HostingSubscription.objects.create(
        project=project,
        plan='annual',
        base_monthly_amount=Decimal('250000.00'),
        discount_percent=40,
        effective_monthly_amount=Decimal('150000.00'),
        billing_amount=Decimal('1800000.00'),
        status='active',
        start_date='2026-01-01',
        next_billing_date='2027-01-01',
    )


def test_forward_recalculates_only_the_unpaid_future_cycle():
    subscription = make_annual_subscription(make_project())
    paid = Payment.objects.create(
        subscription=subscription,
        amount=Decimal('1800000.00'),
        description='Hosting Anual histórico',
        billing_period_start='2025-01-01',
        billing_period_end='2025-12-31',
        due_date='2025-01-01',
        status='paid',
    )
    pending = Payment.objects.create(
        subscription=subscription,
        amount=Decimal('1800000.00'),
        description='Hosting Anual futuro',
        billing_period_start='2026-01-01',
        billing_period_end='2026-12-31',
        due_date='2026-01-01',
        status='pending',
    )

    migration.migrate_to_nine_month(apps, None)

    subscription.refresh_from_db()
    paid.refresh_from_db()
    pending.refresh_from_db()
    assert subscription.plan == 'nine_month'
    assert subscription.billing_amount == Decimal('1350000.00')
    assert subscription.next_billing_date.isoformat() == '2026-10-01'
    assert pending.amount == Decimal('1350000.00')
    assert pending.billing_period_end.isoformat() == '2026-09-30'
    assert 'Cada 9 meses' in pending.description
    assert paid.amount == Decimal('1800000.00')
    assert paid.billing_period_end.isoformat() == '2025-12-31'
    assert paid.description == 'Hosting Anual histórico'


def test_forward_refuses_a_subscription_with_a_wompi_link():
    subscription = make_annual_subscription(make_project('Bloqueado'))
    Payment.objects.create(
        subscription=subscription,
        amount=Decimal('1800000.00'),
        description='Cobro enlazado',
        billing_period_start='2026-01-01',
        billing_period_end='2026-12-31',
        due_date='2026-01-01',
        status='pending',
        wompi_payment_link_id='link-123',
    )

    with pytest.raises(RuntimeError, match='linked to Wompi'):
        migration.migrate_to_nine_month(apps, None)


def test_forward_updates_current_snapshots_and_hosting_filters():
    project = make_project('Snapshot')
    project.hosting_tiers = [{
        'frequency': 'annual',
        'months': 12,
        'label': 'Anual',
        'effective_monthly': 150000,
        'billing_amount': 1800000,
    }]
    project.save(update_fields=['hosting_tiers'])
    admin = User.objects.create_superuser(
        username='admin@example.com',
        email='admin@example.com',
        password='secret',
    )
    annual_tab = SavedFilterTab.objects.create(
        user=admin,
        view='accounting_hosting',
        name='Anuales',
        filters={'modalities': ['annual']},
        base_filters={'modalities': ['annual']},
        is_seeded=True,
    )
    monthly_tab = SavedFilterTab.objects.create(
        user=admin,
        view='accounting_hosting',
        name='Mensuales',
        filters={'modalities': ['monthly']},
        base_filters={'modalities': ['monthly']},
        is_seeded=True,
    )

    migration.migrate_to_nine_month(apps, None)

    project.refresh_from_db()
    annual_tab.refresh_from_db()
    tier = project.hosting_tiers[0]
    assert (tier['frequency'], tier['months']) == ('nine_month', 9)
    assert tier['billing_amount'] == 1350000
    assert annual_tab.name == 'Cada 9 meses'
    assert annual_tab.filters == {'modalities': ['nine_month']}
    assert not SavedFilterTab.objects.filter(pk=monthly_tab.pk).exists()


def test_forward_preserves_cancelled_annual_subscription_snapshot():
    project = make_project('Cancelado')
    project.hosting_tiers = [{
        'frequency': 'annual',
        'months': 12,
        'label': 'Anual',
        'effective_monthly': 150000,
        'billing_amount': 1800000,
    }]
    project.save(update_fields=['hosting_tiers'])
    subscription = make_annual_subscription(project)
    subscription.status = 'cancelled'
    subscription.save(update_fields=['status'])

    migration.migrate_to_nine_month(apps, None)

    project.refresh_from_db()
    subscription.refresh_from_db()
    assert subscription.plan == 'annual'
    assert project.hosting_tiers[0] == {
        'frequency': 'annual',
        'months': 12,
        'label': 'Anual',
        'effective_monthly': 150000,
        'billing_amount': 1800000,
    }
