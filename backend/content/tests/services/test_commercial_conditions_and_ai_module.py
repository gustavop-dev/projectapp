"""Tests for the commercial-conditions section, the free AI automation module
and the value-added per-module gating/terms (Req 1, 2, 3).

Covers:
- section_content_schemas: commercial_conditions + value_added conditions.
- migration 0142 _augment_sections_json: additions + idempotency.
- PDF: _render_commercial_conditions renders; _render_value_added_modules
  shows the "condicionado" minimum note only when the effective total is below
  the module minimum, and prints the consolidated terms block.
- Full ProposalPdfService.generate smoke with the new sections.
"""
import importlib
import io
from decimal import Decimal

import pytest
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.models import BusinessProposal
from content.models.proposal_section import ProposalSection
from content.services import proposal_pdf_service as pdf_mod
from content.services.proposal_pdf_service import (
    MARGIN_T,
    PAGE_H,
    ProposalPdfService,
    _register_fonts,
    _render_commercial_conditions,
    _render_value_added_modules,
)
from content.services.proposal_service import DEFAULT_SECTIONS
from content.services.section_content_schemas import validate_section_content

pytestmark = pytest.mark.django_db

_migration = importlib.import_module(
    'content.migrations.0142_backfill_ai_module_and_commercial_conditions'
)


@pytest.fixture
def pdf_canvas():
    _register_fonts()
    buf = io.BytesIO()
    return canvas.Canvas(buf, pagesize=A4)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_commercial_conditions_valid(self):
        content = {
            'title': 'Condiciones', 'packagesTitle': 'Paquetes',
            'hourlyRate': 90000, 'currency': 'COP',
            'packages': [{'name': 'Ágil', 'hours': 20, 'discountPercent': 0,
                          'note': 'x'}],
            'effortBadge': 'badge', 'scopeTitle': 'Alcance',
            'scopeParagraphs': ['p1', 'p2'],
        }
        assert validate_section_content('commercial_conditions', content) == []

    def test_commercial_conditions_rejects_bad_types(self):
        content = {'hourlyRate': 'not-a-number',
                   'packages': [{'hours': 'nope'}]}
        errors = validate_section_content('commercial_conditions', content)
        assert any('hourlyRate' in e for e in errors)
        assert any('hours' in e for e in errors)

    def test_value_added_conditions_dict_ok(self):
        content = {'module_ids': ['ai_automation_module'],
                   'conditions': {'ai_automation_module': {
                       'min_price_usd': 2900, 'duration_months': 6}}}
        assert validate_section_content('value_added_modules', content) == []

    def test_value_added_conditions_wrong_type(self):
        errors = validate_section_content(
            'value_added_modules', {'conditions': ['not-a-dict']})
        assert any('conditions' in e for e in errors)


# ---------------------------------------------------------------------------
# Migration augment helper
# ---------------------------------------------------------------------------

class TestAugmentSectionsJson:
    def _sample(self):
        # Minimal snapshot with an FR section (no ai module) and a value_added
        # section (no ai id / conditions) and NO commercial_conditions.
        return [
            {'section_type': 'functional_requirements',
             'content_json': {'groups': [{'id': 'admin_module'}]}},
            {'section_type': 'value_added_modules',
             'content_json': {'module_ids': ['admin_module'],
                              'justifications': {}}},
        ]

    def test_adds_all_pieces(self):
        sections = self._sample()
        changed = _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        assert changed is True
        fr = next(s for s in sections
                  if s['section_type'] == 'functional_requirements')
        assert any(g.get('id') == 'ai_automation_module'
                   for g in fr['content_json']['groups'])
        va = next(s for s in sections
                  if s['section_type'] == 'value_added_modules')
        assert 'ai_automation_module' in va['content_json']['module_ids']
        assert 'ai_automation_module' in va['content_json']['conditions']
        assert any(s['section_type'] == 'commercial_conditions'
                   for s in sections)

    def test_idempotent(self):
        sections = self._sample()
        _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        n_before = len(sections)
        changed = _migration._augment_sections_json(sections, DEFAULT_SECTIONS)
        assert changed is False
        assert len(sections) == n_before


# ---------------------------------------------------------------------------
# PDF: commercial_conditions renderer
# ---------------------------------------------------------------------------

class TestRenderCommercialConditions:
    def test_renders_and_returns_number(self, pdf_canvas, monkeypatch):
        recorded = []
        orig = pdf_mod._draw_paragraphs

        def rec(c, y, paragraphs, *a, **k):
            recorded.extend(str(p) for p in (paragraphs or []))
            return orig(c, y, paragraphs, *a, **k)

        monkeypatch.setattr(pdf_mod, '_draw_paragraphs', rec)
        data = {
            'index': '17', 'title': 'Condiciones comerciales',
            'packagesTitle': 'Paquetes', 'packagesIntro': 'intro-text',
            'hourlyRate': 90000, 'currency': 'COP',
            'packages': [
                {'name': 'Ágil', 'hours': 20, 'discountPercent': 0},
                {'name': 'Pro', 'hours': 60, 'discountPercent': 10},
            ],
            'effortBadge': 'Esfuerzo medio se cotiza aparte',
            'scopeTitle': 'Alcance del trabajo aprobado',
            'scopeParagraphs': ['El trabajo aprobado corresponde solo al alcance.'],
        }
        result = _render_commercial_conditions(
            pdf_canvas, data, None, ps={'num': 1, 'client': 'X'},
            y=PAGE_H - MARGIN_T)
        assert isinstance(result, (int, float))
        assert any('alcance' in r.lower() for r in recorded)


# ---------------------------------------------------------------------------
# PDF: value_added gating ("condicionado")
# ---------------------------------------------------------------------------

