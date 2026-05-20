"""Tests for the stored-card subscription flow (Wompi payment sources + 3DS).

Covers:
- wompi service: get_acceptance_tokens, create_payment_source, charge_with_payment_source
- card_setup_start_view / card_setup_status_view / card_setup_confirm_view
- payment_charge_stored_view
- auto_charge_due_subscriptions Huey task (charge, retry, suspension)
"""
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.models import HostingSubscription, Payment, Project, UserProfile
from accounts.tasks import auto_charge_due_subscriptions

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='client@card.com', email='client@card.com', password='clientpass1',
        first_name='Carlos', last_name='Ruiz',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT, is_onboarded=True)
    return user


@pytest.fixture
def client_headers(api_client, client_user):
    resp = api_client.post('/api/accounts/login/', {
        'email': 'client@card.com', 'password': 'clientpass1',
    })
    token = resp.json()['tokens']['access']
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Card Project', client=client_user, status=Project.STATUS_ACTIVE,
    )


@pytest.fixture
def subscription(project):
    sub = HostingSubscription(
        project=project, plan=HostingSubscription.PLAN_MONTHLY,
        base_monthly_amount=Decimal('300000'), discount_percent=0,
        start_date='2026-01-01', next_billing_date='2026-02-01',
        status=HostingSubscription.STATUS_ACTIVE,
    )
    sub.calculate_amounts()
    sub.save()
    return sub


@pytest.fixture
def pending_payment(subscription):
    return Payment.objects.create(
        subscription=subscription, amount=subscription.billing_amount,
        description='Hosting', billing_period_start='2026-02-01',
        billing_period_end='2026-02-28', due_date='2020-02-01',
        status=Payment.STATUS_PENDING,
    )


VALID_CARD = {
    'card_number': '4242424242424242', 'exp_month': '12', 'exp_year': '30',
    'cvc': '123', 'card_holder': 'Carlos Ruiz',
}


# ===========================================================================
# wompi service
# ===========================================================================

class TestWompiService:
    @override_settings(WOMPI_API_URL='https://sb.wompi.co/v1', WOMPI_PUBLIC_KEY='pub')
    @patch('accounts.services.wompi.requests.get')
    def test_get_acceptance_tokens_returns_both(self, mock_get):
        mock_get.return_value = MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={'data': {
                'presigned_acceptance': {'acceptance_token': 'ACC'},
                'presigned_personal_data_auth': {'acceptance_token': 'PERS'},
            }}),
        )
        from accounts.services.wompi import get_acceptance_tokens
        tokens = get_acceptance_tokens()
        assert tokens == {'acceptance_token': 'ACC', 'accept_personal_auth': 'PERS'}

    @override_settings(WOMPI_API_URL='https://sb.wompi.co/v1', WOMPI_PRIVATE_KEY='priv')
    @patch('accounts.services.wompi.requests.post')
    def test_create_payment_source_sends_card_token(self, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={'data': {'id': 3891, 'status': 'AVAILABLE'}}),
        )
        from accounts.services.wompi import create_payment_source
        data = create_payment_source('tok_x', 'a@b.com', 'acc', 'auth')
        assert data['id'] == 3891
        payload = mock_post.call_args.kwargs['json']
        assert payload['type'] == 'CARD'
        assert payload['token'] == 'tok_x'
        assert payload['accept_personal_auth'] == 'auth'

    @override_settings(WOMPI_API_URL='https://sb.wompi.co/v1', WOMPI_PRIVATE_KEY='priv')
    @patch('accounts.services.wompi.requests.post')
    def test_charge_with_payment_source_is_recurrent(self, mock_post):
        mock_post.return_value = MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={'data': {'id': 'txn1', 'status': 'APPROVED'}}),
        )
        from accounts.services.wompi import charge_with_payment_source
        payment = MagicMock(id=1, amount=Decimal('100000'))
        payment.subscription.project.client.email = 'a@b.com'
        charge_with_payment_source(payment, '3891', 'REF1', 'sig')
        payload = mock_post.call_args.kwargs['json']
        assert payload['recurrent'] is True
        assert payload['payment_source_id'] == 3891
        assert payload['amount_in_cents'] == 10000000


# ===========================================================================
# card_setup_start_view
# ===========================================================================

