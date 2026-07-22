"""Tests for the hosting cuenta de cobro flow (hosting_billing_service)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import re

import pytest
from django.core import mail

from content.models import Document, EmailLog, HostingRecord, IssuerProfile
from content.services import hosting_billing_service
from content.services.hosting_billing_service import (
    HostingBillingError,
    create_hosting_collection_account,
    next_billing_period,
    resend_collection_account_email,
    send_hosting_collection_account,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def issuer(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    # Migration 0052 seeds the default issuer; the flow uses the first by pk.
    profile = IssuerProfile.objects.order_by('pk').first()
    if profile is None:
        profile = IssuerProfile.objects.create(name='ProjectApp')
    profile.legal_name = 'ProjectApp SAS'
    profile.identification_number = '901.234.567-8'
    profile.email = 'team@projectapp.co'
    profile.default_payment_methods = [
        {
            'payment_method_type': 'bank_transfer',
            'bank_name': 'Bancolombia',
            'account_number': '123-456789-01',
            'account_holder_name': 'ProjectApp SAS',
        },
        {'payment_method_type': 'nequi', 'account_number': '3001234567'},
    ]
    profile.save()
    return profile


def make_hosting(**overrides):
    defaults = {
        'client_name': 'German - Kore',
        'client_email': 'german@korehealths.com',
        'client_contact_name': 'German',
        'client_identification': '80.123.456',
        'domain_url': 'https://korehealths.com/',
        'monthly_value': Decimal('91667.00'),
        'payment_modality': 'semiannual',
        'payment_per_cycle': Decimal('550002.00'),
        'valid_from': date(2026, 1, 2),
        'valid_to': date(2026, 7, 2),
        'is_active': True,
    }
    defaults.update(overrides)
    return HostingRecord.objects.create(**defaults)


class TestCreateDraft:
    def test_period_advances_one_modality(self):
        hosting = make_hosting()
        period_from, period_to = next_billing_period(hosting)
        assert period_from == date(2026, 7, 2)
        assert period_to == date(2027, 1, 2)

    def test_draft_shape(self):
        hosting = make_hosting()
        document = create_hosting_collection_account(hosting)
        assert document.commercial_status == Document.CommercialStatus.DRAFT
        assert document.hosting_record_id == hosting.pk
        item = document.items.get()
        assert item.unit_price == Decimal('550002.00')
        assert item.period_start == date(2026, 7, 2)
        assert item.period_end == date(2027, 1, 2)
        assert 'korehealths.com' in item.description
        methods = list(document.payment_methods.all())
        assert len(methods) == 2
        assert methods[0].is_primary and methods[0].bank_name == 'Bancolombia'


class TestSendFlow:
    def test_issues_with_hosting_customer_and_emails_pdf(self):
        hosting = make_hosting()
        result = send_hosting_collection_account(hosting)
        document = Document.objects.get(pk=result['document'].pk)
        assert result['email_sent'] is True
        assert document.commercial_status == Document.CommercialStatus.ISSUED
        assert re.fullmatch(r'[A-Z]+-\d{4}-\d{4}', document.public_number)
        ext = document.collection_account
        assert ext.customer_name == 'German - Kore'
        assert ext.customer_email == 'german@korehealths.com'
        assert document.total == Decimal('550002.00')

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert sent.to == ['german@korehealths.com']
        assert document.public_number in sent.subject
        assert sent.attachments[0][0] == f'{document.public_number}.pdf'
        assert sent.attachments[0][2] == 'application/pdf'

        hosting.refresh_from_db()
        assert hosting.billing_requested_at is not None
        assert hosting.expiry_notice_target == hosting.valid_to
        assert EmailLog.objects.filter(
            template_key='collection_account_sent',
            status=EmailLog.Status.SENT,
        ).exists()

    def test_requires_client_email(self):
        hosting = make_hosting(client_email='')
        with pytest.raises(HostingBillingError) as excinfo:
            send_hosting_collection_account(hosting)
        assert 'email' in str(excinfo.value)
        assert Document.objects.count() == 0

    def test_requires_payment_per_cycle(self):
        hosting = make_hosting(payment_per_cycle=Decimal('0'))
        with pytest.raises(HostingBillingError) as excinfo:
            send_hosting_collection_account(hosting)
        assert 'pago por ciclo' in str(excinfo.value)
        assert Document.objects.count() == 0

    def test_duplicate_period_guard(self):
        hosting = make_hosting()
        send_hosting_collection_account(hosting)
        hosting.refresh_from_db()
        with pytest.raises(HostingBillingError) as excinfo:
            send_hosting_collection_account(hosting)
        assert 'Reenviar' in str(excinfo.value)
        assert Document.objects.count() == 1

    def test_email_failure_keeps_document_issued(self):
        hosting = make_hosting()
        with patch.object(
            hosting_billing_service.EmailMultiAlternatives,
            'send',
            side_effect=OSError('smtp down'),
        ):
            result = send_hosting_collection_account(hosting)
        assert result['email_sent'] is False
        document = result['document']
        document.refresh_from_db()
        assert document.commercial_status == Document.CommercialStatus.ISSUED
        hosting.refresh_from_db()
        assert hosting.billing_requested_at is not None
        assert EmailLog.objects.filter(
            template_key='collection_account_sent',
            status=EmailLog.Status.FAILED,
        ).exists()


class TestResend:
    def test_resend_sends_again(self):
        hosting = make_hosting()
        result = send_hosting_collection_account(hosting)
        document = Document.objects.get(pk=result['document'].pk)
        mail.outbox.clear()
        assert resend_collection_account_email(document) is True
        assert len(mail.outbox) == 1

    def test_resend_rejects_drafts_without_customer(self):
        hosting = make_hosting()
        document = create_hosting_collection_account(hosting)
        # Draft: the customer snapshot only happens at issue time.
        with pytest.raises(HostingBillingError) as excinfo:
            resend_collection_account_email(document)
        assert 'email de cliente' in str(excinfo.value)
        assert len(mail.outbox) == 0
