"""Tests for the Wompi payment gateway service.

Covers: create_payment_link, verify_transaction, validate_webhook_signature,
get_acceptance_token, tokenize_card, create_card_transaction.
"""
import datetime
import hashlib
import hmac
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from accounts.models import HostingSubscription, Payment, Project, UserProfile
from accounts.services.wompi import (
    create_card_transaction,
    create_payment_link,
    get_acceptance_token,
    tokenize_card,
    validate_webhook_signature,
    verify_transaction,
)

User = get_user_model()

WOMPI_SETTINGS = {
    'WOMPI_PRIVATE_KEY': 'test-private-key',
    'WOMPI_PUBLIC_KEY': 'test-public-key',
    'WOMPI_INTEGRITY_SECRET': 'test-integrity',
    'WOMPI_EVENTS_SECRET': 'test-events-secret',
    'WOMPI_API_URL': 'https://sandbox.wompi.co/v1',
    'FRONTEND_BASE_URL': 'https://example.com',
}

pytestmark = pytest.mark.django_db


@pytest.fixture
def payment(db):
    user = User.objects.create_user(
        username='wompi-client@test.com',
        email='wompi-client@test.com',
        password='pass12345',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
    project = Project.objects.create(name='Wompi Test Project', client=user)
    sub = HostingSubscription.objects.create(
        project=project,
        plan=HostingSubscription.PLAN_MONTHLY,
        base_monthly_amount=Decimal('500000'),
        effective_monthly_amount=Decimal('500000'),
        billing_amount=Decimal('500000'),
        start_date=datetime.date.today(),
    )
    return Payment.objects.create(
        subscription=sub,
        amount=Decimal('500000'),
        billing_period_start=datetime.date.today(),
        billing_period_end=datetime.date.today() + datetime.timedelta(days=30),
        due_date=datetime.date.today(),
        description='Hosting mensual',
    )


class TestCreatePaymentLink:
    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_returns_link_id_and_url_on_success(self, mock_post, payment):
        """Successful API call returns (link_id, link_url) tuple."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-abc123'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        link_id, link_url = create_payment_link(payment)

        assert link_id == 'link-abc123'
        assert 'link-abc123' in link_url

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_updates_payment_status_to_processing(self, mock_post, payment):
        """Payment status is set to STATUS_PROCESSING after link creation."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-status'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        create_payment_link(payment)

        payment.refresh_from_db()
        assert payment.status == Payment.STATUS_PROCESSING

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_stores_link_id_on_payment(self, mock_post, payment):
        """wompi_payment_link_id is saved to the payment after creation."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-stored'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        create_payment_link(payment)

        payment.refresh_from_db()
        assert payment.wompi_payment_link_id == 'link-stored'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_raises_on_request_exception(self, mock_post, payment):
        """RequestException from the API is propagated to the caller."""
        import requests as req_lib
        mock_post.side_effect = req_lib.RequestException('timeout')

        with pytest.raises(req_lib.RequestException):
            create_payment_link(payment)

    @override_settings(**{**WOMPI_SETTINGS, 'FRONTEND_BASE_URL': 'http://localhost:3000'})
    @patch('requests.post')
    def test_omits_redirect_url_for_non_https_frontend(self, mock_post, payment):
        """redirect_url is absent from payload when FRONTEND_BASE_URL is http."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-dev'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        create_payment_link(payment)

        payload = mock_post.call_args[1]['json']
        assert 'redirect_url' not in payload

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_includes_redirect_url_for_https_frontend(self, mock_post, payment):
        """redirect_url is included in payload when FRONTEND_BASE_URL is https."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-prod'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        create_payment_link(payment)

        payload = mock_post.call_args[1]['json']
        assert 'redirect_url' in payload

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_payload_contains_integrity_signature(self, mock_post, payment):
        """integrity_signature field is present in the API request payload."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'link-sig'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        create_payment_link(payment)

        payload = mock_post.call_args[1]['json']
        assert 'integrity_signature' in payload


class TestVerifyTransaction:
    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.get')
    def test_returns_transaction_data_dict(self, mock_get):
        """Successful call returns the data dict from the API response."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'txn-001', 'status': 'APPROVED'}}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        data = verify_transaction('txn-001')

        assert data['status'] == 'APPROVED'
        assert data['id'] == 'txn-001'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.get')
    def test_raises_on_request_exception(self, mock_get):
        """RequestException is propagated when the verification call fails."""
        import requests as req_lib
        mock_get.side_effect = req_lib.RequestException('network error')

        with pytest.raises(req_lib.RequestException):
            verify_transaction('txn-bad')


class TestValidateWebhookSignature:
    @override_settings(**WOMPI_SETTINGS)
    def test_returns_true_for_valid_signature(self):
        """Correctly computed HMAC-SHA256 signature is accepted."""
        timestamp = '1700000000'
        body = b'{"event": "transaction.updated"}'
        message = f'{timestamp}.{body.decode("utf-8")}'
        expected = hmac.new(
            b'test-events-secret',
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        result = validate_webhook_signature(body, expected, timestamp)

        assert result is True

    @override_settings(**WOMPI_SETTINGS)
    def test_returns_false_for_invalid_signature(self):
        """Tampered or wrong signature is rejected."""
        body = b'{"event": "transaction.updated"}'

        result = validate_webhook_signature(body, 'invalid-signature', '1700000000')

        assert result is False


class TestGetAcceptanceToken:
    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.get')
    def test_returns_acceptance_token_string(self, mock_get):
        """Acceptance token string is extracted from presigned_acceptance data."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'data': {'presigned_acceptance': {'acceptance_token': 'acc-tok-xyz'}}
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        token = get_acceptance_token()

        assert token == 'acc-tok-xyz'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.get')
    def test_raises_on_request_exception(self, mock_get):
        """RequestException from the merchant endpoint is propagated."""
        import requests as req_lib
        mock_get.side_effect = req_lib.RequestException('unavailable')

        with pytest.raises(req_lib.RequestException):
            get_acceptance_token()


class TestTokenizeCard:
    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_returns_token_id_on_success(self, mock_post):
        """Token ID string is returned after successful card tokenization."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'tok-card-abc', 'last_four': '1234'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        token = tokenize_card('4111111111111111', '12', '28', '123', 'John Doe')

        assert token == 'tok-card-abc'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_raises_value_error_when_response_has_no_token_id(self, mock_post):
        """ValueError is raised when the API returns an empty id field."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        with pytest.raises(ValueError, match='No token ID'):
            tokenize_card('4111111111111111', '12', '28', '123', 'John Doe')

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_strips_spaces_and_hyphens_from_card_number(self, mock_post):
        """Spaces and hyphens are removed from the card number before sending."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'data': {'id': 'tok-clean'}}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        tokenize_card('4111-1111-1111-1111', '12', '28', '123', 'Jane')

        payload = mock_post.call_args[1]['json']
        assert payload['number'] == '4111111111111111'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_raises_on_request_exception(self, mock_post):
        """RequestException during tokenization is propagated to the caller."""
        import requests as req_lib
        mock_post.side_effect = req_lib.RequestException('gateway error')

        with pytest.raises(req_lib.RequestException):
            tokenize_card('4111111111111111', '12', '28', '123', 'Jane')


class TestCreateCardTransaction:
    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_returns_transaction_data_on_success(self, mock_post, payment):
        """Successful call returns the transaction data dict."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'data': {'id': 'txn-card-001', 'status': 'PENDING'}
        }
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        data = create_card_transaction(payment, 'tok-abc', 'acc-tok', 'ref-001', 'sig-abc')

        assert data['id'] == 'txn-card-001'
        assert data['status'] == 'PENDING'

    @override_settings(**WOMPI_SETTINGS)
    @patch('requests.post')
    def test_raises_on_request_exception(self, mock_post, payment):
        """RequestException from the transaction endpoint is propagated."""
        import requests as req_lib
        mock_post.side_effect = req_lib.RequestException('gateway timeout')

        with pytest.raises(req_lib.RequestException):
            create_card_transaction(payment, 'tok', 'acc', 'ref', 'sig')
