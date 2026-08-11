"""Tests for CollectionAccountPdfService."""

import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4, A5

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

# Far more detail lines than a real cuenta de cobro carries — enough that a
# fixed-height page would have had to break.
_PDF_LINE_COUNT_MANY = 72


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


def test_generate_renders_words_formats_and_parties(issuer, project, client_user):
    """Client-facing content: valor en letras, COP/date formats, ident types,
    party blocks — and none of the internal or non-applicable sections."""
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Cuenta de cobro — Desarrollo',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        issuer=issuer,
        public_number='PA-ACME-001',
        issue_date=date(2026, 8, 5),
        due_date=date(2026, 8, 13),
        subtotal=Decimal('1490000'),
        tax_total=Decimal('0'),
        total=Decimal('1490000'),
        currency='COP',
        city='Bogotá',
    )
    DocumentCollectionAccount.objects.create(
        document=doc,
        payer_name='ProjectApp SAS',
        payer_identification='901000000',
        payer_identification_type='NIT',
        customer_name='Acme Soluciones',
        customer_identification='901234567',
        customer_identification_type='NIT',
        billing_concept='Desarrollo módulo de reportes',
    )
    DocumentItem.objects.create(
        document=doc,
        position=0,
        description='Desarrollo módulo de reportes',
        quantity=Decimal('1'),
        unit_price=Decimal('1490000'),
        line_total=Decimal('1490000'),
    )

    pdf_bytes = CollectionAccountPdfService.generate(doc)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ''.join(page.extract_text() for page in reader.pages)
    assert 'Un millón cuatrocientos noventa mil pesos M/CTE' in text
    assert 'Total (COP): $1.490.000' in text
    assert 'NIT 901234567' in text
    assert 'NIT 901000000' in text
    assert '5 de agosto de 2026' in text
    assert 'Estado' not in text

    # The block above the amounts holds the issuer's own data (payer_* is
    # snapshotted from the issuer), so it is the Emisor, not the Pagador.
    assert 'Emisor' in text
    assert 'ProjectApp SAS' in text
    assert 'Pagador' not in text

    # Sections that do not apply: nothing is billed by units, no tax is ever
    # itemised (so Subtotal only ever repeated the Total), and the document
    # carries no signature block.
    assert 'Cant.' not in text
    assert 'Impuestos' not in text
    assert 'Subtotal' not in text
    assert 'Firma' not in text

    # The concepto is not repeated a third time in a field of its own.
    assert 'Concepto de cobro' not in text
    assert text.count('Desarrollo módulo de reportes') == 2

    # Compact page: A5 width, height cut to the content instead of an A4 sheet.
    page = reader.pages[0]
    assert len(reader.pages) == 1
    assert float(page.mediabox.width) == pytest.approx(A5[0], abs=1)
    assert float(page.mediabox.height) < A4[1]


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


def test_generate_grows_the_page_instead_of_breaking_it_on_many_line_items(
    issuer, project, client_user,
):
    """Many line items stretch the single page rather than spilling onto a
    second sheet — the operator reviews and the client reads one document."""
    short = _issued_collection_document_with_items_and_payments(
        issuer, project, client_user, line_count=1,
    )
    long = _issued_collection_document_with_items_and_payments(
        issuer, project, client_user, line_count=_PDF_LINE_COUNT_MANY,
    )

    short_page = PdfReader(
        io.BytesIO(CollectionAccountPdfService.generate(short)),
    ).pages
    long_pages = PdfReader(
        io.BytesIO(CollectionAccountPdfService.generate(long)),
    ).pages

    assert len(short_page) == 1
    assert len(long_pages) == 1
    assert float(long_pages[0].mediabox.height) > float(
        short_page[0].mediabox.height,
    )
    # Width stays put: only the height follows the content.
    assert float(long_pages[0].mediabox.width) == pytest.approx(
        float(short_page[0].mediabox.width),
    )


