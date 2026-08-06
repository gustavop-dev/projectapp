"""Tests for build_collection_account_email: what preview and send both show.

First coverage of this module — sibling of test_collection_account_service.py /
test_collection_account_pdf_service.py / test_collection_account_numbering.py.
Until now this was only verified indirectly, via a loose HTML substring check
on the create endpoint (test_collection_account_create_views.py).
"""
from decimal import Decimal

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

from content.models import Document, IncomeRecord, IssuerProfile
from content.services.collection_account_email_service import (
    build_collection_account_email,
)

User = get_user_model()
pytestmark = pytest.mark.django_db

CREATE_URL = '/api/accounting/collection-accounts/create/'


@pytest.fixture(autouse=True)
def issuer(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    profile = IssuerProfile.objects.order_by('pk').first()
    profile.default_payment_methods = [
        {'payment_method_type': 'bank_transfer', 'bank_name': 'Bancolombia'},
    ]
    profile.save()
    return profile


def make_client(email='ana@acme.co', company='Acme Soluciones'):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
        first_name='Ana', last_name='Pérez',
    )
    UserProfile.objects.create(user=user, company_name=company)
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


class TestBuildCollectionAccountEmail:
    def test_renders_period_valor_and_payment_methods_from_a_real_document(
        self, super_client,
    ):
        """Fails if a regression corrupts what the preview modal AND the real client email show (the only function both share)."""
        client = make_client()
        income = make_income()
        response = super_client.post(
            CREATE_URL,
            payload(client, income, items=[{
                'description': 'Desarrollo módulo de reportes',
                'quantity': '1',
                'unit_price': '1490000.00',
                'period_start': '2026-08-01',
                'period_end': '2026-08-31',
            }]),
            format='json',
        )
        assert response.status_code == 201, response.data
        document = Document.objects.get(pk=response.data['document']['id'])

        email = build_collection_account_email(document)

        assert email['subject'] == (
            f'Cuenta de cobro {document.public_number} — ProjectApp'
        )
        assert 'Período facturado: 01/08/2026 a 31/08/2026.' in email['sections']
        valor = next(s for s in email['sections'] if s.startswith('Valor a pagar'))
        # startswith (not `in`) so a doubled-$ formatter regression is caught too.
        assert valor.startswith("Valor a pagar: $1'490.000 COP")
        methods = next(
            s for s in email['sections'] if s.startswith('Formas de pago')
        )
        assert 'Bank transfer · Bancolombia' in methods
        assert email['greeting'] == 'Hola Ana Pérez'

    def test_omits_period_and_payment_methods_sections_when_absent(
        self, super_client, issuer,
    ):
        """Fails if a dropped/inverted guard ships a blank or broken section."""
        issuer.default_payment_methods = []
        issuer.save()
        client = make_client()
        income = make_income()

        response = super_client.post(
            CREATE_URL, payload(client, income), format='json',
        )
        assert response.status_code == 201, response.data
        document = Document.objects.get(pk=response.data['document']['id'])

        email = build_collection_account_email(document)

        assert not any('Período facturado' in s for s in email['sections'])
        assert not any(s.startswith('Formas de pago') for s in email['sections'])
