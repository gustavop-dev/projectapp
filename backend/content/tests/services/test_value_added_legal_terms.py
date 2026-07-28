"""Legal terms of the value-added modules: clause shape, parity and rendering.

The terms of the free modules are categorised clauses (`terms_clauses`) plus a
section-level `general_terms` block. The public web modal and the PDF annex read
that very same source, so these tests pin the shape, the ES/EN parity and the
fact that both surfaces receive the same clauses.
"""
import io
from decimal import Decimal

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services import proposal_pdf_service as pdf_mod
from content.services.proposal_pdf_service import (
    _clause_bullets,
    _render_value_added_modules,
)
from content.services.proposal_service import (
    DEFAULT_SECTIONS,
    DEFAULT_SECTIONS_EN,
    flatten_terms_clauses,
    merge_value_added_legal_terms,
)
from content.services.pdf_utils import MARGIN_T, PAGE_H

MODULE_IDS = [
    'kpi_dashboard_module',
    'analytics_dashboard',
    'admin_module',
    'manual_module',
    'ai_automation_module',
]


@pytest.fixture
def pdf_canvas():
    """A ReportLab canvas backed by an in-memory buffer."""
    pdf_mod._register_fonts()
    return canvas.Canvas(io.BytesIO(), pagesize=A4)


def _defaults(lang):
    return DEFAULT_SECTIONS_EN if lang == 'en' else DEFAULT_SECTIONS


def _value_added_cj(lang):
    section = next(
        s for s in _defaults(lang)
        if s['section_type'] == 'value_added_modules'
    )
    return section['content_json']


def _conditions(lang, module_id):
    return _value_added_cj(lang)['conditions'][module_id]


def _commercial_cj(lang):
    section = next(
        s for s in _defaults(lang)
        if s['section_type'] == 'commercial_conditions'
    )
    return section['content_json']


# ---------------------------------------------------------------------------
# Clause shape
# ---------------------------------------------------------------------------

class TestClauseShape:
    @pytest.mark.parametrize('lang', ['es', 'en'])
    @pytest.mark.parametrize('module_id', MODULE_IDS)
    def test_every_module_carries_labelled_clauses(self, lang, module_id):
        clauses = _conditions(lang, module_id)['terms_clauses']
        # A real legal block, not a single repurposed sentence.
        assert len(clauses) >= 3, f'{lang}/{module_id} has {len(clauses)} clauses'
        for clause in clauses:
            assert clause['label'].strip(), f'{lang}/{module_id} clause without label'
            assert clause['text'].strip(), f'{lang}/{module_id} clause without text'

    @pytest.mark.parametrize('lang', ['es', 'en'])
    @pytest.mark.parametrize('module_id', MODULE_IDS)
    def test_terms_string_is_derived_from_clauses(self, lang, module_id):
        cond = _conditions(lang, module_id)
        assert cond['terms'] == flatten_terms_clauses(cond['terms_clauses'])

    @pytest.mark.parametrize('module_id', MODULE_IDS)
    def test_es_and_en_declare_the_same_clause_count(self, module_id):
        assert (len(_conditions('es', module_id)['terms_clauses'])
                == len(_conditions('en', module_id)['terms_clauses']))

    @pytest.mark.parametrize('lang', ['es', 'en'])
    def test_general_terms_block_present(self, lang):
        general = _value_added_cj(lang)['general_terms']
        assert general['title'].strip()
        assert len(general['clauses']) >= 8
        for clause in general['clauses']:
            assert clause['label'].strip()
            assert clause['text'].strip()

    def test_general_terms_parity_between_languages(self):
        assert (len(_value_added_cj('es')['general_terms']['clauses'])
                == len(_value_added_cj('en')['general_terms']['clauses']))


# ---------------------------------------------------------------------------
# Legal content the operator explicitly asked for
# ---------------------------------------------------------------------------

