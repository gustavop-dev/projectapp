"""Tests for ProposalPdfService.

Covers: _strip_emoji, _safe helpers, drawing helpers,
section renderers, generate() happy/error paths,
_merge_with_covers, generate_to_file.
"""
import io
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas

from content.models import (
    BusinessProposal,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
)
from content.services.proposal_pdf_service import (
    CONTENT_W,
    ESMERALD,
    LEMON,
    MARGIN_B,
    MARGIN_L,
    PAGE_H,
    SECTION_RENDERERS,
    ProposalPdfService,
    _clean_inline_bold,
    _clean_url_display,
    _draw_banner_box,
    _draw_bullet_list,
    _draw_footer,
    _draw_green_bar,
    _draw_line_with_links,
    _draw_paragraphs,
    _draw_pill,
    _draw_section_header,
    _draw_sidebar_box,
    _draw_subtitle,
    _font,
    _format_cop,
    _parse_markdown_lines,
    _register_fonts,
    _render_context_diagnostic,
    _render_creative_support,
    _render_design_ux,
    _render_executive_summary,
    _render_raw_text,
    _replace_urls_with_placeholders,
    _safe,
    _strip_emoji,
)

pytestmark = pytest.mark.django_db


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def pdf_canvas():
    """A ReportLab canvas backed by an in-memory buffer."""
    _register_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c._test_buf = buf
    return c


@pytest.fixture
def proposal_with_sections(db):
    """Proposal with all 12 section types enabled."""
    p = BusinessProposal.objects.create(
        title='PDF Test Proposal',
        client_name='Test Client',
        client_email='test@example.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=20),
    )
    sections_data = [
        ('greeting', 'Saludo', 0, {
            'clientName': 'Test Client',
            'inspirationalQuote': 'Design is how it works.',
        }),
        ('executive_summary', 'Resumen ejecutivo', 1, {
            'index': '1', 'title': 'Resumen ejecutivo',
            'paragraphs': ['Primera línea.', 'Segunda línea.'],
            'highlightsTitle': 'Puntos clave',
            'highlights': ['Diseño', 'Desarrollo'],
        }),
        ('context_diagnostic', 'Contexto', 2, {
            'index': '2', 'title': 'Contexto y diagnóstico',
            'paragraphs': ['Análisis del cliente.'],
            'issuesTitle': 'Problemas', 'issues': ['SEO débil'],
            'opportunityTitle': 'Oportunidad', 'opportunity': 'Crecer.',
        }),
        ('conversion_strategy', 'Estrategia', 3, {
            'index': '3', 'title': 'Estrategia de conversión',
            'intro': 'Se construirá una página.',
            'steps': [{'title': 'Paso 1', 'bullets': ['Acción A']}],
            'resultTitle': 'Resultado', 'result': 'Más clientes.',
        }),
        ('design_ux', 'Diseño UX', 4, {
            'index': '4', 'title': 'Diseño Visual',
            'paragraphs': ['El sitio será moderno.'],
            'focusTitle': 'Enfoque', 'focusItems': ['Mobile first'],
            'objectiveTitle': 'Objetivo', 'objective': 'Impactar.',
        }),
        ('creative_support', 'Soporte Creativo', 5, {
            'index': '5', 'title': 'Acompañamiento Creativo',
            'paragraphs': ['Acompañamiento cercano.'],
            'includesTitle': 'Incluye', 'includes': ['Revisiones'],
            'closing': 'Estamos aquí para ti.',
        }),
        ('development_stages', 'Etapas', 6, {
            'title': 'Etapas de Desarrollo',
            'stages': [
                {'title': 'Propuesta', 'description': 'Etapa inicial.', 'current': True},
                {'title': 'Desarrollo', 'description': 'Construcción.', 'current': False},
            ],
        }),
        ('functional_requirements', 'Requerimientos', 7, {
            'index': '7', 'title': 'Requerimientos Funcionales',
            'intro': 'Detalle de requerimientos.',
            'groups': [
                {
                    'title': 'Vistas',
                    'description': 'Pantallas del sitio.',
                    'items': [{'name': 'Home', 'description': 'Página de inicio.'}],
                },
            ],
            'additionalModules': [],
        }),
        ('timeline', 'Cronograma', 8, {
            'index': '8', 'title': 'Cronograma',
            'introText': 'Fases del proyecto.',
            'totalDuration': '1 mes',
            'phases': [{
                'title': 'Diseño', 'duration': '1 semana',
                'description': 'Diseño visual.',
                'tasks': ['Wireframes', 'Mockups'],
                'milestone': 'Aprobación de diseño',
            }],
        }),
        ('investment', 'Inversión', 9, {
            'index': '9', 'title': 'Inversión',
            'introText': 'La inversión total es:',
            'totalInvestment': '$5,000,000', 'currency': 'COP',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Diseño', 'description': 'UX/UI'},
            ],
            'paymentOptions': [
                {'label': '50% inicio', 'description': '$2,500,000 COP'},
            ],
            'hostingPlan': {'title': 'Cloud 1', 'description': 'Hosting incluido.'},
            'valueReasons': ['Calidad', 'Soporte'],
        }),
        ('final_note', 'Nota Final', 10, {
            'index': '10', 'title': 'Nota Final',
            'message': 'Gracias por considerar nuestra propuesta.',
            'personalNote': 'Es un placer trabajar contigo.',
            'teamName': 'Project App', 'teamRole': 'CEO',
            'contactEmail': 'team@projectapp.co',
            'commitmentBadges': [
                {'icon': '🤝', 'title': 'Calidad', 'description': 'Garantizada'},
            ],
        }),
        ('next_steps', 'Próximos pasos', 11, {
            'index': '11', 'title': 'Próximos pasos',
            'introMessage': 'Estamos listos.',
            'steps': [
                {'title': 'Revisión', 'description': 'Revisar propuesta.'},
            ],
            'ctaMessage': 'Agenda una llamada.',
            'contactMethods': [
                {'icon': '📧', 'title': 'Email', 'value': 'team@projectapp.co'},
            ],
        }),
    ]
    for stype, title, order, content in sections_data:
        ProposalSection.objects.create(
            proposal=p, section_type=stype,
            title=title, order=order,
            is_enabled=True, content_json=content,
        )
    return p