class TestCardSetupStart:
    def _url(self, project):
        return f'/api/accounts/projects/{project.id}/subscription/card/'

    def test_missing_card_fields_returns_400(self, api_client, client_headers, project, subscription):
        resp = api_client.post(self._url(project), {'card_number': '4242'}, **client_headers)
        assert resp.status_code == 400

    def test_no_subscription_returns_400(self, api_client, client_headers, project):
        resp = api_client.post(self._url(project), VALID_CARD, **client_headers)
        assert resp.status_code == 400

    def test_creates_payment_source_non_3ds(self, api_client, client_headers, project, subscription):
        with patch('accounts.services.wompi.tokenize_card',
                   return_value={'id': 'tok_x', 'brand': 'VISA', 'last_four': '4242'}), \
             patch('accounts.services.wompi.get_acceptance_tokens',
                   return_value={'acceptance_token': 'a', 'accept_personal_auth': 'b'}), \
             patch('accounts.services.wompi.create_payment_source',
                   return_value={'id': 3891, 'status': 'AVAILABLE', 'extra': {}}):
            resp = api_client.post(self._url(project), VALID_CARD, **client_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body['payment_source_id'] == 3891
        assert body['status'] == 'AVAILABLE'
        assert body['is_three_ds'] is False
        assert body['card_last_four'] == '4242'


# ===========================================================================
# card_setup_status_view
# ===========================================================================

class TestCardSetupStatus:
    def test_returns_three_ds_state(self, api_client, client_headers, project, subscription):
        url = f'/api/accounts/projects/{project.id}/subscription/card/3891/status/'
        with patch('accounts.services.wompi.get_payment_source',
                   return_value={'id': 3891, 'status': 'PENDING',
                                 'customer_email': 'client@card.com',
                                 'extra': {'is_three_ds': True,
                                           'three_ds_auth': {'current_step': 'CHALLENGE'}}}):
            resp = api_client.get(url, **client_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body['is_three_ds'] is True
        assert body['three_ds_auth']['current_step'] == 'CHALLENGE'


# ===========================================================================
# card_setup_confirm_view
# ===========================================================================

class TestCardSetupConfirm:
    def _url(self, project, ps_id=3891):
        return f'/api/accounts/projects/{project.id}/subscription/card/{ps_id}/confirm/'

    def test_rejects_when_source_not_available(self, api_client, client_headers, project, subscription):
        with patch('accounts.services.wompi.get_payment_source',
                   return_value={'id': 3891, 'status': 'DECLINED',
                                 'customer_email': 'client@card.com'}):
            resp = api_client.post(self._url(project), {}, **client_headers)
        assert resp.status_code == 400

    def test_rejects_foreign_payment_source(self, api_client, client_headers, project, subscription):
        """A payment source created for a different customer_email is rejected."""
        with patch('accounts.services.wompi.get_payment_source',
                   return_value={'id': 3891, 'status': 'AVAILABLE',
                                 'customer_email': 'attacker@evil.com', 'public_data': {}}):
            resp = api_client.post(self._url(project), {}, **client_headers)
        assert resp.status_code == 400
        subscription.refresh_from_db()
        assert subscription.wompi_payment_source_id == ''

    def test_persists_card_and_charges_first_payment(
        self, api_client, client_headers, project, subscription, pending_payment,
    ):
        with patch('accounts.services.wompi.get_payment_source',
                   return_value={'id': 3891, 'status': 'AVAILABLE',
                                 'customer_email': 'client@card.com',
                                 'public_data': {'last_four': '4242', 'exp_month': '12', 'exp_year': '30'}}), \
             patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txn1', 'status': 'APPROVED'}):
            resp = api_client.post(self._url(project), {'card_brand': 'VISA'}, **client_headers)
        assert resp.status_code == 200
        subscription.refresh_from_db()
        pending_payment.refresh_from_db()
        assert subscription.wompi_payment_source_id == '3891'
        assert subscription.card_last_four == '4242'
        assert pending_payment.status == Payment.STATUS_PAID

    def test_confirms_card_without_open_payment(
        self, api_client, client_headers, project, subscription,
    ):
        with patch('accounts.services.wompi.get_payment_source',
                   return_value={'id': 3891, 'status': 'AVAILABLE',
                                 'customer_email': 'client@card.com', 'public_data': {}}):
            resp = api_client.post(self._url(project), {'card_last_four': '1111'}, **client_headers)
        assert resp.status_code == 200
        subscription.refresh_from_db()
        assert subscription.wompi_payment_source_id == '3891'
        assert resp.json()['charge'] is None


# ===========================================================================
# payment_charge_stored_view
# ===========================================================================

class TestPaymentChargeStored:
    def _url(self, project, payment):
        return f'/api/accounts/projects/{project.id}/payments/{payment.id}/charge/'

    def test_rejects_when_no_stored_card(
        self, api_client, client_headers, project, subscription, pending_payment,
    ):
        resp = api_client.post(self._url(project, pending_payment), {}, **client_headers)
        assert resp.status_code == 400

    def test_charges_with_stored_card(
        self, api_client, client_headers, project, subscription, pending_payment,
    ):
        subscription.wompi_payment_source_id = '3891'
        subscription.save(update_fields=['wompi_payment_source_id'])
        with patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txn9', 'status': 'APPROVED'}):
            resp = api_client.post(self._url(project, pending_payment), {}, **client_headers)
        assert resp.status_code == 200
        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID

    def test_pending_charge_resolves_via_polling(
        self, api_client, client_headers, project, subscription, pending_payment,
    ):
        """A PENDING card charge resolves to PAID once polling sees APPROVED."""
        subscription.wompi_payment_source_id = '3891'
        subscription.save(update_fields=['wompi_payment_source_id'])
        with patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txnP', 'status': 'PENDING'}), \
             patch('accounts.services.wompi.verify_transaction',
                   return_value={'id': 'txnP', 'status': 'APPROVED'}), \
             patch('time.sleep'):
            resp = api_client.post(self._url(project, pending_payment), {}, **client_headers)
        assert resp.status_code == 200
        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID


# ===========================================================================
# auto_charge_due_subscriptions Huey task
# ===========================================================================

class TestAutoChargeTask:
    def test_charges_due_payment_with_stored_card(self, subscription, pending_payment):
        subscription.wompi_payment_source_id = '3891'
        subscription.save(update_fields=['wompi_payment_source_id'])
        with patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txn1', 'status': 'APPROVED'}):
            result = auto_charge_due_subscriptions.call_local()
        assert result['charged'] == 1
        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID

    def test_skips_subscription_without_stored_card(self, subscription, pending_payment):
        with patch('accounts.services.wompi.charge_with_payment_source') as mock_charge:
            result = auto_charge_due_subscriptions.call_local()
        mock_charge.assert_not_called()
        assert result['charged'] == 0

    def test_suspends_subscription_after_attempt_limit(self, subscription, pending_payment):
        subscription.wompi_payment_source_id = '3891'
        subscription.save(update_fields=['wompi_payment_source_id'])
        pending_payment.charge_attempts = 2
        pending_payment.save(update_fields=['charge_attempts'])
        with patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txn1', 'status': 'DECLINED', 'status_message': 'Fondos insuficientes'}):
            result = auto_charge_due_subscriptions.call_local()
        assert result['failed'] == 1
        subscription.refresh_from_db()
        pending_payment.refresh_from_db()
        assert subscription.status == HostingSubscription.STATUS_SUSPENDED
        assert pending_payment.status == Payment.STATUS_FAILED
        assert pending_payment.charge_attempts == 3

    def test_reschedules_retry_before_limit(self, subscription, pending_payment):
        subscription.wompi_payment_source_id = '3891'
        subscription.save(update_fields=['wompi_payment_source_id'])
        with patch('accounts.services.wompi.charge_with_payment_source',
                   return_value={'id': 'txn1', 'status': 'DECLINED'}):
            auto_charge_due_subscriptions.call_local()
        subscription.refresh_from_db()
        pending_payment.refresh_from_db()
        assert subscription.status == HostingSubscription.STATUS_ACTIVE
        assert pending_payment.charge_attempts == 1
        assert pending_payment.next_retry_at == date.today() + timedelta(days=2)


# ===========================================================================
# Re-verifying PROCESSING payments (async settlement / missed webhook)
# ===========================================================================

class TestPaymentReverify:
    def test_verify_uses_stored_transaction_id(
        self, api_client, client_headers, project, subscription, pending_payment,
    ):
        """A PROCESSING payment can be re-verified without re-supplying the txn id."""
        pending_payment.status = Payment.STATUS_PROCESSING
        pending_payment.wompi_transaction_id = 'txnStored'
        pending_payment.save(update_fields=['status', 'wompi_transaction_id'])

        url = f'/api/accounts/projects/{project.id}/payments/{pending_payment.id}/verify/'
        with patch('accounts.services.wompi.verify_transaction',
                   return_value={'id': 'txnStored', 'status': 'APPROVED'}):
            resp = api_client.post(url, {}, **client_headers)

        assert resp.status_code == 200
        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID

    def test_cron_reverifies_stuck_processing_payment(self, subscription, pending_payment):
        """The billing cron resolves a PROCESSING payment via direct verification."""
        from accounts.tasks import _reverify_processing_payments

        pending_payment.status = Payment.STATUS_PROCESSING
        pending_payment.wompi_transaction_id = 'txnStuck'
        pending_payment.save(update_fields=['status', 'wompi_transaction_id'])

        with patch('accounts.services.wompi.verify_transaction',
                   return_value={'id': 'txnStuck', 'status': 'APPROVED'}):
            resolved = _reverify_processing_payments()

        assert resolved == 1
        pending_payment.refresh_from_db()
        assert pending_payment.status == Payment.STATUS_PAID
