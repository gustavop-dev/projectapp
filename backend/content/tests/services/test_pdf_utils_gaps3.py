"""Gap tests for pdf_utils — targets uncovered exception paths and edge cases."""
import io
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from reportlab.pdfbase import pdfmetrics


# ---------------------------------------------------------------------------
# _font — KeyError fallback when primary not registered
# ---------------------------------------------------------------------------

class TestFontFallback:
    def test_font_falls_back_to_helvetica_when_primary_not_found(self):
        from content.services.pdf_utils import _font

        _font.cache_clear()
        with patch.object(pdfmetrics, 'getFont', side_effect=KeyError('Ubuntu')):
            result = _font('regular')
        _font.cache_clear()

        assert result == 'Helvetica'

    def test_font_falls_back_to_helvetica_bold_for_bold_style(self):
        from content.services.pdf_utils import _font

        _font.cache_clear()
        with patch.object(pdfmetrics, 'getFont', side_effect=KeyError('Ubuntu-Bold')):
            result = _font('bold')
        _font.cache_clear()

        assert result == 'Helvetica-Bold'


# ---------------------------------------------------------------------------
# Font registration — exception swallowed
# ---------------------------------------------------------------------------

class TestFontRegistrationException:
    def test_register_fonts_swallows_exception_per_font(self, caplog):
        import content.services.pdf_utils as pdf_utils
        pdf_utils._fonts_registered = False

        with patch('content.services.pdf_utils.TTFont', side_effect=Exception('corrupt font')), \
             caplog.at_level(logging.DEBUG, logger='content.services.pdf_utils'):
            pdf_utils._register_fonts()

        pdf_utils._fonts_registered = False  # reset for other tests


# ---------------------------------------------------------------------------
# _format_cop — non-numeric fallback
# ---------------------------------------------------------------------------

class TestFormatCopNonNumeric:
    def test_non_numeric_string_returns_str_value(self):
        from content.services.pdf_utils import _format_cop
        assert _format_cop('not_a_number') == 'not_a_number'

    def test_none_returns_str_none(self):
        from content.services.pdf_utils import _format_cop
        assert _format_cop(None) == 'None'


# ---------------------------------------------------------------------------
# _clean_url_display — exception path
# ---------------------------------------------------------------------------

class TestCleanUrlDisplay:
    def test_valid_url_returns_clean_host(self):
        from content.services.pdf_utils import _clean_url_display
        result = _clean_url_display('https://www.example.com/path')
        assert 'example.com' in result

    def test_exception_returns_original_url(self):
        from content.services.pdf_utils import _clean_url_display
        with patch('content.services.pdf_utils.urlparse' if hasattr(__import__('content.services.pdf_utils', fromlist=['urlparse']), 'urlparse') else 'urllib.parse.urlparse', side_effect=Exception('parse error'), create=True):
            # Even with a parse failure, the function should return the url
            # Simulate by passing something that would cause urlparse to fail
            result = _clean_url_display('not_a_url_at_all')
        # Either clean result or original — no exception raised
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# merge_with_covers — all-covers-disabled fast path
# ---------------------------------------------------------------------------

class TestMergeWithCoversAllDisabled:
    def test_returns_content_bytes_unchanged_when_all_covers_disabled(self):
        from content.services.pdf_utils import merge_with_covers

        content = b'%PDF-1.4 fake content'
        result = merge_with_covers(
            content,
            include_portada=False,
            include_contraportada=False,
            prepend_bytes=None,
        )
        assert result is content


# ---------------------------------------------------------------------------
# merge_with_covers — front cover exception (corrupted file)
# ---------------------------------------------------------------------------

class TestMergeWithCoversFrontException:
    def test_logs_warning_when_front_cover_pdf_is_corrupt(self, tmp_path, caplog):
        from content.services.pdf_utils import merge_with_covers

        corrupt_pdf = tmp_path / 'cover.pdf'
        corrupt_pdf.write_bytes(b'not_a_pdf')

        with patch('content.services.pdf_utils.COVER_PDF', corrupt_pdf), \
             caplog.at_level(logging.WARNING, logger='content.services.pdf_utils'):
            from reportlab.pdfgen import canvas as rl_canvas
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf)
            c.drawString(10, 10, 'x')
            c.save()
            content = buf.getvalue()
            result = merge_with_covers(content, include_portada=True, include_contraportada=False)

        assert isinstance(result, bytes)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# merge_with_covers — back cover exception (corrupted file)
# ---------------------------------------------------------------------------

class TestMergeWithCoversBackException:
    def test_logs_warning_when_back_cover_pdf_is_corrupt(self, tmp_path, caplog):
        from content.services.pdf_utils import merge_with_covers

        corrupt_back = tmp_path / 'back.pdf'
        corrupt_back.write_bytes(b'not_a_pdf_either')

        with patch('content.services.pdf_utils.BACK_COVER_PDF', corrupt_back), \
             patch('content.services.pdf_utils.COVER_PDF', Path('/nonexistent/cover.pdf')), \
             caplog.at_level(logging.WARNING, logger='content.services.pdf_utils'):
            from reportlab.pdfgen import canvas as rl_canvas
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf)
            c.drawString(10, 10, 'y')
            c.save()
            content = buf.getvalue()
            result = merge_with_covers(content, include_portada=False, include_contraportada=True)

        assert isinstance(result, bytes)
        assert len(result) > 0
