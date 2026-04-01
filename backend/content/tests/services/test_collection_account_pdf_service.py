"""Tests for CollectionAccountPdfService."""

import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from pypdf import PdfReader

from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentItem,
    DocumentPaymentMethod,
    IssuerProfile,
)
from content.services.collection_account_pdf_service import CollectionAccountPdfService
from content.services.document_type_utils import (
    get_collection_account_document_type,
    get_markdown_document_type,
)

User = get_user_model()
pytestmark = pytest.mark.django_db

# Enough line items to exhaust vertical space on A4 after headers (ensure_space / showPage).
_PDF_LINE_COUNT_MULTIPAGE = 72


def _issued_collection_document_with_items_and_payments(issuer, project, client_user, line_count):
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Heavy invoice',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        issuer=issuer,
        public_number='PA-2026-2000',
        issue_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15),
        subtotal=Decimal(str(line_count)),
        tax_total=Decimal('0'),
        total=Decimal(str(line_count)),
        currency='COP',
        city='Bogotá',
    )
    multiline_concept = 'Phase A\nPhase B\nPhase C\n' + ('detail text ' * 30)
    DocumentCollectionAccount.objects.create(
        document=doc,
        payer_name='Payer Legal',
        payer_identification='NIT 900',
        payer_address='Street 1',
        payer_phone='3000000000',
        payer_email='pay@example.com',
        customer_name='Customer Co',
        customer_identification='CC 1',
        customer_contact_name='Contact Name',
        customer_email='c@example.com',
        customer_address='Client Ave',
        billing_concept=multiline_concept,
    )
    rows = [
        DocumentItem(
            document=doc,
            position=idx,
            description=f'Line {idx:03d} ' + ('x' * 40),
            quantity=Decimal('1'),
            unit_price=Decimal('1'),
            discount_amount=Decimal('0'),
            tax_amount=Decimal('0'),
            line_total=Decimal('1'),
        )
        for idx in range(line_count)
    ]
    DocumentItem.objects.bulk_create(rows)
    DocumentPaymentMethod.objects.create(
        document=doc,
        payment_method_type=DocumentPaymentMethod.MethodType.BANK_TRANSFER,
        bank_name='Banco Demo',
        account_number='000-111',
        payment_instructions='Transfer to savings account ending 111',
    )
    DocumentPaymentMethod.objects.create(
        document=doc,
        payment_method_type=DocumentPaymentMethod.MethodType.NEQUI,
        account_number='300222',
        payment_instructions='Nequi business wallet',
    )
    return doc


@pytest.fixture
def issuer():
    return IssuerProfile.objects.create(name='PDF Issuer', legal_name='PDF LLC')


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='pdf-client@test.com',
        email='pdf-client@test.com',
        password='pass12345',
        first_name='Doc',
        last_name='User',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
    )
    return user


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='PDF Project',
        client=client_user,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )


def test_generate_returns_none_when_document_is_not_collection_account(project, client_user):
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='Markdown doc',
        document_type=md,
        project=project,
        client_user=client_user,
    )

    result = CollectionAccountPdfService.generate(doc)

    assert result is None


def test_generate_returns_none_when_collection_account_extension_row_is_absent(project, client_user):
    """Return None when the document has no collection_account extension row."""
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='No extension',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        public_number='PA-2026-0001',
        subtotal=Decimal('0'),
        tax_total=Decimal('0'),
        total=Decimal('0'),
    )

    result = CollectionAccountPdfService.generate(doc)

    assert result is None


def test_generate_returns_pdf_bytes_for_issued_collection_account(issuer, project, client_user):
    """Return PDF bytes for an issued collection account with line items."""
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Invoice PDF',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        issuer=issuer,
        public_number='PA-2026-0999',
        subtotal=Decimal('100'),
        tax_total=Decimal('0'),
        total=Decimal('100'),
        currency='COP',
    )
    DocumentCollectionAccount.objects.create(
        document=doc,
        payer_name='Payer',
        customer_name='Customer',
    )
    DocumentItem.objects.create(
        document=doc,
        position=0,
        description='Service',
        quantity=Decimal('1'),
        unit_price=Decimal('100'),
        line_total=Decimal('100'),
    )

    pdf_bytes = CollectionAccountPdfService.generate(doc)

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 100
    assert pdf_bytes[:4] == b'%PDF'


def test_generate_returns_none_when_canvas_raises(project, client_user):
    """Return None when ReportLab canvas construction raises."""
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Broken PDF',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        public_number='PA-2026-0888',
        subtotal=Decimal('0'),
        tax_total=Decimal('0'),
        total=Decimal('0'),
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with patch('content.services.collection_account_pdf_service.canvas.Canvas') as mock_canvas:
        mock_canvas.side_effect = RuntimeError('canvas failed')

        result = CollectionAccountPdfService.generate(doc)

    assert result is None


def test_generate_pdf_includes_payment_methods_when_document_has_payment_methods(
    issuer, project, client_user,
):
    doc = _issued_collection_document_with_items_and_payments(
        issuer, project, client_user, line_count=3,
    )

    pdf_bytes = CollectionAccountPdfService.generate(doc)

    assert pdf_bytes is not None
    assert pdf_bytes[:4] == b'%PDF'
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1


def test_generate_pdf_uses_more_than_one_page_when_line_items_trigger_page_breaks(
    issuer, project, client_user,
):
    doc = _issued_collection_document_with_items_and_payments(
        issuer, project, client_user, line_count=_PDF_LINE_COUNT_MULTIPAGE,
    )

    pdf_bytes = CollectionAccountPdfService.generate(doc)

    assert pdf_bytes is not None
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 2