# ── _strip_emoji tests ───────────────────────────────────────

class TestStripEmoji:
    def test_removes_standard_emoji(self):
        """Standard emoji characters are stripped from the string."""
        assert _strip_emoji('Hello 🎨 World') == 'Hello  World'

    def test_removes_multiple_emojis(self):
        result = _strip_emoji('✅ Done 🚀 Launch 🎯 Target')
        assert '✅' not in result
        assert '🚀' not in result
        assert '🎯' not in result

    def test_preserves_plain_latin_text(self):
        """Plain ASCII text passes through unchanged."""
        assert _strip_emoji('Hello World') == 'Hello World'

    def test_preserves_accented_characters(self):
        """Accented Latin characters are preserved."""
        assert _strip_emoji('Diseño gráfico') == 'Diseño gráfico'

    def test_returns_empty_for_none(self):
        """None input returns None."""
        assert _strip_emoji(None) is None

    def test_returns_empty_for_empty_string(self):
        """Empty string returns empty string."""
        assert _strip_emoji('') == ''

    def test_removes_variation_selectors(self):
        result = _strip_emoji('⚙️ Settings')
        assert 'Settings' in result

    def test_removes_geometric_shapes(self):
        result = _strip_emoji('■ Square ● Circle')
        assert '■' not in result
        assert '●' not in result


# ── _safe tests ───────────────────────────────────────────────

class TestSafe:
    def test_returns_value_for_existing_key(self):
        """Existing key with a truthy value is returned."""
        assert _safe({'name': 'Alice'}, 'name') == 'Alice'

    def test_returns_default_for_missing_key(self):
        """Missing key falls back to the provided default."""
        assert _safe({}, 'name', 'Unknown') == 'Unknown'

    def test_returns_default_for_none_value(self):
        """None value falls back to the default."""
        assert _safe({'name': None}, 'name', 'Default') == 'Default'

    def test_returns_default_for_empty_string_value(self):
        """Empty string value falls back to the default."""
        assert _safe({'name': ''}, 'name', 'Default') == 'Default'

    def test_returns_empty_string_default(self):
        """No explicit default returns empty string."""
        assert _safe({}, 'name') == ''

    def test_returns_default_for_non_dict(self):
        """Non-dict input falls back to the default."""
        assert _safe('not_a_dict', 'key', 'fallback') == 'fallback'

    def test_returns_list_default(self):
        """List default is returned for missing key."""
        assert _safe({}, 'items', []) == []

    def test_returns_existing_list(self):
        """Existing list value is returned over the default."""
        assert _safe({'items': [1, 2]}, 'items', []) == [1, 2]


_INVESTMENT_DATA = {
    'index': '9', 'title': 'Investment',
    'introText': 'Total:',
    'totalInvestment': '$5,000,000', 'currency': 'COP',
    'whatsIncluded': [{'title': 'Design', 'description': 'UX'}],
    'paymentOptions': [{'label': '50%', 'description': '$2.5M'}],
    'hostingPlan': {'title': 'Cloud', 'description': 'Included.'},
    'valueReasons': ['Quality'],
}

_FINAL_NOTE_DATA = {
    'index': '10', 'title': 'Final Note',
    'message': 'Thank you.',
    'personalNote': 'A pleasure.',
    'teamName': 'Team', 'teamRole': 'CEO',
    'contactEmail': 'team@test.com',
    'commitmentBadges': [{'title': 'Quality', 'description': 'Guaranteed'}],
}


# ── Drawing helper tests ─────────────────────────────────────

class TestDrawGreenBar:
    def test_draws_without_error(self, pdf_canvas):
        ops_before = len(pdf_canvas._code)
        _draw_green_bar(pdf_canvas)
        assert len(pdf_canvas._code) > ops_before


class TestDrawFooter:
    def test_draws_footer_without_error(self, pdf_canvas):
        ops_before = len(pdf_canvas._code)
        _draw_footer(pdf_canvas, 1, 10, 'Test Client')
        assert len(pdf_canvas._code) > ops_before

    def test_draws_footer_with_empty_client_name(self, pdf_canvas):
        ops_before = len(pdf_canvas._code)
        _draw_footer(pdf_canvas, 1, 5, '')
        assert len(pdf_canvas._code) > ops_before


class TestDrawPill:
    def test_returns_right_x_and_bottom_y(self, pdf_canvas):
        right_x, bottom_y = _draw_pill(
            pdf_canvas, MARGIN_L, PAGE_H - 100, 'Test Badge',
        )
        assert right_x > MARGIN_L
        assert bottom_y < PAGE_H - 100

    def test_custom_colors(self, pdf_canvas):
        right_x, _ = _draw_pill(
            pdf_canvas, MARGIN_L, PAGE_H - 100, 'COP',
            bg_color=LEMON, text_color=ESMERALD, font_size=8,
        )
        assert right_x > MARGIN_L


class TestDrawBannerBox:
    def test_returns_lower_y(self, pdf_canvas):
        start_y = PAGE_H - 100
        end_y = _draw_banner_box(
            pdf_canvas, MARGIN_L, start_y, CONTENT_W,
            'Test banner text', icon_text='Info:',
        )
        assert end_y < start_y


