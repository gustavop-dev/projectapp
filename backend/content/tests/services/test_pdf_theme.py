"""PdfTheme selection and default-preserves-professional guarantees."""
import io

import pytest
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

from content.services.pdf_theme import (
    PdfTheme, PROFESSIONAL_THEME, FRIENDLY_THEME, get_theme)

pytestmark = pytest.mark.django_db


class TestThemeSelection:
    def test_get_theme_friendly(self):
        assert get_theme('friendly') is FRIENDLY_THEME

    def test_get_theme_defaults_professional(self):
        assert get_theme('professional') is PROFESSIONAL_THEME
        assert get_theme('') is PROFESSIONAL_THEME
        assert get_theme(None) is PROFESSIONAL_THEME
        assert get_theme('nonsense') is PROFESSIONAL_THEME

    def test_professional_matches_legacy_constants(self):
        from content.services import pdf_utils as u
        assert PROFESSIONAL_THEME.h1_color == u.ESMERALD
        assert PROFESSIONAL_THEME.body_color == u.ESMERALD_80
        assert PROFESSIONAL_THEME.header_bar_color == u.ESMERALD

    def test_friendly_uses_preview_palette(self):
        from reportlab.lib.colors import HexColor
        assert FRIENDLY_THEME.h1_color == HexColor('#047857')
        assert FRIENDLY_THEME.body_color == HexColor('#374151')
        assert FRIENDLY_THEME.quote_bg == HexColor('#F0FDF4')

    def test_is_frozen(self):
        original = FRIENDLY_THEME.h1_color
        with pytest.raises(Exception):
            FRIENDLY_THEME.h1_color = None
        assert FRIENDLY_THEME.h1_color == original


class TestDefaultThemePreservesLook:
    def test_drawers_accept_theme_none_without_error(self):
        from content.services.pdf_utils import (
            _draw_header_bar, _draw_section_header, _draw_separator,
            _register_fonts)
        _register_fonts()
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        _draw_header_bar(c)                    # theme defaulted
        _draw_section_header(c, 780, '01', 'Titulo')
        _draw_separator(c, 700)
        c.save()
        assert buf.getvalue()[:4] == b'%PDF'
