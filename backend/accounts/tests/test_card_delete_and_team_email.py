"""Tests for card removal and the team payment-status email.

Covers:
- card_delete_view: clears the stored card (best-effort Wompi delete) / 400 when none.
- record_payment_status_change: triggers a team email on PAID/FAILED only.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from accounts.models import HostingSubscription, Payment, Project, UserProfile
from accounts.services.payment_history import record_payment_status_change

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='client@del.com', email='client@del.com', password='clientpass1',
        first_name='Mimi', last_name='Tos',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@del.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Mimitos', client=client_user, status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def subscription(project):
    sub = HostingSubscription(
        project=project, plan=HostingSubscription.PLAN_QUARTERLY,
        base_monthly_amount=Decimal('300000'), discount_percent=0,
        start_date='2026-01-01', next_billing_date='2026-04-01',
        status=HostingSubscription.STATUS_ACTIVE,
    )
    sub.calculate_amounts()
    sub.save()
    return sub


@pytest.fixture
def subscription_with_card(subscription):
    subscription.wompi_payment_source_id = '12345'
    subscription.card_brand = 'VISA'
    subscription.card_last_four = '4242'
    subscription.card_exp_month = '12'
    subscription.card_exp_year = '30'
    subscription.save()
    return subscription


@pytest.fixture
def payment(subscription):
    return Payment.objects.create(
        subscription=subscription, amount=Decimal('900000'),
        description='Hosting', billing_period_start='2026-04-01',
        billing_period_end='2026-06-30', due_date='2026-04-01',
        status=Payment.STATUS_PENDING,
    )


DELETE_URL = '/api/accounts/projects/{}/subscription/card/remove/'


# ---------------------------------------------------------------------------
# card_delete_view
# ---------------------------------------------------------------------------

class TestCardDelete:
    def test_delete_clears_card_and_calls_wompi(
        self, api_client, client_headers, project, subscription_with_card,
    ):
        with patch('accounts.services.wompi.delete_payment_source', return_value=True) as m:
            resp = api_client.delete(DELETE_URL.format(project.id), **client_headers)

        assert resp.status_code == 200
        m.assert_called_once_with('12345')
        subscription_with_card.refresh_from_db()
        assert subscription_with_card.wompi_payment_source_id == ''
        assert subscription_with_card.card_brand == ''
        assert subscription_with_card.card_last_four == ''
        body = resp.json()
        assert body['subscription']['has_payment_source'] is False

    def test_delete_succeeds_even_if_wompi_fails(
        self, api_client, client_headers, project, subscription_with_card,
    ):
        # delete_payment_source is best-effort and returns False on Wompi error.
        with patch('accounts.services.wompi.delete_payment_source', return_value=False):
            resp = api_client.delete(DELETE_URL.format(project.id), **client_headers)

        assert resp.status_code == 200
        subscription_with_card.refresh_from_db()
        assert subscription_with_card.wompi_payment_source_id == ''

    def test_delete_without_card_returns_400(
        self, api_client, client_headers, project, subscription,
    ):
        resp = api_client.delete(DELETE_URL.format(project.id), **client_headers)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# team payment-status email trigger
# ---------------------------------------------------------------------------

@pytest.fixture
def team_email(settings):
    settings.TEAM_PAYMENTS_EMAIL = 'team-test@proyegarts.co'
    return settings.TEAM_PAYMENTS_EMAIL


class TestTeamPaymentEmailTrigger:
    """record_payment_status_change enqueues the team email on terminal states."""

    def test_paid_transition_enqueues_task(self, payment):
        with patch('accounts.tasks.send_payment_status_team_email_task') as m:
            record_payment_status_change(
                payment, Payment.STATUS_PENDING, Payment.STATUS_PAID, source='webhook',
            )
        m.assert_called_once_with(payment.id, Payment.STATUS_PAID, 'webhook')

    def test_failed_transition_enqueues_task(self, payment):
        with patch('accounts.tasks.send_payment_status_team_email_task') as m:
            record_payment_status_change(
                payment, Payment.STATUS_PENDING, Payment.STATUS_FAILED, source='webhook',
            )
        m.assert_called_once_with(payment.id, Payment.STATUS_FAILED, 'webhook')

    def test_non_terminal_transition_does_not_enqueue(self, payment):
        with patch('accounts.tasks.send_payment_status_team_email_task') as m:
            record_payment_status_change(
                payment, Payment.STATUS_PENDING, Payment.STATUS_PROCESSING, source='webhook',
            )
        m.assert_not_called()

    def test_noop_transition_does_not_enqueue(self, payment):
        with patch('accounts.tasks.send_payment_status_team_email_task') as m:
            result = record_payment_status_change(
                payment, Payment.STATUS_PAID, Payment.STATUS_PAID, source='webhook',
            )
        assert result is None
        m.assert_not_called()


class TestTeamPaymentEmailSend:
    """The send function renders and delivers the team notification."""

    def test_paid_email_goes_to_team_inbox(self, payment, team_email):
        from accounts.services.payment_notifications import send_payment_status_team_email

        mail.outbox = []
        ok = send_payment_status_team_email(payment.id, Payment.STATUS_PAID, 'webhook')
        assert ok is True
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.to == ['team-test@proyegarts.co']
        assert 'Pago aprobado' in msg.subject
        assert 'Mimitos' in msg.subject

    def test_failed_email_subject(self, payment, team_email):
        from accounts.services.payment_notifications import send_payment_status_team_email

        mail.outbox = []
        send_payment_status_team_email(payment.id, Payment.STATUS_FAILED, 'webhook')
        assert len(mail.outbox) == 1
        assert 'Pago fallido' in mail.outbox[0].subject