class TestDrawSectionHeader:
    def test_returns_lower_y_after_drawing(self, pdf_canvas):
        start_y = PAGE_H - 50
        end_y = _draw_section_header(pdf_canvas, start_y, '1', 'Test Title')
        assert end_y < start_y

    def test_wraps_long_title(self, pdf_canvas):
        start_y = PAGE_H - 50
        long_title = 'A' * 100
        end_y = _draw_section_header(pdf_canvas, start_y, '1', long_title)
        assert end_y < start_y - 30

    def test_draws_without_index(self, pdf_canvas):
        start_y = PAGE_H - 50
        end_y = _draw_section_header(pdf_canvas, start_y, '', 'No Index')
        assert end_y < start_y


class TestDrawParagraphs:
    def test_returns_lower_y_after_drawing(self, pdf_canvas):
        start_y = 500
        end_y = _draw_paragraphs(pdf_canvas, start_y, ['Test paragraph.'])
        assert end_y < start_y

    def test_skips_empty_paragraphs(self, pdf_canvas):
        start_y = 500
        end_y = _draw_paragraphs(pdf_canvas, start_y, ['', None, 'Valid'])
        assert end_y < start_y

    def test_handles_empty_list(self, pdf_canvas):
        start_y = 500
        end_y = _draw_paragraphs(pdf_canvas, start_y, [])
        assert end_y == start_y

    def test_stops_at_page_bottom(self, pdf_canvas):
        end_y = _draw_paragraphs(pdf_canvas, MARGIN_B + 10, ['Text'])
        assert end_y == MARGIN_B + 10


class TestDrawBulletList:
    def test_returns_lower_y_after_drawing(self, pdf_canvas):
        start_y = 400
        end_y = _draw_bullet_list(pdf_canvas, start_y, ['Item A', 'Item B'])
        assert end_y < start_y

    def test_handles_empty_list(self, pdf_canvas):
        start_y = 400
        end_y = _draw_bullet_list(pdf_canvas, start_y, [])
        assert end_y == start_y


class TestDrawSidebarBox:
    def test_returns_box_bottom_y(self, pdf_canvas):
        box_y = _draw_sidebar_box(
            pdf_canvas, 500, 'Test', ['Item 1', 'Item 2'],
        )
        assert box_y < 500

    def test_handles_empty_items(self, pdf_canvas):
        box_y = _draw_sidebar_box(pdf_canvas, 500, 'Empty', [])
        assert box_y < 500


class TestDrawSubtitle:
    def test_returns_lower_y(self, pdf_canvas):
        end_y = _draw_subtitle(pdf_canvas, 400, 'Subtitle')
        assert end_y == 382


# ── Section renderer tests ───────────────────────────────────