def _billable_document(issuer, project, client_user, **method_fields):
    """Minimal issued cuenta de cobro with one line item and one payment method."""
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Cuenta de cobro — Hosting',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        issuer=issuer,
        public_number='PA-MIMITTOS-001',
        issue_date=date(2026, 8, 11),
        due_date=date(2026, 8, 19),
        subtotal=Decimal('1490000'),
        tax_total=Decimal('0'),
        total=Decimal('1490000'),
        currency='COP',
        city='Medellín',
    )
    DocumentCollectionAccount.objects.create(
        document=doc,
        payer_name='ProjectApp',
        customer_name='Mimittos SAS',
        billing_concept='Hosting agosto 2026',
    )
    DocumentItem.objects.create(
        document=doc,
        position=0,
        description='Hosting y mantenimiento',
        quantity=Decimal('1'),
        unit_price=Decimal('1490000'),
        line_total=Decimal('1490000'),
    )
    if method_fields:
        DocumentPaymentMethod.objects.create(document=doc, **method_fields)
    return doc


_BANK_METHOD = {
    'payment_method_type': DocumentPaymentMethod.MethodType.BANK_TRANSFER,
    'bank_name': 'Bancolombia',
    'account_type': 'Ahorros',
    'account_number': '00774149350',
    'account_holder_name': 'GUSTAVO ADOLFO PEREZ PEREZ',
    'account_holder_identification': 'NIT 1021513348-7',
}


def test_generate_writes_the_document_metadata(issuer, project, client_user):
    """A viewer reads /Title, not the download filename — an empty one is what
    made Chrome label the tab 'untitled'."""
    doc = _billable_document(issuer, project, client_user, **_BANK_METHOD)

    reader = PdfReader(io.BytesIO(CollectionAccountPdfService.generate(doc)))

    assert reader.metadata['/Title'] == 'PA-MIMITTOS-001'
    assert reader.metadata['/Author'] == 'ProjectApp'
    assert reader.metadata['/Subject'] == (
        'Cuenta de cobro — Mimittos SAS — 11 de agosto de 2026'
    )
    assert reader.metadata['/CreationDate']


def test_generate_paints_the_brand_watermark_behind_the_content(
    issuer, project, client_user,
):
    """The wordmark has to be there, faint, and not at the cost of the text."""
    doc = _billable_document(issuer, project, client_user, **_BANK_METHOD)

    reader = PdfReader(io.BytesIO(CollectionAccountPdfService.generate(doc)))
    page = reader.pages[0]
    images = [
        ref.get_object() for ref in page['/Resources']['/XObject'].values()
    ]
    alphas = [
        state.get_object()['/ca']
        for state in page['/Resources']['/ExtGState'].values()
        if '/ca' in state.get_object()
    ]

    assert any(image.get('/Subtype') == '/Image' for image in images)
    # Low enough to sit behind the text rather than compete with it.
    assert alphas and max(alphas) <= 0.1
    # The point of a watermark is that the document still reads.
    assert 'Cuenta de cobro' in page.extract_text()


def test_generate_prints_the_full_payment_block(issuer, project, client_user):
    """Entidad, tipo, número and titular all reach the page: dropping any of
    them leaves the client unable to actually transfer the money."""
    doc = _billable_document(issuer, project, client_user, **_BANK_METHOD)

    reader = PdfReader(io.BytesIO(CollectionAccountPdfService.generate(doc)))
    text = ''.join(page.extract_text() for page in reader.pages)

    assert 'Formas de pago' in text
    assert 'Transferencia bancaria' in text
    assert 'Bancolombia' in text
    assert 'Ahorros' in text
    assert '00774149350' in text
    assert 'GUSTAVO ADOLFO PEREZ PEREZ' in text
    assert 'NIT 1021513348-7' in text


def test_generate_omits_the_payment_block_when_no_method_is_configured(
    issuer, project, client_user,
):
    """No configured account must print no box at all — an empty frame of
    labels reads worse than nothing."""
    doc = _billable_document(issuer, project, client_user)

    reader = PdfReader(io.BytesIO(CollectionAccountPdfService.generate(doc)))
    text = ''.join(page.extract_text() for page in reader.pages)

    assert 'Formas de pago' not in text
    assert 'Total (COP): $1.490.000' in text