class TestLegalContent:
    def test_ai_term_counts_from_production_deployment(self):
        clauses = _conditions('es', 'ai_automation_module')['terms_clauses']
        vigencia = next(c for c in clauses if c['label'] == 'Vigencia')
        assert '6 meses' in vigencia['text']
        assert 'despliegue del proyecto en producción' in vigencia['text']
        # It must rule out the readings it is meant to displace.
        assert 'no' in vigencia['text'].lower()
        assert 'aceptación de esta propuesta' in vigencia['text']

    def test_ai_term_counts_from_production_deployment_en(self):
        clauses = _conditions('en', 'ai_automation_module')['terms_clauses']
        term = next(c for c in clauses if c['label'] == 'Term')
        assert '6 months' in term['text']
        assert 'deployed to production' in term['text']

    def test_ai_third_party_dependency_and_liability_are_separate_clauses(self):
        labels = [c['label'] for c in _conditions('es', 'ai_automation_module')['terms_clauses']]
        assert 'Dependencia de proveedores externos' in labels
        assert 'Exclusión de responsabilidad' in labels

    def test_ai_liability_clause_disclaims_provider_discontinuation(self):
        clauses = _conditions('es', 'ai_automation_module')['terms_clauses']
        liability = next(c for c in clauses
                         if c['label'] == 'Exclusión de responsabilidad')
        assert 'no constituye incumplimiento' in liability['text']
        assert 'discontinúa' in liability['text']

    @pytest.mark.parametrize('module_id', [
        'kpi_dashboard_module', 'analytics_dashboard', 'ai_automation_module',
    ])
    def test_data_dependent_modules_require_data_to_exist(self, module_id):
        """No data to process → not deliverable, even if the price qualifies."""
        clauses = _conditions('es', module_id)['terms_clauses']
        data_clause = next(
            c for c in clauses
            if c['label'] == 'Requisito de disponibilidad de datos'
        )
        assert 'aun cuando el valor del proyecto habilite el beneficio' in data_clause['text']

    def test_general_terms_cover_the_expected_legal_grounds(self):
        labels = [c['label'] for c in _value_added_cj('es')['general_terms']['clauses']]
        for expected in [
            'Condición de viabilidad y pertinencia técnica',
            'Disponibilidad y suficiencia de datos',
            'Dependencia de proveedores y servicios de terceros',
            'Tratamiento de datos personales',
            'Fuerza mayor y caso fortuito',
            'Intransferibilidad y no canje',
            'Prevalencia del contrato y vigencia',
        ]:
            assert expected in labels

    def test_personal_data_clause_cites_colombian_law(self):
        clauses = _value_added_cj('es')['general_terms']['clauses']
        data_clause = next(c for c in clauses
                           if c['label'] == 'Tratamiento de datos personales')
        assert 'Ley 1581 de 2012' in data_clause['text']

    @pytest.mark.parametrize('lang,fragment', [
        ('es', '**antes o durante**'),
        ('en', '**before or during**'),
    ])
    def test_scope_clause_covers_requests_raised_before_the_project(self, lang, fragment):
        paragraphs = _commercial_cj(lang)['scopeParagraphs']
        assert any(fragment in p for p in paragraphs)

    @pytest.mark.parametrize('lang,fragment', [
        ('es', 'correo electrónico'),
        ('en', 'email'),
    ])
    def test_scope_clause_enumerates_email_like_the_contract(self, lang, fragment):
        paragraphs = _commercial_cj(lang)['scopeParagraphs']
        assert any(fragment in p for p in paragraphs)


# ---------------------------------------------------------------------------
# flatten_terms_clauses / _clause_bullets
# ---------------------------------------------------------------------------

class TestClauseFlattening:
    def test_flatten_emits_one_bold_labelled_line_per_clause(self):
        flat = flatten_terms_clauses([
            {'label': 'Elegibilidad', 'text': 'Aplica a X.'},
            {'label': 'Vigencia', 'text': 'Dura Y.'},
        ])
        assert flat == '**Elegibilidad.** Aplica a X.\n**Vigencia.** Dura Y.'

    def test_flatten_skips_empty_text_and_tolerates_missing_label(self):
        flat = flatten_terms_clauses([
            {'label': 'A', 'text': '   '},
            {'label': '', 'text': 'Sin categoría.'},
            'not-a-dict',
        ])
        assert flat == 'Sin categoría.'

    def test_flatten_of_non_list_is_empty(self):
        assert flatten_terms_clauses(None) == ''

    def test_clause_bullets_prefer_clauses_over_legacy_terms(self):
        bullets = _clause_bullets(
            [{'label': 'Alcance', 'text': 'Uno.'}],
            'legacy que no debe usarse',
        )
        assert bullets == ['**Alcance.** Uno.']

    def test_clause_bullets_fall_back_to_legacy_terms_line_by_line(self):
        bullets = _clause_bullets(None, '**A.** uno\n**B.** dos')
        assert bullets == ['**A.** uno', '**B.** dos']

    def test_clause_bullets_empty_when_nothing_to_render(self):
        assert _clause_bullets([], '') == []