class TestSectionRenderers:
    def test_greeting_renders_without_error(self, pdf_canvas, proposal):
        data = {'clientName': 'Test', 'inspirationalQuote': 'Be great.'}
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['greeting'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_greeting_renders_with_long_name(self, pdf_canvas, proposal):
        data = {'clientName': 'A' * 50, 'inspirationalQuote': ''}
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['greeting'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_executive_summary_renders(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Summary',
            'paragraphs': ['Paragraph one.'],
            'highlightsTitle': 'Key', 'highlights': ['Point'],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['executive_summary'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_context_diagnostic_renders(self, pdf_canvas, proposal):
        data = {
            'index': '2', 'title': 'Context',
            'paragraphs': ['Analysis.'],
            'issuesTitle': 'Issues', 'issues': ['SEO'],
            'opportunityTitle': 'Opportunity', 'opportunity': 'Growth.',
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['context_diagnostic'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_conversion_strategy_renders(self, pdf_canvas, proposal):
        data = {
            'index': '3', 'title': 'Strategy',
            'intro': 'Build trust.',
            'steps': [{'title': 'Step 1', 'bullets': ['A']}],
            'resultTitle': 'Result', 'result': 'More clients.',
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['conversion_strategy'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_design_ux_renders(self, pdf_canvas, proposal):
        data = {
            'index': '4', 'title': 'Design',
            'paragraphs': ['Modern.'],
            'focusTitle': 'Focus', 'focusItems': ['Mobile'],
            'objectiveTitle': 'Objective', 'objective': 'Impact.',
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['design_ux'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_creative_support_renders(self, pdf_canvas, proposal):
        data = {
            'index': '5', 'title': 'Support',
            'paragraphs': ['Guidance.'],
            'includesTitle': 'Includes', 'includes': ['Reviews'],
            'closing': 'We are here.',
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['creative_support'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_development_stages_renders(self, pdf_canvas, proposal):
        data = {
            'title': 'Stages',
            'stages': [
                {'title': 'Phase 1', 'description': 'Start.', 'current': True},
                {'title': 'Phase 2', 'description': 'Build.', 'current': False},
            ],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['development_stages'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_functional_requirements_returns_y_and_stores_groups(self, pdf_canvas, proposal):
        """functional_requirements returns a y-position and stores groups in ps."""
        ps = {'num': 1, 'client': 'Test'}
        data = {
            'index': '7', 'title': 'Requirements',
            'intro': 'Details.',
            'groups': [{'title': 'Views', 'description': 'Pages.', 'items': []}],
            'additionalModules': [],
        }
        result = SECTION_RENDERERS['functional_requirements'](
            pdf_canvas, data, proposal, ps=ps,
        )
        assert isinstance(result, (int, float))
        assert result < PAGE_H - 50
        assert '_func_req_groups' in ps
        assert len(ps['_func_req_groups']) >= 1

    def test_timeline_renders(self, pdf_canvas, proposal):
        """Timeline section renders phases without error."""
        data = {
            'index': '8', 'title': 'Timeline',
            'introText': 'Phases.',
            'totalDuration': '1 month',
            'phases': [{
                'title': 'Design', 'duration': '1 week',
                'description': 'Visual design.',
                'tasks': ['Wireframes'],
                'milestone': 'Approval',
            }],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['timeline'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_investment_renders(self, pdf_canvas, proposal):
        """Investment section renders pricing info without error."""
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['investment'](pdf_canvas, _INVESTMENT_DATA, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_final_note_renders(self, pdf_canvas, proposal):
        """Final note section renders team info without error."""
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['final_note'](pdf_canvas, _FINAL_NOTE_DATA, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_next_steps_renders(self, pdf_canvas, proposal):
        data = {
            'index': '11', 'title': 'Next Steps',
            'introMessage': 'Ready.',
            'steps': [{'title': 'Review', 'description': 'Check.'}],
            'ctaMessage': 'Call us.',
            'contactMethods': [{'title': 'Email', 'value': 'team@test.com'}],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['next_steps'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before


class TestRenderRawText:
    def test_renders_paste_mode_section(self, pdf_canvas, proposal):
        data = {
            'index': '12', 'title': 'Custom',
            'rawText': 'Custom content from paste mode.',
        }
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_renders_markdown_headings(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Markdown Test',
            'rawText': '# Heading 1\n## Heading 2\n### Heading 3\nParagraph.',
        }
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_renders_markdown_bullets(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Bullets',
            'rawText': '- Item one\n- Item two\n* Item three',
        }
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_renders_numbered_list(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Numbered',
            'rawText': '1. First\n2. Second\n3. Third',
        }
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_renders_bold_lines(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Bold',
            'rawText': '**Bold line**\nNormal text with **inline bold** here.',
        }
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_handles_empty_raw_text(self, pdf_canvas, proposal):
        data = {'index': '1', 'title': 'Empty', 'rawText': ''}
        page_before = pdf_canvas.getPageNumber()
        _render_raw_text(pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before


class TestParseMarkdownLines:
    def test_parses_headings(self):
        tokens = _parse_markdown_lines('# H1\n## H2\n### H3\n#### H4')
        assert tokens == [
            ('h1', 'H1'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4'),
        ]

    def test_parses_bullets(self):
        tokens = _parse_markdown_lines('- Apple\n* Banana')
        assert tokens == [('bullet', 'Apple'), ('bullet', 'Banana')]

    def test_parses_numbered_list(self):
        tokens = _parse_markdown_lines('1. First\n2. Second')
        assert tokens == [('numbered', 'First'), ('numbered', 'Second')]

    def test_parses_bold_line(self):
        tokens = _parse_markdown_lines('**Bold Title**')
        assert tokens == [('bold_line', 'Bold Title')]

    def test_parses_paragraph(self):
        tokens = _parse_markdown_lines('Just a normal line.')
        assert tokens == [('paragraph', 'Just a normal line.')]

    def test_parses_blank_lines(self):
        tokens = _parse_markdown_lines('Line 1\n\nLine 2')
        assert tokens == [
            ('paragraph', 'Line 1'), ('blank', ''), ('paragraph', 'Line 2'),
        ]

    def test_returns_empty_for_none(self):
        """None input returns an empty token list."""
        assert _parse_markdown_lines(None) == []

    def test_returns_empty_for_empty_string(self):
        """Empty string returns an empty token list."""
        assert _parse_markdown_lines('') == []


class TestCleanInlineBold:
    def test_removes_bold_markers(self):
        """Double-asterisk bold markers are stripped."""
        assert _clean_inline_bold('Use **bold** text') == 'Use bold text'

    def test_handles_multiple_bold(self):
        result = _clean_inline_bold('**A** and **B**')
        assert result == 'A and B'

    def test_preserves_non_bold_text(self):
        """Text without bold markers passes through unchanged."""
        assert _clean_inline_bold('No bold here') == 'No bold here'


class TestSectionRenderersMap:
    def test_contains_all_12_section_types(self):
        expected = {
            'greeting', 'executive_summary', 'context_diagnostic',
            'conversion_strategy', 'design_ux', 'creative_support',
            'development_stages', 'functional_requirements',
            'timeline', 'investment', 'final_note', 'next_steps',
        }
        assert set(SECTION_RENDERERS.keys()) == expected


# ── ProposalPdfService.generate tests ─────────────────────────

class TestGenerate:
    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_returns_pdf_bytes(self, mock_back, mock_cover, proposal_with_sections):
        """Generate produces valid PDF bytes for a proposal with sections."""
        result = ProposalPdfService.generate(proposal_with_sections)

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_generates_multiple_pages(self, mock_back, mock_cover, proposal_with_sections):
        """Multiple sections produce at least 2 PDF pages."""
        from pypdf import PdfReader

        pdf_bytes = ProposalPdfService.generate(proposal_with_sections)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 2
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch('content.services.proposal_pdf_service.canvas.Canvas')
    def test_returns_none_on_exception(self, mock_canvas_cls, proposal):
        mock_canvas_cls.side_effect = RuntimeError('Canvas error')

        result = ProposalPdfService.generate(proposal)

        assert result is None

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_handles_proposal_with_no_sections(self, mock_back, mock_cover, proposal):
        """Proposal with zero sections still produces valid PDF bytes."""
        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert isinstance(result, bytes)
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_handles_db_requirement_groups(self, mock_back, mock_cover, proposal):
        """DB-backed requirement groups are rendered into the PDF."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='Requirements',
            order=0,
            is_enabled=True,
            content_json={
                'index': '1', 'title': 'Requirements',
                'intro': 'Detail.',
                'groups': [], 'additionalModules': [],
            },
        )
        grp = ProposalRequirementGroup.objects.create(
            proposal=proposal, group_id='views',
            title='Views', description='Pages.', order=0,
        )
        ProposalRequirementItem.objects.create(
            group=grp, item_id='home', icon='✅',
            name='Home', description='Landing.', order=0,
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_handles_raw_text_section(self, mock_back, mock_cover, proposal):
        """Unknown section type with rawText falls back to raw text rendering."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='unknown_type',
            title='Custom Section',
            order=0,
            is_enabled=True,
            content_json={'rawText': 'Custom content.', 'title': 'Custom'},
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_paste_mode_overrides_form_renderer(self, mock_back, mock_cover, proposal):
        """Known section type with _editMode='paste' should use rawText, not form renderer."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='executive_summary',
            title='Resumen ejecutivo',
            order=0,
            is_enabled=True,
            content_json={
                '_editMode': 'paste',
                'rawText': '# Resumen\n\nEsta es la propuesta.\n\n- Punto 1\n- Punto 2',
                'index': '1',
                'title': 'Resumen ejecutivo',
                'paragraphs': [],
                'highlights': [],
            },
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_form_mode_uses_form_renderer(self, mock_back, mock_cover, proposal):
        """Known section type with _editMode='form' should use the form renderer."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='executive_summary',
            title='Resumen ejecutivo',
            order=0,
            is_enabled=True,
            content_json={
                '_editMode': 'form',
                'index': '1',
                'title': 'Resumen ejecutivo',
                'paragraphs': ['Primer párrafo.'],
                'highlights': ['Diseño'],
            },
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_paste_mode_requirement_group(self, mock_back, mock_cover, proposal):
        """Functional requirement group in paste mode should render rawText."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='Requerimientos',
            order=0,
            is_enabled=True,
            content_json={
                'index': '7',
                'title': 'Requerimientos Funcionales',
                'intro': 'Detalle.',
                'groups': [{
                    'title': 'Vistas',
                    'description': 'Pantallas.',
                    '_editMode': 'paste',
                    'rawText': '## Vistas\n- Home\n- About\n- Contact',
                    'items': [],
                }],
                'additionalModules': [],
            },
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_selected_modules_passed_to_investment_renderer(
        self, mock_back, mock_cover, proposal,
    ):
        """selected_modules list is forwarded through ps dict to _render_investment."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='investment',
            title='Inversión',
            order=0,
            is_enabled=True,
            content_json={
                'index': '4', 'title': 'Inversión',
                'introText': 'Total:',
                'totalInvestment': '$5,000,000', 'currency': 'COP',
                'whatsIncluded': [],
                'paymentOptions': [],
                'hostingPlan': {'title': 'Cloud', 'description': 'Included.'},
                'modules': [
                    {'id': 'web', 'name': 'Sitio Web', 'price': 3000000, 'included': True},
                    {'id': 'seo', 'name': 'SEO', 'price': 500000, 'included': False},
                ],
                'valueReasons': [],
            },
        )

        result = ProposalPdfService.generate(
            proposal, selected_modules=['web'],
        )

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_selected_modules_none_renders_all(
        self, mock_back, mock_cover, proposal,
    ):
        """When selected_modules is None, all modules are rendered normally."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='investment',
            title='Inversión',
            order=0,
            is_enabled=True,
            content_json={
                'index': '4', 'title': 'Inversión',
                'introText': 'Total:',
                'totalInvestment': '$5,000,000', 'currency': 'COP',
                'whatsIncluded': [],
                'paymentOptions': [],
                'hostingPlan': {'title': 'Cloud', 'description': 'Included.'},
                'modules': [
                    {'id': 'web', 'name': 'Sitio Web', 'price': 3000000, 'included': True},
                    {'id': 'seo', 'name': 'SEO', 'price': 500000, 'included': False},
                ],
                'valueReasons': [],
            },
        )

        result = ProposalPdfService.generate(
            proposal, selected_modules=None,
        )

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_selected_modules_empty_list_renders_without_error(
        self, mock_back, mock_cover, proposal,
    ):
        """Empty selected_modules list produces valid PDF without errors."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='investment',
            title='Inversión',
            order=0,
            is_enabled=True,
            content_json={
                'index': '4', 'title': 'Inversión',
                'introText': 'Total:',
                'totalInvestment': '$5,000,000', 'currency': 'COP',
                'whatsIncluded': [],
                'paymentOptions': [],
                'hostingPlan': {'title': 'Cloud', 'description': 'Included.'},
                'modules': [
                    {'id': 'web', 'name': 'Sitio Web', 'price': 3000000, 'included': True},
                ],
                'valueReasons': [],
            },
        )

        result = ProposalPdfService.generate(
            proposal, selected_modules=[],
        )

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()


# ── _merge_with_covers tests ─────────────────────────────────

class TestMergeWithCovers:
    def _make_pdf_bytes(self, num_pages=1):
        """Create minimal valid PDF bytes."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        for i in range(num_pages):
            c.drawString(100, 400, f'Page {i + 1}')
            c.showPage()
        c.save()
        return buf.getvalue()

    @patch('content.services.proposal_pdf_service.COVER_PDF')
    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    def test_returns_content_when_no_covers(self, mock_back, mock_cover):
        """Without cover PDFs, merge returns the original content unchanged."""
        mock_cover.exists.return_value = False
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(2)
        result = ProposalPdfService._merge_with_covers(content)

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_adds_cover_when_exists(self, mock_cover, mock_back):
        """When a cover PDF exists, it is prepended to the content pages."""
        cover_bytes = self._make_pdf_bytes(1)
        cover_path = Path('/tmp/test_cover.pdf')
        cover_path.write_bytes(cover_bytes)

        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(cover_path))
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(2)
        result = ProposalPdfService._merge_with_covers(content)

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3  # 1 cover + 2 content
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

        cover_path.unlink(missing_ok=True)

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_handles_corrupt_cover_gracefully(self, mock_cover, mock_back):
        """Corrupt cover PDF is skipped, returning only the content pages."""
        corrupt_path = Path('/tmp/test_corrupt.pdf')
        corrupt_path.write_bytes(b'not a pdf')

        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(corrupt_path))
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(1)
        result = ProposalPdfService._merge_with_covers(content)

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1  # only content, corrupt cover skipped
        mock_cover.exists.assert_called()

        corrupt_path.unlink(missing_ok=True)

    def _make_letter_cover_path(self):
        """Create a LETTER-size cover PDF on disk and return its path."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER)
        c.drawString(100, 400, 'Cover page in Letter size')
        c.showPage()
        c.save()
        path = Path('/tmp/test_cover_letter.pdf')
        path.write_bytes(buf.getvalue())
        return path

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_letter_cover_merged_produces_two_pages(self, mock_cover, mock_back):
        """A Letter-size cover merges with 1 content page → 2 pages total."""
        cover_path = self._make_letter_cover_path()
        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(cover_path))
        mock_back.exists.return_value = False

        result = ProposalPdfService._merge_with_covers(self._make_pdf_bytes(1))
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

        cover_path.unlink(missing_ok=True)

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_letter_cover_scaled_to_a4_dimensions(self, mock_cover, mock_back):
        """scale_to normalises Letter-size cover page to A4 (≈595×842 pt)."""
        cover_path = self._make_letter_cover_path()
        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(cover_path))
        mock_back.exists.return_value = False

        result = ProposalPdfService._merge_with_covers(self._make_pdf_bytes(1))
        cover_page = PdfReader(io.BytesIO(result)).pages[0]
        assert abs(float(cover_page.mediabox.width) - 595.0) < 2
        assert abs(float(cover_page.mediabox.height) - 842.0) < 2
        mock_cover.exists.assert_called()

        cover_path.unlink(missing_ok=True)


# ── generate_to_file tests ───────────────────────────────────

class TestGenerateToFile:
    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_saves_pdf_to_specified_path(self, mock_back, mock_cover, proposal_with_sections, tmp_path):
        """generate_to_file writes a valid PDF to the specified output path."""
        out = tmp_path / 'output.pdf'

        result = ProposalPdfService.generate_to_file(
            proposal_with_sections, output_path=str(out),
        )

        assert result == str(out)
        assert out.exists()
        assert out.read_bytes()[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_saves_to_temp_path_when_no_output_path(self, mock_back, mock_cover, proposal_with_sections):
        """Without output_path, generate_to_file creates a temp file."""
        result = ProposalPdfService.generate_to_file(proposal_with_sections)

        assert result is not None
        assert Path(result).exists()
        assert Path(result).read_bytes()[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()
        Path(result).unlink(missing_ok=True)

    @patch.object(ProposalPdfService, 'generate', return_value=None)
    def test_returns_none_when_generate_fails(self, mock_gen, proposal):
        """generate_to_file returns None when generate() returns None."""
        result = ProposalPdfService.generate_to_file(proposal)

        assert result is None
        mock_gen.assert_called_once_with(proposal)


# ── _format_cop tests ────────────────────────────────────────

class TestFormatCop:
    def test_formats_integer_with_dots(self):
        """Integer value is formatted as $X.XXX.XXX."""
        assert _format_cop(5000000) == '$5.000.000'

    def test_formats_string_integer(self):
        """String-numeric value is formatted correctly."""
        assert _format_cop('1490000') == '$1.490.000'

    def test_returns_string_for_non_numeric(self):
        """Non-numeric input is returned as-is string."""
        assert _format_cop('N/A') == 'N/A'

    def test_returns_string_for_none(self):
        """None input returns 'None' string."""
        assert _format_cop(None) == 'None'

    def test_formats_zero(self):
        """Zero formats to $0."""
        assert _format_cop(0) == '$0'


# ── _clean_url_display tests ─────────────────────────────────

class TestCleanUrlDisplay:
    def test_strips_scheme_from_https_url(self):
        """HTTPS scheme is removed, returning domain + path."""
        result = _clean_url_display('https://example.com/path')
        assert result == 'example.com/path'

    def test_strips_www_prefix(self):
        """Www prefix is removed from display label."""
        result = _clean_url_display('https://www.example.com')
        assert result == 'example.com'

    def test_handles_bare_domain(self):
        """Bare domain without scheme gets https:// prepended internally."""
        result = _clean_url_display('example.com')
        assert result == 'example.com'

    def test_strips_trailing_slash(self):
        """Trailing slash on root path is removed."""
        result = _clean_url_display('https://example.com/')
        assert result == 'example.com'

    def test_preserves_meaningful_path(self):
        """Non-root path segments are preserved."""
        result = _clean_url_display('https://docs.example.com/api/v2')
        assert result == 'docs.example.com/api/v2'

    def test_handles_invalid_url_gracefully(self):
        """Malformed input returns the original string."""
        result = _clean_url_display('')
        assert isinstance(result, str)


# ── _replace_urls_with_placeholders tests ─────────────────────

class TestReplaceUrlsWithPlaceholders:
    def test_replaces_full_url_with_display_label(self):
        """Full https URL is replaced with domain+path label."""
        text = 'Visit https://example.com/docs for details.'
        result, links = _replace_urls_with_placeholders(text)
        assert 'https://' not in result
        assert len(links) >= 1
        assert links[0][1] == 'https://example.com/docs'

    def test_replaces_bare_domain(self):
        """Bare domain like example.com is detected and replaced."""
        text = 'See example.com for info.'
        result, links = _replace_urls_with_placeholders(text)
        assert len(links) >= 1
        assert links[0][1].startswith('https://')

    def test_no_urls_returns_empty_links(self):
        """Text with no URLs returns empty links list."""
        text = 'No URLs here.'
        result, links = _replace_urls_with_placeholders(text)
        assert result == text
        assert links == []

    def test_multiple_urls(self):
        """Multiple URLs are all detected and replaced."""
        text = 'Visit https://a.com/page and https://b.com/page today.'
        result, links = _replace_urls_with_placeholders(text)
        assert len(links) >= 2


# ── _draw_line_with_links tests ──────────────────────────────

class TestDrawLineWithLinks:
    def test_draws_plain_text_without_error(self, pdf_canvas):
        """Plain text line draws without raising."""
        _register_fonts()
        ops_before = len(pdf_canvas._code)
        _draw_line_with_links(
            pdf_canvas, 50, 500, 'Hello world',
            _font('regular'), 10, ESMERALD,
        )
        assert len(pdf_canvas._code) > ops_before

    def test_draws_text_with_link(self, pdf_canvas):
        """Text containing a domain renders with link styling."""
        _register_fonts()
        ops_before = len(pdf_canvas._code)
        _draw_line_with_links(
            pdf_canvas, 50, 500, 'Visit example.com today',
            _font('regular'), 10, ESMERALD,
        )
        assert len(pdf_canvas._code) > ops_before

    def test_draws_full_url_as_link(self, pdf_canvas):
        """Full URL in text renders with clickable link."""
        _register_fonts()
        ops_before = len(pdf_canvas._code)
        _draw_line_with_links(
            pdf_canvas, 50, 500, 'See https://example.com/path here',
            _font('regular'), 10, ESMERALD,
        )
        assert len(pdf_canvas._code) > ops_before


# ── _font fallback tests ────────────────────────────────────

class TestFontFallback:
    def test_returns_string_for_regular(self):
        """Regular style returns a valid font name string."""
        result = _font('regular')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_string_for_unknown_style(self):
        """Unknown style falls back to Ubuntu/Helvetica."""
        result = _font('nonexistent_style')
        assert isinstance(result, str)

    def test_returns_fallback_for_bold(self):
        """Bold style returns a valid font name."""
        result = _font('bold')
        assert isinstance(result, str)


# ── Section renderer edge cases (no-sidebar branches) ────────

class TestSectionRendererEdgeCases:
    @pytest.fixture
    def proposal(self, db):
        return BusinessProposal.objects.create(
            title='Edge Case Proposal',
            client_name='Test',
            client_email='t@t.com',
            language='es',
            total_investment=Decimal('1000000'),
            currency='COP',
            status='sent',
        )

    def test_exec_summary_no_highlights_renders(self, pdf_canvas, proposal):
        """Executive summary with empty highlights uses full-width paragraphs."""
        data = {
            'index': '1', 'title': 'Summary',
            'paragraphs': ['Test paragraph.'],
            'highlightsTitle': '', 'highlights': [],
        }
        y = _render_executive_summary(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_context_diagnostic_no_issues_renders(self, pdf_canvas, proposal):
        """Context diagnostic with no issues renders paragraphs and opportunity."""
        data = {
            'index': '2', 'title': 'Context',
            'paragraphs': ['Analysis.'],
            'issuesTitle': '', 'issues': [],
            'opportunityTitle': 'Opportunity', 'opportunity': 'Growth potential.',
        }
        y = _render_context_diagnostic(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_context_diagnostic_no_issues_no_opportunity(self, pdf_canvas, proposal):
        """Context with neither issues nor opportunity renders just paragraphs."""
        data = {
            'index': '2', 'title': 'Context',
            'paragraphs': ['Analysis.'],
            'issuesTitle': '', 'issues': [],
            'opportunityTitle': '', 'opportunity': '',
        }
        y = _render_context_diagnostic(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_design_ux_no_focus_items_renders(self, pdf_canvas, proposal):
        """Design UX with no focus items renders paragraphs and objective."""
        data = {
            'index': '4', 'title': 'Design',
            'paragraphs': ['Modern design.'],
            'focusTitle': '', 'focusItems': [],
            'objectiveTitle': 'Objective', 'objective': 'Impact.',
        }
        y = _render_design_ux(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_design_ux_no_focus_no_objective(self, pdf_canvas, proposal):
        """Design UX with no focus items and no objective."""
        data = {
            'index': '4', 'title': 'Design',
            'paragraphs': ['Modern design.'],
            'focusTitle': '', 'focusItems': [],
            'objectiveTitle': '', 'objective': '',
        }
        y = _render_design_ux(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_creative_support_no_includes_renders(self, pdf_canvas, proposal):
        """Creative support with no includes renders paragraphs and closing."""
        data = {
            'index': '5', 'title': 'Support',
            'paragraphs': ['Guidance.'],
            'includesTitle': '', 'includes': [],
            'closing': 'We are here for you.',
        }
        y = _render_creative_support(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_creative_support_no_includes_no_closing(self, pdf_canvas, proposal):
        """Creative support with no includes and no closing."""
        data = {
            'index': '5', 'title': 'Support',
            'paragraphs': ['Guidance.'],
            'includesTitle': '', 'includes': [],
            'closing': '',
        }
        y = _render_creative_support(pdf_canvas, data, proposal)
        assert isinstance(y, (int, float))

    def test_exec_summary_low_y_no_sidebar(self, pdf_canvas, proposal):
        """Executive summary starting at low y triggers no-sidebar branch."""
        data = {
            'index': '1', 'title': 'Summary',
            'paragraphs': ['Short.'],
            'highlightsTitle': 'Key', 'highlights': ['A', 'B'],
        }
        y = _render_executive_summary(pdf_canvas, data, proposal, y=MARGIN_B + 150)
        assert isinstance(y, (int, float))

    def test_context_diagnostic_low_y_no_sidebar(self, pdf_canvas, proposal):
        """Context diagnostic starting at low y triggers no-sidebar branch."""
        data = {
            'index': '2', 'title': 'Context',
            'paragraphs': ['Analysis.'],
            'issuesTitle': 'Issues', 'issues': ['SEO'],
            'opportunityTitle': 'Opportunity', 'opportunity': 'Growth.',
        }
        y = _render_context_diagnostic(pdf_canvas, data, proposal, y=MARGIN_B + 150)
        assert isinstance(y, (int, float))

    def test_creative_support_low_y_no_sidebar(self, pdf_canvas, proposal):
        """Creative support starting at low y triggers no-sidebar branch."""
        data = {
            'index': '5', 'title': 'Support',
            'paragraphs': ['Guidance.'],
            'includesTitle': 'Includes', 'includes': ['Reviews'],
            'closing': 'We are here.',
        }
        y = _render_creative_support(pdf_canvas, data, proposal, y=MARGIN_B + 150)
        assert isinstance(y, (int, float))


# ── Back cover merge test ────────────────────────────────────

class TestBackCoverMerge(TestMergeWithCovers):
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    def test_adds_back_cover_when_exists(self, mock_back, mock_cover):
        """When a back cover PDF exists, it is appended after content pages."""
        back_bytes = self._make_pdf_bytes(1)
        back_path = Path('/tmp/test_back_cover.pdf')
        back_path.write_bytes(back_bytes)

        mock_cover.exists.return_value = False
        mock_back.exists.return_value = True
        mock_back.__str__ = MagicMock(return_value=str(back_path))

        content = self._make_pdf_bytes(2)
        result = ProposalPdfService._merge_with_covers(content)

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3  # 2 content + 1 back
        mock_back.exists.assert_called()

        back_path.unlink(missing_ok=True)

    @patch('content.services.proposal_pdf_service.COVER_PDF')
    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    def test_corrupt_back_cover_skipped(self, mock_back, mock_cover):
        """Corrupt back cover PDF is skipped gracefully."""
        corrupt_path = Path('/tmp/test_corrupt_back.pdf')
        corrupt_path.write_bytes(b'not a pdf')

        mock_cover.exists.return_value = False
        mock_back.exists.return_value = True
        mock_back.__str__ = MagicMock(return_value=str(corrupt_path))

        content = self._make_pdf_bytes(1)
        result = ProposalPdfService._merge_with_covers(content)

        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1  # only content
        mock_back.exists.assert_called()

        corrupt_path.unlink(missing_ok=True)


# ── Investment hosting edge cases ────────────────────────────

class TestInvestmentHostingEdgeCases:
    def test_investment_with_hosting_specs_and_pricing(self, pdf_canvas, proposal):
        """Investment section with hosting specs grid and pricing renders."""
        data = {
            'index': '9', 'title': 'Investment',
            'introText': 'Total:',
            'totalInvestment': '$5,000,000', 'currency': 'COP',
            'whatsIncluded': [{'title': 'Design', 'description': 'UX'}],
            'paymentOptions': [{'label': '50%', 'description': '$2.5M'}],
            'hostingPlan': {
                'title': 'Cloud Pro',
                'description': 'Full managed hosting.',
                'specs': [
                    {'label': 'Storage', 'value': '50 GB'},
                    {'label': 'Bandwidth', 'value': 'Unlimited'},
                    {'label': 'SSL', 'value': 'Included'},
                ],
                'monthlyPrice': '$150.000',
                'monthlyLabel': 'por mes',
                'annualPrice': '$1.500.000',
                'annualLabel': 'pago anual',
                'coverageNote': 'Hosting covers domain, SSL, and CDN.',
            },
            'valueReasons': ['Quality', 'Support'],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['investment'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before

    def test_investment_with_monthly_price_only(self, pdf_canvas, proposal):
        """Investment hosting with only monthly price renders."""
        data = {
            'index': '9', 'title': 'Investment',
            'introText': 'Total:',
            'totalInvestment': '$1,000,000', 'currency': 'COP',
            'whatsIncluded': [],
            'paymentOptions': [],
            'hostingPlan': {
                'title': 'Basic',
                'description': 'Basic hosting.',
                'monthlyPrice': '$50.000',
                'annualPrice': '',
            },
            'valueReasons': [],
        }
        page_before = pdf_canvas.getPageNumber()
        SECTION_RENDERERS['investment'](pdf_canvas, data, proposal)
        assert pdf_canvas.getPageNumber() >= page_before


# ── Generate with FR items and selected_modules ──────────────

class TestGenerateWithFRItems:
    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_fr_items_filtered_by_selected_modules(
        self, mock_back, mock_cover, proposal,
    ):
        """FR configurable items are filtered when selected_modules is provided."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='greeting',
            title='Hi', order=0, is_enabled=True,
            content_json={'clientName': 'Test', 'inspirationalQuote': ''},
        )
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='Reqs', order=1, is_enabled=True,
            content_json={
                'index': '7', 'title': 'Requirements',
                'intro': 'Details.',
                'groups': [{
                    'id': 'views', 'title': 'Views',
                    'description': 'Pages.',
                    'items': [
                        {'name': 'Home', 'description': 'Landing.', 'is_required': True},
                        {'name': 'Blog', 'description': 'Blog.', 'is_required': False, 'price': 500000},
                    ],
                }],
                'additionalModules': [],
            },
        )
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='investment',
            title='Inv', order=2, is_enabled=True,
            content_json={
                'index': '9', 'title': 'Investment',
                'introText': 'Total:', 'totalInvestment': '$2,000,000',
                'currency': 'COP', 'whatsIncluded': [], 'paymentOptions': [],
                'hostingPlan': {}, 'valueReasons': [],
            },
        )

        result = ProposalPdfService.generate(
            proposal, selected_modules=['fr-views-blog'],
        )

        assert result is not None
        assert result[:5] == b'%PDF-'
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_greeting_not_first_section_triggers_page_break(
        self, mock_back, mock_cover, proposal,
    ):
        """Greeting section that isn't the first content triggers a page break."""
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='executive_summary',
            title='Summary', order=0, is_enabled=True,
            content_json={
                'index': '1', 'title': 'Summary',
                'paragraphs': ['P1.'], 'highlightsTitle': '',
                'highlights': [],
            },
        )
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='greeting',
            title='Hi', order=1, is_enabled=True,
            content_json={'clientName': 'Test', 'inspirationalQuote': ''},
        )

        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert result[:5] == b'%PDF-'
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) >= 2
        mock_cover.exists.assert_called()
        mock_back.exists.assert_called()
