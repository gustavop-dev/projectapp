"""Tests for bounded conversion of proposal attachments to Markdown."""
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from django.core.files.base import ContentFile
from openpyxl import Workbook
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from content.models import ProposalDocument
from content.services.attachment_markdown import (
    MarkdownExportError,
    docx_markdown,
    extract_attachment_markdown,
    pdf_markdown,
    read_attachment,
    xlsx_markdown,
)

pytestmark = pytest.mark.django_db


def _proposal_document(proposal, name, content):
    document = ProposalDocument.objects.create(
        proposal=proposal,
        document_type=ProposalDocument.DOC_TYPE_LEGAL_ANNEX,
        title='Anexo de prueba',
    )
    document.file.save(name, ContentFile(content), save=True)
    return document


def _pdf_with_text(text):
    output = BytesIO()
    canvas = Canvas(output)
    canvas.drawString(72, 720, text)
    canvas.save()
    return output.getvalue()


def _pdf_pages(count, password=None):
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(count):
        writer.add_blank_page(width=612, height=792)
    if password:
        writer.encrypt(password)
    writer.write(output)
    return output.getvalue()


def _docx_bytes():
    document = '''<?xml version="1.0" encoding="UTF-8"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
      <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Scope</w:t></w:r></w:p>
      <w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr><w:r><w:t>First item</w:t></w:r></w:p>
      <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Feature</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:p><w:r><w:t>Orders</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Included</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    </w:body></w:document>'''
    numbering = '''<?xml version="1.0" encoding="UTF-8"?>
    <w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:numFmt w:val="bullet"/></w:lvl></w:abstractNum>
      <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
    </w:numbering>'''
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('word/document.xml', document)
        archive.writestr('word/numbering.xml', numbering)
    return output.getvalue()


def _xlsx_bytes(rows):
    book = Workbook()
    sheet = book.active
    sheet.title = 'Budget'
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    book.save(output)
    return output.getvalue()


def _compressed_archive(size):
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('word/document.xml', 'x' * size)
    return output.getvalue()


def test_docx_markdown_preserves_heading_list_and_table_content():
    """Fails if DOCX extraction drops structured text a user expects to copy."""
    markdown, warnings = docx_markdown(_docx_bytes())

    assert '# Scope' in markdown
    assert '- First item' in markdown
    assert '| Feature | Value |' in markdown
    assert '| Orders | Included |' in markdown
    assert warnings == ['Vista del contenido textual; el diseño, las imágenes y los objetos incrustados no se reproducen.']


def test_xlsx_markdown_preserves_formula_as_literal_text():
    """Fails if spreadsheet extraction evaluates formulas instead of copying their literal expression."""
    markdown, warnings = xlsx_markdown(_xlsx_bytes([['Item', 'Amount'], ['Build', '=1+1']]))

    assert '## Budget' in markdown
    assert '| Build | =1+1 |' in markdown
    assert warnings[-1] == 'Las fórmulas se muestran como texto; no se calculan ni se consultan vínculos externos.'


def test_pdf_markdown_extracts_text_with_reconstruction_warning():
    """Fails if a text PDF is copied without warning that its visual layout was reconstructed."""
    markdown, warnings = pdf_markdown(_pdf_with_text('PDF BODY'))

    assert markdown == 'PDF BODY\n'
    assert warnings == ['Texto extraído del PDF; el formato fue reconstruido. Las imágenes y firmas gráficas no se copian.']


@pytest.mark.parametrize(
    ('filename', 'expected_message'),
    [
        ('legacy.doc', 'Convierte el archivo a DOCX o XLSX'),
        ('legacy.xls', 'Convierte el archivo a DOCX o XLSX'),
        ('scan.png', 'Este formato no admite copia de texto'),
    ],
)
def test_attachment_markdown_rejects_formats_without_safe_text_extraction(proposal, filename, expected_message):
    """Fails if legacy office files or images enter the binary parser."""
    document = _proposal_document(proposal, filename, b'unsupported binary bytes')

    with pytest.raises(MarkdownExportError) as error:
        extract_attachment_markdown(document)

    assert error.value.code == 'unsupported_format'
    assert error.value.status == 415
    assert expected_message in str(error.value)


def test_attachment_markdown_returns_controlled_error_for_corrupt_pdf(proposal):
    """Fails if a corrupted PDF crashes the extraction worker instead of returning a recoverable error."""
    document = _proposal_document(proposal, 'broken.pdf', b'not a PDF')

    with pytest.raises(MarkdownExportError) as error:
        extract_attachment_markdown(document)

    assert error.value.code == 'invalid_document'
    assert error.value.status == 422


def test_attachment_markdown_rejects_password_protected_pdf(proposal):
    """Fails if a protected PDF is treated as an empty or successfully copied attachment."""
    document = _proposal_document(proposal, 'protected.pdf', _pdf_pages(1, password='secret'))

    with pytest.raises(MarkdownExportError) as error:
        extract_attachment_markdown(document)

    assert error.value.code == 'document_protected'
    assert error.value.status == 422


def test_read_attachment_rejects_file_larger_than_configured_limit(monkeypatch, proposal):
    """Fails if the upload byte cap is bypassed before an attachment enters a parser process."""
    document = _proposal_document(proposal, 'large.pdf', b'12345')
    monkeypatch.setattr('content.services.attachment_markdown.MAX_FILE_BYTES', 4)

    with pytest.raises(MarkdownExportError) as error:
        read_attachment(document)

    assert error.value.code == 'document_too_large'
    assert error.value.status == 413


def test_pdf_markdown_rejects_more_pages_than_configured_limit(monkeypatch):
    """Fails if a page-heavy PDF avoids the configured extraction bound."""
    monkeypatch.setattr('content.services.attachment_markdown.MAX_PDF_PAGES', 1)

    with pytest.raises(MarkdownExportError) as error:
        pdf_markdown(_pdf_pages(2))

    assert error.value.code == 'document_too_large'
    assert error.value.status == 413


def test_xlsx_markdown_rejects_more_cells_than_configured_limit(monkeypatch):
    """Fails if a workbook can exceed the cell cap while being copied to Markdown."""
    monkeypatch.setattr('content.services.attachment_markdown.MAX_SHEET_CELLS', 1)

    with pytest.raises(MarkdownExportError) as error:
        xlsx_markdown(_xlsx_bytes([['first', 'second']]))

    assert error.value.code == 'document_too_large'
    assert error.value.status == 413


def test_docx_markdown_rejects_archive_larger_than_configured_expansion_limit(monkeypatch):
    """Fails if a highly compressed office archive can expand past the safe parser budget."""
    monkeypatch.setattr('content.services.attachment_markdown.MAX_EXPANDED_BYTES', 8)

    with pytest.raises(MarkdownExportError) as error:
        docx_markdown(_compressed_archive(9))

    assert error.value.code == 'document_too_large'
    assert error.value.status == 413


def test_xlsx_markdown_rejects_output_larger_than_one_million_characters():
    """Fails if a workbook produces truncated Markdown after passing the extraction limits."""
    with pytest.raises(MarkdownExportError) as error:
        xlsx_markdown(_xlsx_bytes([['Body']] + [['x' * 32_767]] * 31))

    assert error.value.code == 'document_too_large'
    assert error.value.status == 413