# ---------------------------------------------------------------------------
# PDF annex — same clauses the web modal receives
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPdfAnnex:
    def _data_and_ps(self):
        cj = _value_added_cj('es')
        catalog = {
            mid: {'title': f'Modulo {mid}', 'description': '', 'items': []}
            for mid in MODULE_IDS
        }
        data = {
            'index': '11',
            'title': cj['title'],
            'intro': cj['intro'],
            'module_ids': list(MODULE_IDS),
            'justifications': cj['justifications'],
            'conditions': cj['conditions'],
            'general_terms': cj['general_terms'],
            'footer_note': cj['footer_note'],
        }
        ps = {
            'num': 1,
            'client': 'C',
            '_pdf_lang': 'es',
            '_currency': 'COP',
            '_value_added_catalog': catalog,
            '_effective_total': Decimal('15000000'),
        }
        return data, ps

    def _render_capture(self, pdf_canvas, monkeypatch):
        recorded = []
        orig_b = pdf_mod._draw_bullet_list

        def rec_b(c, y, items, *a, **k):
            recorded.extend(str(it) for it in (items or []))
            return orig_b(c, y, items, *a, **k)

        monkeypatch.setattr(pdf_mod, '_draw_bullet_list', rec_b)
        data, ps = self._data_and_ps()
        _render_value_added_modules(
            pdf_canvas, data, None, ps=ps, y=PAGE_H - MARGIN_T)
        return recorded

    def test_pdf_annex_emits_every_module_clause(self, pdf_canvas, monkeypatch):
        """The PDF must carry exactly the clauses the web modal shows."""
        recorded = self._render_capture(pdf_canvas, monkeypatch)
        cj = _value_added_cj('es')
        for module_id in MODULE_IDS:
            for clause in cj['conditions'][module_id]['terms_clauses']:
                expected = f"**{clause['label']}.** {clause['text']}"
                assert expected in recorded, (
                    f"{module_id} clause '{clause['label']}' missing from the PDF annex")

    def test_pdf_annex_emits_the_general_provisions(self, pdf_canvas, monkeypatch):
        recorded = self._render_capture(pdf_canvas, monkeypatch)
        for clause in _value_added_cj('es')['general_terms']['clauses']:
            expected = f"**{clause['label']}.** {clause['text']}"
            assert expected in recorded

    def test_pdf_annex_falls_back_to_legacy_terms(self, pdf_canvas, monkeypatch):
        """Proposals predating the clause format still render their terms."""
        recorded = []
        orig_b = pdf_mod._draw_bullet_list

        def rec_b(c, y, items, *a, **k):
            recorded.extend(str(it) for it in (items or []))
            return orig_b(c, y, items, *a, **k)

        monkeypatch.setattr(pdf_mod, '_draw_bullet_list', rec_b)
        data = {
            'index': '11', 'title': 'T', 'intro': '',
            'module_ids': ['admin_module'],
            'justifications': {},
            'conditions': {'admin_module': {'terms': 'Términos heredados.'}},
        }
        ps = {
            'num': 1, 'client': 'C', '_pdf_lang': 'es', '_currency': 'COP',
            '_value_added_catalog': {
                'admin_module': {'title': 'Admin', 'description': '', 'items': []},
            },
            '_effective_total': Decimal('1000'),
        }
        _render_value_added_modules(
            pdf_canvas, data, None, ps=ps, y=PAGE_H - MARGIN_T)
        assert 'Términos heredados.' in recorded


# ---------------------------------------------------------------------------
# JSON/MCP import must not wipe the legal terms
# ---------------------------------------------------------------------------

class TestImportPreservesLegalTerms:
    def test_payload_without_conditions_keeps_them(self):
        previous = _value_added_cj('es')
        payload = {
            'title': 'Incluido',
            'module_ids': list(MODULE_IDS),
            'justifications': {'admin_module': 'nuevo texto'},
        }
        merged = merge_value_added_legal_terms(payload, previous)
        assert set(merged['conditions']) == set(previous['conditions'])
        assert merged['general_terms'] == previous['general_terms']
        assert merged['justifications'] == {'admin_module': 'nuevo texto'}

    def test_explicit_payload_conditions_win(self):
        previous = _value_added_cj('es')
        payload = {
            'conditions': {'admin_module': {'terms': 'Términos a medida.'}},
        }
        merged = merge_value_added_legal_terms(payload, previous)
        assert merged['conditions']['admin_module'] == {'terms': 'Términos a medida.'}
        # The modules the payload did not mention are still preserved.
        assert 'ai_automation_module' in merged['conditions']

    def test_non_dict_inputs_are_returned_untouched(self):
        assert merge_value_added_legal_terms(None, {}) is None


