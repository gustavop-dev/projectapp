"""Gap tests for proposal_pdf_service — targets uncovered branches.

Covers:
- default_selected_modules_from_content: non-dict group (line 161) and missing gid (line 174)
- _render_investment: forced linear layout with payment option desc recalculation
- _render_value_added_modules: y=None default (line 1460) and missing catalog entry (line 1494)
- generate(): section content_json without 'title' key (line 2021)
"""
import io
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.models import BusinessProposal
from content.models.proposal_section import ProposalSection
from content.services.proposal_pdf_service import (
    MARGIN_B,
    PAGE_H,
    MARGIN_T,
    _register_fonts,
    _render_creative_support,
    _render_investment,
    _render_value_added_modules,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pdf_canvas():
    _register_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c


@pytest.fixture
def proposal(db):
    return BusinessProposal.objects.create(
        title='Gaps3 Proposal',
        client_name='Gaps Client',
        client_email='gaps3@example.com',
        language='es',
        total_investment=Decimal('5000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=14),
    )


# ---------------------------------------------------------------------------
# default_selected_modules_from_content — non-dict group skipped (line 161)
# ---------------------------------------------------------------------------

class TestDefaultSelectedModulesNonDictGroup:
    def test_non_dict_entry_in_groups_is_skipped(self, proposal):
        from content.services.proposal_pdf_service import (
            default_selected_modules_from_content,
        )

        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='FR',
            order=0,
            is_enabled=True,
            content_json={
                'groups': [
                    'not-a-dict',
                    None,
                    {'id': 'grp1', 'title': 'Valid Group'},
                ],
            },
        )

        result = default_selected_modules_from_content(proposal, has_confirmed=False)

        assert isinstance(result, list)
        assert 'group-grp1' in result


# ---------------------------------------------------------------------------
# default_selected_modules_from_content — group without id skipped (line 174)
# ---------------------------------------------------------------------------

class TestDefaultSelectedModulesMissingGid:
    def test_group_without_id_is_not_added_to_selected(self, proposal):
        from content.services.proposal_pdf_service import (
            default_selected_modules_from_content,
        )

        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='FR',
            order=0,
            is_enabled=True,
            content_json={
                'groups': [
                    {'title': 'No ID Group', 'selected': True},
                ],
            },
        )

        result = default_selected_modules_from_content(proposal, has_confirmed=False)

        assert result == []


# ---------------------------------------------------------------------------
# _render_value_added_modules — y=None default (line 1460)
# ---------------------------------------------------------------------------

class TestRenderValueAddedModulesYNone:
    def test_y_none_defaults_to_page_top(self, pdf_canvas):
        data = {'index': '05', 'title': 'Incluido', 'module_ids': []}
        ps = {'_value_added_catalog': {}, 'num': 1, 'client': 'Test'}

        result = _render_value_added_modules(pdf_canvas, data, None, ps=ps, y=None)

        assert isinstance(result, (int, float))


# ---------------------------------------------------------------------------
# _render_value_added_modules — module not in catalog skipped (line 1494)
# ---------------------------------------------------------------------------

class TestRenderValueAddedModulesMissingCatalogEntry:
    def test_module_id_not_in_catalog_is_skipped_without_error(self, pdf_canvas):
        data = {
            'index': '05',
            'title': 'Incluido',
            'module_ids': ['missing-id-1', 'missing-id-2'],
        }
        ps = {'_value_added_catalog': {}, 'num': 1, 'client': 'Test'}

        result = _render_value_added_modules(
            pdf_canvas, data, None, ps=ps, y=PAGE_H - MARGIN_T,
        )

        assert isinstance(result, (int, float))


# ---------------------------------------------------------------------------
# _render_investment — forced linear layout with ps (lines 1042, 1050, 1082)
# ---------------------------------------------------------------------------

class TestRenderInvestmentLinearLayout:
    def test_linear_layout_with_ps_and_options_renders_without_error(
        self, pdf_canvas, proposal,
    ):
        ps = {
            'num': 1,
            'client': 'Test',
            'selected_modules': None,
            '_fr_items': [],
            '_calc_module_items': [],
            'base_weeks': 0,
        }
        data = {
            'index': '4',
            'title': 'Inversión',
            'totalInvestment': '$5.000.000',
            'currency': 'COP',
            'paymentOptions': [
                {'label': '50% Inicio', 'description': '$2.500.000'},
                {'label': '50% Final', 'description': '$2.500.000'},
            ],
            'whatsIncluded': [
                {'title': 'Diseño', 'description': 'UI/UX completo'},
            ],
            'modules': [],
        }

        # Force linear layout by using small y
        small_y = MARGIN_B + 60

        result = _render_investment(pdf_canvas, data, proposal, ps=ps, y=small_y)

        assert isinstance(result, (int, float))

    def test_linear_layout_with_adjusted_total_recalculates_option_desc(
        self, pdf_canvas, proposal,
    ):
        ps = {
            'num': 1,
            'client': 'Test',
            'selected_modules': ['module-web'],
            '_fr_items': [],
            '_calc_module_items': [],
            'base_weeks': 0,
        }
        data = {
            'index': '4',
            'title': 'Inversión',
            'totalInvestment': '$5.000.000',
            'currency': 'COP',
            'paymentOptions': [
                {'label': '50% Inicio', 'description': '$2500000'},
            ],
            'whatsIncluded': [
                {'title': 'Soporte', 'description': 'Incluido'},
            ],
            'modules': [
                {'id': 'web', 'name': 'Web', 'price': 5000000},
            ],
        }

        small_y = MARGIN_B + 60

        result = _render_investment(pdf_canvas, data, proposal, ps=ps, y=small_y)

        assert isinstance(result, (int, float))


# ---------------------------------------------------------------------------
# generate() — section content_json without 'title' key (line 2021)
# ---------------------------------------------------------------------------

class TestGenerateSectionWithoutTitleInContentJson:
    def test_section_without_title_in_content_json_falls_back_to_section_title(
        self, proposal,
    ):
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='executive_summary',
            title='Resumen Ejecutivo',
            order=1,
            is_enabled=True,
            content_json={'index': '01', 'paragraphs': ['Texto de resumen.']},
        )

        from content.services.proposal_pdf_service import ProposalPdfService

        with patch(
            'content.services.proposal_pdf_service.ProposalPdfService._merge_with_covers',
            side_effect=lambda b, **kw: b,
        ):
            result = ProposalPdfService.generate(proposal)

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'


# ---------------------------------------------------------------------------
# _render_creative_support — Tier 2 partial two-column layout (lines 456-462)
# ---------------------------------------------------------------------------

class TestRenderCreativeSupportTier2:
    def test_tier2_partial_two_column_renders_paragraphs_then_closing_below(
        self, pdf_canvas,
    ):
        # 7 short paragraphs give para_h ≈ 140, closing_h ≈ 20 (full_left_h ≈ 160).
        # 1 include item gives sb_h ≈ 51.
        # partial_need = max(51, 140) + 20 = 160; full_need = max(51, 160) + 20 = 180.
        # With y_start=280: content_top ≈ 224, avail ≈ 176 — lands in (160, 180].
        data = {
            'index': None,
            'title': 'Soporte',
            'paragraphs': ['Línea de texto.'] * 7,
            'closing': 'Mensaje de cierre.',
            'includes': ['Elemento incluido'],
            'includesTitle': 'Incluye',
        }

        result = _render_creative_support(pdf_canvas, data, None, ps=None, y=280)

        assert isinstance(result, (int, float))
