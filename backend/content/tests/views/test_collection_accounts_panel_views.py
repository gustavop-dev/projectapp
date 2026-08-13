"""API tests for the panel collection accounts (Cobros) endpoints."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from content.models import Document, HostingRecord, IncomeRecord, IssuerProfile
from content.services.hosting_billing_service import (
    send_hosting_collection_account,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def issuer(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    profile = IssuerProfile.objects.order_by('pk').first()
    profile.default_payment_methods = [
        {'payment_method_type': 'bank_transfer', 'bank_name': 'Bancolombia'},
    ]
    profile.save()
    return profile


def make_hosting(**overrides):
    defaults = {
        'client_name': 'German - Kore',
        'client_email': 'german@korehealths.com',
        'domain_url': 'https://korehealths.com/',
        'monthly_value': Decimal('91667.00'),
        'payment_modality': 'semiannual',
        'payment_per_cycle': Decimal('550002.00'),
        'valid_to': date(2026, 7, 20),
        'is_active': True,
    }
    defaults.update(overrides)
    return HostingRecord.objects.create(**defaults)


def issue_for(hosting):
    return send_hosting_collection_account(hosting)['document']


class TestSendEndpoint:
    def test_send_creates_and_emails(self, super_client):
        hosting = make_hosting()
        response = super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/send-collection-account/',
        )
        assert response.status_code == 201, response.data
        assert response.data['email_sent'] is True
        assert response.data['document']['public_number']
        assert response.data['document']['origin'] == 'hosting'
        hosting.refresh_from_db()
        assert hosting.billing_requested_at is not None

    def test_send_without_client_email_returns_400(self, super_client):
        hosting = make_hosting(client_email='')
        response = super_client.post(
            f'/api/accounting/hostings/{hosting.pk}/send-collection-account/',
        )
        assert response.status_code == 400
        assert 'email' in response.data['error']

    def test_requires_superuser(self, admin_client):
        hosting = make_hosting()
        response = admin_client.post(
            f'/api/accounting/hostings/{hosting.pk}/send-collection-account/',
        )
        assert response.status_code == 403


class TestListAndDetail:
    def test_list_filters_and_meta(self, super_client):
        issue_for(make_hosting())
        other = issue_for(make_hosting(
            client_name='Nestor - Xpandia',
            client_email='nestor@xpandia.global',
            domain_url='https://xpandia.global/',
        ))
        other.commercial_status = Document.CommercialStatus.PAID
        other.save(update_fields=['commercial_status'])

        response = super_client.get('/api/accounting/collection-accounts/')
        assert response.status_code == 200
        assert len(response.data['results']) == 2
        assert response.data['meta']['issued_count'] == 1
        assert response.data['meta']['paid_count'] == 1
        assert response.data['meta']['issued_total'] == '550002.00'

        issued_only = super_client.get(
            '/api/accounting/collection-accounts/?commercial_status=issued',
        )
        assert len(issued_only.data['results']) == 1

        search = super_client.get(
            '/api/accounting/collection-accounts/?q=Xpandia',
        )
        assert len(search.data['results']) == 1

    def test_overdue_flag(self, super_client):
        document = issue_for(make_hosting())
        Document.objects.filter(pk=document.pk).update(
            due_date=date.today() - timedelta(days=2),
        )
        response = super_client.get('/api/accounting/collection-accounts/')
        assert response.data['results'][0]['is_overdue'] is True

    def test_detail_and_pdf(self, super_client):
        document = issue_for(make_hosting())
        detail = super_client.get(
            f'/api/accounting/collection-accounts/{document.pk}/',
        )
        assert detail.status_code == 200
        assert detail.data['items'][0]['unit_price'] == '550002.00'
        assert detail.data['payment_methods'][0]['bank_name'] == 'Bancolombia'

        pdf = super_client.get(
            f'/api/accounting/collection-accounts/{document.pk}/pdf/',
        )
        assert pdf.status_code == 200
        assert pdf['Content-Type'] == 'application/pdf'
        assert pdf.content[:4] == b'%PDF'


class TestLifecycleActions:
    def test_resend(self, super_client):
        document = issue_for(make_hosting())
        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/resend/',
        )
        assert response.status_code == 200
        assert response.data['email_sent'] is True

    def test_mark_paid(self, super_client):
        document = issue_for(make_hosting())
        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/mark-paid/',
        )
        assert response.status_code == 200
        assert response.data['commercial_status'] == 'paid'

    def test_cancel_resumes_expiry_cadence(self, super_client):
        hosting = make_hosting()
        document = issue_for(hosting)
        hosting.refresh_from_db()
        assert hosting.billing_requested_at is not None

        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/cancel/',
        )
        assert response.status_code == 200
        assert response.data['commercial_status'] == 'cancelled'
        hosting.refresh_from_db()
        assert hosting.billing_requested_at is None

    def test_paid_cannot_be_cancelled(self, super_client):
        document = issue_for(make_hosting())
        super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/mark-paid/',
        )
        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/cancel/',
        )
        assert response.status_code == 400


def make_income(**overrides):
    fields = {
        'concept': 'Kore - Inicio 40%',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-07-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def link_income(document, income):
    Document.objects.filter(pk=document.pk).update(income_record=income)
    document.refresh_from_db()
    return document


class TestIncomeLinkedAccounts:
    def test_origin_income_filter_and_fields(self, super_client):
        issue_for(make_hosting())
        income = make_income()
        document = link_income(issue_for(make_hosting(
            client_name='Nestor - Xpandia',
            client_email='nestor@xpandia.global',
            domain_url='https://xpandia.global/',
        )), income)
        # Only hosting outranks an income link in get_origin, so clear the
        # hosting FK to model a modal-created cuenta.
        Document.objects.filter(pk=document.pk).update(hosting_record=None)

        response = super_client.get(
            '/api/accounting/collection-accounts/?origin=income',
        )
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        row = response.data['results'][0]
        assert row['origin'] == 'income'
        assert row['origin_label'] == 'Ingreso'
        assert row['income_record_id'] == income.pk
        assert row['income_kind'] == 'expected'

    def test_a_project_does_not_relabel_an_income_driven_cuenta(
        self, super_client,
    ):
        """A cuenta inherits its income's project; that must not turn its
        origin into 'project' and drop it out of the income filter."""
        from accounts.models import Project
        from django.contrib.auth import get_user_model

        client_user = get_user_model().objects.create_user(
            username='nestor@xpandia.global', email='nestor@xpandia.global',
            password='pass12345', first_name='Néstor', last_name='Franco',
        )
        income = make_income()
        document = link_income(issue_for(make_hosting()), income)
        project = Project.objects.create(name='Xpandia', client=client_user)
        Document.objects.filter(pk=document.pk).update(
            hosting_record=None, project=project,
        )

        response = super_client.get(
            '/api/accounting/collection-accounts/?origin=income',
        )

        assert [r['id'] for r in response.data['results']] == [document.pk]
        assert response.data['results'][0]['origin'] == 'income'
        # And it must not leak into the project bucket either.
        projects = super_client.get(
            '/api/accounting/collection-accounts/?origin=project',
        )
        assert projects.data['results'] == []

    def test_mark_paid_blocked_while_linked_income_pending(self, super_client):
        income = make_income()
        document = link_income(issue_for(make_hosting()), income)

        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/mark-paid/',
        )

        assert response.status_code == 409
        assert 'saldo pendiente' in response.data['error']
        document.refresh_from_db()
        assert document.commercial_status == Document.CommercialStatus.ISSUED

    def test_mark_paid_allowed_once_income_fully_paid(self, super_client):
        income = make_income()
        document = link_income(issue_for(make_hosting()), income)
        IncomeRecord.objects.create(
            concept='Kore - Inicio 40% (líquido)',
            kind=IncomeRecord.Kind.LIQUID,
            expected_income=income,
            period_date='2026-07-15',
            total_amount=Decimal('1000000.00'),
            gustavo_amount=Decimal('500000.00'),
            carlos_amount=Decimal('500000.00'),
        )

        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/mark-paid/',
        )

        assert response.status_code == 200
        assert response.data['commercial_status'] == 'paid'

    def test_mark_paid_direct_when_the_linked_income_is_liquid(self, super_client):
        # A liquid income is money already received: it carries no collection
        # state to settle, so the guard that protects expected incomes must
        # not stand in the way here.
        income = make_income(
            concept='Kore - Inicio 40% (recibido)',
            kind=IncomeRecord.Kind.LIQUID,
        )
        document = link_income(issue_for(make_hosting()), income)

        response = super_client.post(
            f'/api/accounting/collection-accounts/{document.pk}/mark-paid/',
        )

        assert response.status_code == 200
        assert response.data['commercial_status'] == 'paid'
