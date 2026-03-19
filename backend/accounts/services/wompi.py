"""
Wompi payment gateway integration service.

Uses Wompi's Payment Links API to generate payment URLs.
Docs: https://docs.wompi.co/docs/colombia/enlaces-de-pago/

Environment variables:
    WOMPI_PRIVATE_KEY — Bearer token for API auth
    WOMPI_INTEGRITY_SECRET — SHA256 integrity signature secret
    WOMPI_API_URL — Base URL (sandbox or production)
"""

import hashlib
import hmac
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_headers():
    return {
        'Authorization': f'Bearer {settings.WOMPI_PRIVATE_KEY}',
        'Content-Type': 'application/json',
    }


def create_payment_link(payment):
    """
    Create a Wompi payment link for a Payment instance.
    Returns (link_id, link_url) on success, raises on failure.
    """
    from accounts.models import Payment

    amount_in_cents = int(payment.amount * 100)

    redirect_url = _get_redirect_url(payment)
    payload = {
        'name': payment.description or f'Hosting — {payment.subscription.project.name}',
        'description': (
            f'Pago hosting {payment.billing_period_start.strftime("%d/%m/%Y")} '
            f'— {payment.billing_period_end.strftime("%d/%m/%Y")}'
        ),
        'single_use': True,
        'collect_shipping': False,
        'currency': 'COP',
        'amount_in_cents': amount_in_cents,
    }
    if redirect_url:
        payload['redirect_url'] = redirect_url

    integrity_str = f'{payment.id}{amount_in_cents}COP{settings.WOMPI_INTEGRITY_SECRET}'
    payload['integrity_signature'] = hashlib.sha256(integrity_str.encode()).hexdigest()

    url = f'{settings.WOMPI_API_URL}/payment_links'

    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json().get('data', {})

        link_id = data.get('id', '')
        link_url = f'https://checkout.wompi.co/l/{link_id}' if link_id else ''

        payment.wompi_payment_link_id = link_id
        payment.wompi_payment_link_url = link_url
        payment.status = Payment.STATUS_PROCESSING
        payment.save(update_fields=[
            'wompi_payment_link_id', 'wompi_payment_link_url', 'status',
        ])

        logger.info('Wompi payment link created: %s for payment %s', link_id, payment.id)
        return link_id, link_url

    except requests.RequestException as e:
        logger.error('Wompi API error creating payment link: %s', e)
        raise


def verify_transaction(transaction_id):
    """
    Verify a transaction status with Wompi.
    Returns the transaction data dict.
    """
    url = f'{settings.WOMPI_API_URL}/transactions/{transaction_id}'

    try:
        resp = requests.get(url, headers=_get_headers(), timeout=15)
        resp.raise_for_status()
        return resp.json().get('data', {})
    except requests.RequestException as e:
        logger.error('Wompi API error verifying transaction %s: %s', transaction_id, e)
        raise


def validate_webhook_signature(body_bytes, signature, timestamp):
    """
    Validate a Wompi webhook event signature.
    Signature = SHA256(timestamp + '.' + body)
    """
    message = f'{timestamp}.{body_bytes.decode("utf-8")}'
    expected = hmac.new(
        settings.WOMPI_EVENTS_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_acceptance_token():
    """Fetch the merchant acceptance token required for transactions."""
    url = f'{settings.WOMPI_API_URL}/merchants/{settings.WOMPI_PUBLIC_KEY}'
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get('data', {})
        presigned = data.get('presigned_acceptance', {})
        return presigned.get('acceptance_token', '')
    except requests.RequestException as e:
        logger.error('Wompi API error fetching acceptance token: %s', e)
        raise


def tokenize_card(number, exp_month, exp_year, cvc, card_holder):
    """
    Tokenize a credit/debit card via Wompi public API.
    Returns the token ID string.
    """
    url = f'{settings.WOMPI_API_URL}/tokens/cards'
    headers = {
        'Authorization': f'Bearer {settings.WOMPI_PUBLIC_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'number': number.replace(' ', '').replace('-', ''),
        'exp_month': str(exp_month).zfill(2),
        'exp_year': str(exp_year).zfill(2),
        'cvc': str(cvc),
        'card_holder': card_holder,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json().get('data', {})
        token_id = data.get('id', '')
        if not token_id:
            raise ValueError('No token ID in Wompi response')
        logger.info('Card tokenized: %s (last4: %s)', token_id[:20], data.get('last_four', ''))
        return token_id
    except requests.RequestException as e:
        logger.error('Wompi card tokenization error: %s', e)
        raise


def create_card_transaction(payment, card_token, acceptance_token, reference, signature):
    """
    Create a Wompi transaction for a card payment.
    Always uses installments=1 (subscription payment, no multi-cuota).
    """
    amount_in_cents = int(payment.amount * 100)

    payload = {
        'amount_in_cents': amount_in_cents,
        'currency': 'COP',
        'customer_email': payment.subscription.project.client.email,
        'payment_method': {
            'type': 'CARD',
            'token': card_token,
            'installments': 1,
        },
        'payment_method_type': 'CARD',
        'reference': reference,
        'signature': signature,
        'acceptance_token': acceptance_token,
    }

    url = f'{settings.WOMPI_API_URL}/transactions'

    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json().get('data', {})
        txn_id = data.get('id', '')
        txn_status = data.get('status', '')
        logger.info('Card transaction created: %s status=%s', txn_id, txn_status)
        return data
    except requests.RequestException as e:
        logger.error('Wompi create card transaction error: %s', e)
        raise


def _get_redirect_url(payment):
    """Build the redirect URL after payment completion.
    Returns empty string in dev (http) — Wompi WAF blocks non-https redirect URLs.
    """
    base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
    if not base.startswith('https'):
        return ''
    project_id = payment.subscription.project_id
    return f'{base}/platform/projects/{project_id}/payments?payment={payment.id}'