# ---------------------------------------------------------------------------
# Migration 0166 — drafts are rewritten, delivered proposals are not
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLegalTermsMigration:
    def _make_proposal(self, status):
        from django.utils import timezone

        from content.models import BusinessProposal, ProposalSection

        proposal = BusinessProposal.objects.create(
            title=f'P {status}', client_name='Cliente',
            client_email=f'{status}@example.com', language='es',
            total_investment=Decimal('15000000'), currency='COP',
            status=status,
            expires_at=timezone.now() + timezone.timedelta(days=14),
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='value_added_modules',
            title='Incluido', order=11, is_enabled=True,
            content_json={
                'title': 'Incluido',
                'module_ids': ['admin_module'],
                'justifications': {},
                'conditions': {'admin_module': {
                    'min_price_cop': None,
                    'terms': 'Redacción comercial vieja.',
                }},
            },
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='commercial_conditions',
            title='Condiciones', order=17, is_enabled=True,
            content_json={
                'title': 'Condiciones',
                'scopeTitle': 'Alcance del trabajo aprobado',
                'scopeParagraphs': [
                    'Cualquier solicitud que surja durante el proyecto no aplica.',
                ],
            },
        )
        return proposal

    def _run_migration(self):
        import importlib

        from django.apps import apps as global_apps

        migration = importlib.import_module(
            'content.migrations.0167_value_added_legal_terms_clauses')
        migration.apply_legal_terms(global_apps, None)

    def _section(self, proposal, section_type):
        return proposal.sections.get(section_type=section_type)

    def test_draft_gets_the_clause_shaped_terms(self):
        proposal = self._make_proposal('draft')
        self._run_migration()

        cond = self._section(proposal, 'value_added_modules').content_json['conditions']['admin_module']
        assert cond['terms_clauses'] == _conditions('es', 'admin_module')['terms_clauses']
        assert cond['terms'] != 'Redacción comercial vieja.'
        # Per-proposal gating a seller may have tuned is preserved.
        assert cond['min_price_cop'] is None

    def test_draft_gets_the_general_provisions(self):
        proposal = self._make_proposal('draft')
        self._run_migration()

        content = self._section(proposal, 'value_added_modules').content_json
        assert content['general_terms'] == _value_added_cj('es')['general_terms']

    def test_draft_scope_clause_is_repaired(self):
        proposal = self._make_proposal('draft')
        self._run_migration()

        paragraphs = self._section(proposal, 'commercial_conditions').content_json['scopeParagraphs']
        assert any('**antes o durante**' in p for p in paragraphs)
        assert any('correo electrónico' in p for p in paragraphs)

    @pytest.mark.parametrize('status', ['sent', 'viewed', 'accepted', 'rejected'])
    def test_delivered_proposals_keep_the_wording_they_were_sent_with(self, status):
        proposal = self._make_proposal(status)
        self._run_migration()

        content = self._section(proposal, 'value_added_modules').content_json
        assert content['conditions']['admin_module']['terms'] == 'Redacción comercial vieja.'
        assert 'terms_clauses' not in content['conditions']['admin_module']
        assert 'general_terms' not in content

        paragraphs = self._section(proposal, 'commercial_conditions').content_json['scopeParagraphs']
        assert paragraphs == [
            'Cualquier solicitud que surja durante el proyecto no aplica.',
        ]

    def test_migration_is_idempotent(self):
        proposal = self._make_proposal('draft')
        self._run_migration()
        first = self._section(proposal, 'value_added_modules').content_json
        self._run_migration()
        assert self._section(proposal, 'value_added_modules').content_json == first


# ---------------------------------------------------------------------------
# Layout — long bold-heavy clauses must not overflow the content width
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAnnexDoesNotOverflow:
    """The annex is far longer and far more bold-heavy than the old paragraph.

    Every clause bullet leads with a bold label and carries several inline bold
    spans, which is exactly the shape that trips width-accurate wrapping. This
    renders the real annex and checks every drawn run against the content box.
    """

    def test_no_drawn_run_exceeds_the_content_width(self, pdf_canvas, monkeypatch):
        from content.services.pdf_utils import CONTENT_W, MARGIN_L

        overflows = []
        original = type(pdf_canvas).drawString

        def recording_draw_string(self, x, y, text, *a, **k):
            if text and text.strip():
                width = self.stringWidth(text, self._fontname, self._fontsize)
                # 1pt of slack absorbs float rounding in the wrap loop.
                if x + width > MARGIN_L + CONTENT_W + 1:
                    overflows.append((round(x + width - MARGIN_L - CONTENT_W, 2),
                                      text[:60]))
            return original(self, x, y, text, *a, **k)

        monkeypatch.setattr(type(pdf_canvas), 'drawString', recording_draw_string)

        cj = _value_added_cj('es')
        data = {
            'index': '11', 'title': cj['title'], 'intro': cj['intro'],
            'module_ids': list(MODULE_IDS),
            'justifications': cj['justifications'],
            'conditions': cj['conditions'],
            'general_terms': cj['general_terms'],
            'footer_note': cj['footer_note'],
        }
        ps = {
            'num': 1, 'client': 'C', '_pdf_lang': 'es', '_currency': 'COP',
            '_value_added_catalog': {
                mid: {'title': f'Modulo {mid}', 'description': '', 'items': []}
                for mid in MODULE_IDS
            },
            '_effective_total': Decimal('15000000'),
        }
        _render_value_added_modules(
            pdf_canvas, data, None, ps=ps, y=PAGE_H - MARGIN_T)

        assert not overflows, f'{len(overflows)} run(s) past the right margin: {overflows[:3]}'