class TestValueAddedGating:
    def _data_and_ps(self, effective_total):
        catalog = {'ai_automation_module': {
            'id': 'ai_automation_module', 'title': 'Automatización IA',
            'description': 'desc'}}
        data = {
            'index': '11', 'title': 'Incluido',
            'module_ids': ['ai_automation_module'],
            'justifications': {'ai_automation_module': 'j'},
            'conditions': {'ai_automation_module': {
                'min_price_cop': 10400000, 'min_price_usd': 2900,
                'duration_months': 6, 'discretionary_note': 'si aplica',
                'terms': 'Depende del asistente de IA.'}},
        }
        ps = {'num': 1, 'client': 'X', '_value_added_catalog': catalog,
              '_pdf_lang': 'es', '_currency': 'COP',
              '_effective_total': effective_total}
        return data, ps

    def _render_capture(self, pdf_canvas, monkeypatch, effective_total):
        recorded = []
        orig = pdf_mod._draw_paragraphs

        def rec(c, y, paragraphs, *a, **k):
            recorded.extend(str(p) for p in (paragraphs or []))
            return orig(c, y, paragraphs, *a, **k)

        monkeypatch.setattr(pdf_mod, '_draw_paragraphs', rec)
        data, ps = self._data_and_ps(effective_total)
        _render_value_added_modules(
            pdf_canvas, data, None, ps=ps, y=PAGE_H - MARGIN_T)
        return recorded

    def test_shows_minimum_note_when_below(self, pdf_canvas, monkeypatch):
        recorded = self._render_capture(pdf_canvas, monkeypatch, Decimal('5000000'))
        assert any('Disponible en proyectos desde' in r for r in recorded)
        # duration + discretionary + consolidated terms are printed too
        assert any('6 meses' in r for r in recorded)
        assert any('asistente de IA' in r for r in recorded)

    def test_hides_minimum_note_when_met(self, pdf_canvas, monkeypatch):
        recorded = self._render_capture(pdf_canvas, monkeypatch, Decimal('15000000'))
        assert not any('Disponible en proyectos desde' in r for r in recorded)
        # duration still shown regardless of the minimum gate
        assert any('6 meses' in r for r in recorded)


# ---------------------------------------------------------------------------
# Full generate() smoke — returns bytes (None means a renderer raised)
# ---------------------------------------------------------------------------

class TestGenerateSmoke:
    def test_generate_with_new_sections(self):
        proposal = BusinessProposal.objects.create(
            title='Smoke', client_name='Cliente', client_email='s@example.com',
            language='es', total_investment=Decimal('5000000'), currency='COP',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=14),
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='functional_requirements',
            title='FR', order=10, is_enabled=True,
            content_json={'title': 'FR', 'groups': [
                {'id': 'ai_automation_module', 'title': 'Automatización IA',
                 'price_percent': 0, 'description': 'd', 'items': []},
            ], 'additionalModules': []},
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='value_added_modules',
            title='Incluido', order=11, is_enabled=True,
            content_json={
                'title': 'Incluido', 'module_ids': ['ai_automation_module'],
                'justifications': {'ai_automation_module': 'j'},
                'conditions': {'ai_automation_module': {
                    'min_price_cop': 10400000, 'duration_months': 6,
                    'discretionary_note': 'si aplica',
                    'terms': 'Depende del asistente.'}},
            },
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='commercial_conditions',
            title='Condiciones', order=17, is_enabled=True,
            content_json={
                'title': 'Condiciones comerciales', 'hourlyRate': 90000,
                'currency': 'COP',
                'packages': [{'name': 'Ágil', 'hours': 20, 'discountPercent': 0},
                             {'name': 'Pro', 'hours': 60, 'discountPercent': 10}],
                'effortBadge': 'Esfuerzo medio aparte',
                'scopeTitle': 'Alcance', 'scopeParagraphs': ['solo el alcance'],
            },
        )
        result = ProposalPdfService.generate(proposal)
        assert result is not None
        assert len(result) > 1000


# ---------------------------------------------------------------------------
# Migration backfill — exercises the prod-facing data migration on real rows
# ---------------------------------------------------------------------------

class TestBackfillIntegration:
    def _make_legacy_proposal(self, lang='es'):
        proposal = BusinessProposal.objects.create(
            title='Legacy', client_name='Legacy Client',
            client_email='legacy@example.com', language=lang,
            total_investment=Decimal('5000000'), currency='COP', status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=14),
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='functional_requirements',
            title='FR', order=10, is_enabled=True,
            content_json={'groups': [{'id': 'admin_module', 'title': 'Admin'}],
                          'additionalModules': []},
        )
        ProposalSection.objects.create(
            proposal=proposal, section_type='value_added_modules',
            title='Incluido', order=11, is_enabled=True,
            content_json={'module_ids': ['admin_module'], 'justifications': {}},
        )
        return proposal

    def test_backfill_adds_pieces_and_is_idempotent(self):
        from django.apps import apps as django_apps

        proposal = self._make_legacy_proposal()
        _migration.backfill(django_apps, None)

        fr = proposal.sections.get(section_type='functional_requirements')
        assert any(g.get('id') == 'ai_automation_module'
                   for g in fr.content_json['groups'])
        va = proposal.sections.get(section_type='value_added_modules')
        assert 'ai_automation_module' in va.content_json['module_ids']
        assert 'ai_automation_module' in va.content_json['conditions']
        assert proposal.sections.filter(
            section_type='commercial_conditions').count() == 1

        # Re-running must not duplicate anything.
        _migration.backfill(django_apps, None)
        assert proposal.sections.filter(
            section_type='commercial_conditions').count() == 1
        va2 = proposal.sections.get(section_type='value_added_modules')
        assert va2.content_json['module_ids'].count('ai_automation_module') == 1
