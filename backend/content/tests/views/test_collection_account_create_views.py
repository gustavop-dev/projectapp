"""Panel create/preview/next-number endpoints for cuentas de cobro."""
import base64
from decimal import Decimal
from unittest.mock import patch

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

from content.models import (
    ClientDocumentNumberSequence,
    Document,
    EmailLog,
    IncomeRecord,
    IssuerProfile,
)
from content.services import collection_account_email_service
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def issuer(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    profile = IssuerProfile.objects.order_by('pk').first()
    profile.city = 'Bogotá'
    profile.default_payment_methods = [
        {'payment_method_type': 'bank_transfer', 'bank_name': 'Bancolombia'},
    ]
    profile.save()
    return profile


def make_client(email='ana@acme.co', company='Acme Soluciones', **profile_kwargs):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
        first_name='Ana', last_name='Pérez',
    )
    UserProfile.objects.create(user=user, company_name=company, **profile_kwargs)
    return user


def make_income(**overrides):
    fields = {
        'concept': 'Desarrollo módulo de reportes',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-08-01',
        'total_amount': Decimal('1490000.00'),
        'gustavo_amount': Decimal('745000.00'),
        'carlos_amount': Decimal('745000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def payload(client_user, income, **overrides):
    data = {
        'client_profile_id': client_user.profile.pk,
        'income_record_id': income.pk,
        'items': [{
            'description': 'Desarrollo módulo de reportes',
            'quantity': '1',
            'unit_price': '1490000.00',
        }],
    }
    data.update(overrides)
    return data


class TestCreateEndpoint:
    def test_create_issues_and_emails(self, super_client, mailoutbox):
        client = make_client(nit='901234567')
        income = make_income()

        response = super_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(client, income),
            format='json',
        )

        assert response.status_code == 201, response.data
        assert response.data['email_sent'] is True
        doc = response.data['document']
        assert doc['public_number'] == 'PA-ACMESOLU-001'
        assert doc['origin'] == 'income'
        assert doc['income_record_id'] == income.pk
        assert len(mailoutbox) == 1
        assert 'PA-ACMESOLU-001' in mailoutbox[0].subject
        assert mailoutbox[0].attachments[0][0] == 'PA-ACMESOLU-001.pdf'

    def test_email_failure_keeps_document_issued(self, super_client):
        client = make_client()
        income = make_income()

        with patch.object(
            collection_account_email_service.EmailMultiAlternatives,
            'send',
            side_effect=OSError('smtp down'),
        ):
            response = super_client.post(
                '/api/accounting/collection-accounts/create/',
                payload(client, income),
                format='json',
            )

        assert response.status_code == 201
        assert response.data['email_sent'] is False
        assert response.data['document']['commercial_status'] == 'issued'
        assert EmailLog.objects.filter(status=EmailLog.Status.FAILED).exists()

    def test_duplicate_income_rejected(self, super_client):
        client = make_client()
        income = make_income()
        super_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(client, income),
            format='json',
        )

        response = super_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(client, income),
            format='json',
        )

        assert response.status_code == 400
        assert 'ya tiene una cuenta de cobro' in response.data['error']

    def test_items_required(self, super_client):
        response = super_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(make_client(), make_income(), items=[]),
            format='json',
        )
        assert response.status_code == 400

    def test_requires_superuser(self, admin_client):
        response = admin_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(make_client(), make_income()),
            format='json',
        )
        assert response.status_code == 403


class TestNextNumberEndpoint:
    def test_suggests_without_consuming(self, super_client):
        client = make_client()

        first = super_client.get(
            f'/api/accounting/collection-accounts/next-number/?client_profile_id={client.profile.pk}',
        )
        second = super_client.get(
            f'/api/accounting/collection-accounts/next-number/?client_profile_id={client.profile.pk}',
        )

        assert first.status_code == 200
        assert first.data['suggested_number'] == 'PA-ACMESOLU-001'
        assert first.data['billing_code'] == 'ACMESOLU'
        assert first.data['issuer_city'] == 'Bogotá'
        assert second.data['suggested_number'] == 'PA-ACMESOLU-001'

    def test_missing_param_is_400(self, super_client):
        response = super_client.get(
            '/api/accounting/collection-accounts/next-number/',
        )
        assert response.status_code == 400


class TestPreviewEndpoint:
    def test_preview_renders_without_persisting(self, super_client, mailoutbox):
        client = make_client(nit='901234567')
        income = make_income()
        docs_before = Document.objects.count()

        response = super_client.post(
            '/api/accounting/collection-accounts/preview/',
            payload(client, income),
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['public_number'] == 'PA-ACMESOLU-001'
        assert 'PA-ACMESOLU-001' in response.data['subject']
        assert 'Valor a pagar' in response.data['html_body']
        pdf = base64.b64decode(response.data['pdf_base64'])
        assert pdf[:4] == b'%PDF'
        # Nothing persisted: no document, no email, no consecutivo consumed.
        assert Document.objects.count() == docs_before
        assert not EmailLog.objects.exists()
        assert len(mailoutbox) == 0
        seq = ClientDocumentNumberSequence.objects.filter(
            client_profile=client.profile,
        ).first()
        assert seq is None or seq.last_value == 0

    def test_preview_surfaces_manual_number_collision(self, super_client):
        Document.objects.create(
            document_type=get_collection_account_document_type(),
            title='Legacy',
            public_number='PA-2026-0001',
            total=Decimal('1'),
        )
        response = super_client.post(
            '/api/accounting/collection-accounts/preview/',
            payload(
                make_client(), make_income(), public_number='PA-2026-0001',
            ),
            format='json',
        )
        assert response.status_code == 400
        assert 'ya está en uso' in response.data['error']

    def test_preview_number_matches_created_number(self, super_client):
        client = make_client()
        income = make_income()

        preview = super_client.post(
            '/api/accounting/collection-accounts/preview/',
            payload(client, income),
            format='json',
        )
        created = super_client.post(
            '/api/accounting/collection-accounts/create/',
            payload(client, income),
            format='json',
        )

        assert (
            preview.data['public_number']
            == created.data['document']['public_number']
        )
