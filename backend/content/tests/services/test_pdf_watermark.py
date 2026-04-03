"""Tests for add_watermark_to_pdf in pdf_utils."""
import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import add_watermark_to_pdf

pytestmark = pytest.mark.django_db


def _make_minimal_pdf(pages=1):
    """Generate a minimal valid PDF with the given number of pages."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for i in range(pages):
        c.drawString(72, 700, f'Page {i + 1}')
        c.showPage()
    c.save()
    return buf.getvalue()


class TestAddWatermarkToPdf:
    def test_returns_valid_pdf_with_same_page_count(self):
        from pypdf import PdfReader

        original = _make_minimal_pdf(pages=2)
        result = add_watermark_to_pdf(original)

        assert isinstance(result, bytes)
        assert len(result) > 0

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2
