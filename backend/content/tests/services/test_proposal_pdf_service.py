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
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.models import (
    BusinessProposal,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
)
from content.services.proposal_pdf_service import (
    CONTENT_W,
    MARGIN_B,
    MARGIN_L,
    PAGE_H,
    PAGE_W,
    SECTION_RENDERERS,
    SIDEBAR_W,
    SIDEBAR_X,
    TEXT_AREA_W,
    ProposalPdfService,
    _draw_bullet_list,
    _draw_footer,
    _draw_green_bar,
    _draw_header_bar,
    _draw_paragraphs,
    _draw_section_header,
    _draw_sidebar_box,
    _draw_subtitle,
    _register_fonts,
    _render_raw_text,
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
        assert _strip_emoji('Hello 🎨 World') == 'Hello  World'

    def test_removes_multiple_emojis(self):
        result = _strip_emoji('✅ Done 🚀 Launch 🎯 Target')
        assert '✅' not in result
        assert '🚀' not in result
        assert '🎯' not in result

    def test_preserves_plain_latin_text(self):
        assert _strip_emoji('Hello World') == 'Hello World'

    def test_preserves_accented_characters(self):
        assert _strip_emoji('Diseño gráfico') == 'Diseño gráfico'

    def test_returns_empty_for_none(self):
        assert _strip_emoji(None) is None

    def test_returns_empty_for_empty_string(self):
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
        assert _safe({'name': 'Alice'}, 'name') == 'Alice'

    def test_returns_default_for_missing_key(self):
        assert _safe({}, 'name', 'Unknown') == 'Unknown'

    def test_returns_default_for_none_value(self):
        assert _safe({'name': None}, 'name', 'Default') == 'Default'

    def test_returns_default_for_empty_string_value(self):
        assert _safe({'name': ''}, 'name', 'Default') == 'Default'

    def test_returns_empty_string_default(self):
        assert _safe({}, 'name') == ''

    def test_returns_default_for_non_dict(self):
        assert _safe('not_a_dict', 'key', 'fallback') == 'fallback'

    def test_returns_list_default(self):
        assert _safe({}, 'items', []) == []

    def test_returns_existing_list(self):
        assert _safe({'items': [1, 2]}, 'items', []) == [1, 2]


# ── Drawing helper tests ─────────────────────────────────────

class TestDrawGreenBar:
    def test_draws_without_error(self, pdf_canvas):
        _draw_green_bar(pdf_canvas)


class TestDrawFooter:
    def test_draws_footer_without_error(self, pdf_canvas):
        _draw_footer(pdf_canvas, 1, 10, 'Test Client')

    def test_draws_footer_with_empty_client_name(self, pdf_canvas):
        _draw_footer(pdf_canvas, 1, 5, '')


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
        SECTION_RENDERERS['greeting'](pdf_canvas, data, proposal)

    def test_greeting_renders_with_long_name(self, pdf_canvas, proposal):
        data = {'clientName': 'A' * 50, 'inspirationalQuote': ''}
        SECTION_RENDERERS['greeting'](pdf_canvas, data, proposal)

    def test_executive_summary_renders(self, pdf_canvas, proposal):
        data = {
            'index': '1', 'title': 'Summary',
            'paragraphs': ['Paragraph one.'],
            'highlightsTitle': 'Key', 'highlights': ['Point'],
        }
        SECTION_RENDERERS['executive_summary'](pdf_canvas, data, proposal)

    def test_context_diagnostic_renders(self, pdf_canvas, proposal):
        data = {
            'index': '2', 'title': 'Context',
            'paragraphs': ['Analysis.'],
            'issuesTitle': 'Issues', 'issues': ['SEO'],
            'opportunityTitle': 'Opportunity', 'opportunity': 'Growth.',
        }
        SECTION_RENDERERS['context_diagnostic'](pdf_canvas, data, proposal)

    def test_conversion_strategy_renders(self, pdf_canvas, proposal):
        data = {
            'index': '3', 'title': 'Strategy',
            'intro': 'Build trust.',
            'steps': [{'title': 'Step 1', 'bullets': ['A']}],
            'resultTitle': 'Result', 'result': 'More clients.',
        }
        SECTION_RENDERERS['conversion_strategy'](pdf_canvas, data, proposal)

    def test_design_ux_renders(self, pdf_canvas, proposal):
        data = {
            'index': '4', 'title': 'Design',
            'paragraphs': ['Modern.'],
            'focusTitle': 'Focus', 'focusItems': ['Mobile'],
            'objectiveTitle': 'Objective', 'objective': 'Impact.',
        }
        SECTION_RENDERERS['design_ux'](pdf_canvas, data, proposal)

    def test_creative_support_renders(self, pdf_canvas, proposal):
        data = {
            'index': '5', 'title': 'Support',
            'paragraphs': ['Guidance.'],
            'includesTitle': 'Includes', 'includes': ['Reviews'],
            'closing': 'We are here.',
        }
        SECTION_RENDERERS['creative_support'](pdf_canvas, data, proposal)

    def test_development_stages_renders(self, pdf_canvas, proposal):
        data = {
            'title': 'Stages',
            'stages': [
                {'title': 'Phase 1', 'description': 'Start.', 'current': True},
                {'title': 'Phase 2', 'description': 'Build.', 'current': False},
            ],
        }
        SECTION_RENDERERS['development_stages'](pdf_canvas, data, proposal)

    def test_functional_requirements_returns_groups(self, pdf_canvas, proposal):
        data = {
            'index': '7', 'title': 'Requirements',
            'intro': 'Details.',
            'groups': [{'title': 'Views', 'description': 'Pages.', 'items': []}],
            'additionalModules': [],
        }
        result = SECTION_RENDERERS['functional_requirements'](
            pdf_canvas, data, proposal,
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_timeline_renders(self, pdf_canvas, proposal):
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
        SECTION_RENDERERS['timeline'](pdf_canvas, data, proposal)

    def test_investment_renders(self, pdf_canvas, proposal):
        data = {
            'index': '9', 'title': 'Investment',
            'introText': 'Total:',
            'totalInvestment': '$5,000,000', 'currency': 'COP',
            'whatsIncluded': [{'title': 'Design', 'description': 'UX'}],
            'paymentOptions': [{'label': '50%', 'description': '$2.5M'}],
            'hostingPlan': {'title': 'Cloud', 'description': 'Included.'},
            'valueReasons': ['Quality'],
        }
        SECTION_RENDERERS['investment'](pdf_canvas, data, proposal)

    def test_final_note_renders(self, pdf_canvas, proposal):
        data = {
            'index': '10', 'title': 'Final Note',
            'message': 'Thank you.',
            'personalNote': 'A pleasure.',
            'teamName': 'Team', 'teamRole': 'CEO',
            'contactEmail': 'team@test.com',
            'commitmentBadges': [{'title': 'Quality', 'description': 'Guaranteed'}],
        }
        SECTION_RENDERERS['final_note'](pdf_canvas, data, proposal)

    def test_next_steps_renders(self, pdf_canvas, proposal):
        data = {
            'index': '11', 'title': 'Next Steps',
            'introMessage': 'Ready.',
            'steps': [{'title': 'Review', 'description': 'Check.'}],
            'ctaMessage': 'Call us.',
            'contactMethods': [{'title': 'Email', 'value': 'team@test.com'}],
        }
        SECTION_RENDERERS['next_steps'](pdf_canvas, data, proposal)


class TestRenderRawText:
    def test_renders_paste_mode_section(self, pdf_canvas, proposal):
        data = {
            'index': '12', 'title': 'Custom',
            'rawText': 'Custom content from paste mode.',
        }
        _render_raw_text(pdf_canvas, data, proposal)


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
    def test_returns_pdf_bytes(self, _mock_back, _mock_cover, proposal_with_sections):
        result = ProposalPdfService.generate(proposal_with_sections)

        assert result is not None
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_generates_correct_page_count(self, _mock_back, _mock_cover, proposal_with_sections):
        from pypdf import PdfReader

        pdf_bytes = ProposalPdfService.generate(proposal_with_sections)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        # 12 sections + 1 functional requirements group detail page = 13
        assert len(reader.pages) == 13

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
    def test_handles_proposal_with_no_sections(self, _mock_back, _mock_cover, proposal):
        result = ProposalPdfService.generate(proposal)

        assert result is not None
        assert isinstance(result, bytes)

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_handles_db_requirement_groups(self, _mock_back, _mock_cover, proposal):
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

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_handles_raw_text_section(self, _mock_back, _mock_cover, proposal):
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
        mock_cover.exists.return_value = False
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(2)
        result = ProposalPdfService._merge_with_covers(content)

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_adds_cover_when_exists(self, mock_cover, mock_back):
        cover_bytes = self._make_pdf_bytes(1)
        cover_path = Path('/tmp/test_cover.pdf')
        cover_path.write_bytes(cover_bytes)

        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(cover_path))
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(2)
        result = ProposalPdfService._merge_with_covers(content)

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3  # 1 cover + 2 content

        cover_path.unlink(missing_ok=True)

    @patch('content.services.proposal_pdf_service.BACK_COVER_PDF')
    @patch('content.services.proposal_pdf_service.COVER_PDF')
    def test_handles_corrupt_cover_gracefully(self, mock_cover, mock_back):
        corrupt_path = Path('/tmp/test_corrupt.pdf')
        corrupt_path.write_bytes(b'not a pdf')

        mock_cover.exists.return_value = True
        mock_cover.__str__ = MagicMock(return_value=str(corrupt_path))
        mock_back.exists.return_value = False

        content = self._make_pdf_bytes(1)
        result = ProposalPdfService._merge_with_covers(content)

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1  # only content, corrupt cover skipped

        corrupt_path.unlink(missing_ok=True)


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
    def test_saves_pdf_to_specified_path(self, _m1, _m2, proposal_with_sections, tmp_path):
        out = tmp_path / 'output.pdf'

        result = ProposalPdfService.generate_to_file(
            proposal_with_sections, output_path=str(out),
        )

        assert result == str(out)
        assert out.exists()
        assert out.read_bytes()[:5] == b'%PDF-'

    @patch(
        'content.services.proposal_pdf_service.COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    @patch(
        'content.services.proposal_pdf_service.BACK_COVER_PDF',
        new_callable=lambda: MagicMock(exists=MagicMock(return_value=False)),
    )
    def test_saves_to_temp_path_when_no_output_path(self, _m1, _m2, proposal_with_sections):
        result = ProposalPdfService.generate_to_file(proposal_with_sections)

        assert result is not None
        assert Path(result).exists()
        assert Path(result).read_bytes()[:5] == b'%PDF-'
        Path(result).unlink(missing_ok=True)

    @patch.object(ProposalPdfService, 'generate', return_value=None)
    def test_returns_none_when_generate_fails(self, _mock_gen, proposal):
        result = ProposalPdfService.generate_to_file(proposal)

        assert result is None
