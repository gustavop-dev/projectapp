"""Scope-closing limits for the free (value-added) modules.

The five free modules must carry explicit quantity caps in their client-facing
copy (descriptions/items) and in the value_added_modules conditions terms, so
the free scope stays bounded and deliverable.
"""
import pytest

from content.services.proposal_service import ProposalService

pytestmark = pytest.mark.django_db


def _fr_group(lang, group_id):
    sections = ProposalService.get_default_sections(lang)
    fr = next(s for s in sections if s['section_type'] == 'functional_requirements')
    return next(g for g in fr['content_json']['groups'] if g['id'] == group_id)


def _conditions(lang, module_id):
    sections = ProposalService.get_default_sections(lang)
    va = next(s for s in sections if s['section_type'] == 'value_added_modules')
    return va['content_json']['conditions'][module_id]


class TestFreeModuleScopeLimits:
    @pytest.mark.parametrize('lang,phrase', [
        ('es', 'hasta 6 reportes estándar'),
        ('en', 'up to 6 standard reports'),
    ])
    def test_analytics_dashboard_caps_reports_in_description(self, lang, phrase):
        group = _fr_group(lang, 'analytics_dashboard')
        assert phrase in group['description']
        # The 6 listed items ARE the 6 standard reports.
        assert len(group['items']) == 6

    @pytest.mark.parametrize('lang,phrase', [
        ('es', 'hasta 8 KPIs y 4 gráficos'),
        ('en', 'up to 8 KPIs and 4 charts'),
    ])
    def test_kpi_dashboard_caps_kpis_and_charts(self, lang, phrase):
        group = _fr_group(lang, 'kpi_dashboard_module')
        assert phrase in group['description']
        haystack = ' '.join(i['description'] for i in group['items'])
        assert ('Hasta 5 alertas' in haystack) or ('Up to 5 alerts' in haystack)

    @pytest.mark.parametrize('lang,phrase', [
        ('es', 'gestores adicionales se cotizan como ampliación'),
        ('en', 'additional managers are quoted as an extension'),
    ])
    def test_admin_module_scope_limited_to_listed_managers(self, lang, phrase):
        group = _fr_group(lang, 'admin_module')
        assert phrase in group['description']

    @pytest.mark.parametrize('lang,phrase', [
        ('es', 'hasta 15 artículos de documentación'),
        ('en', 'up to 15 documentation articles'),
    ])
    def test_manual_module_caps_articles_and_updates(self, lang, phrase):
        group = _fr_group(lang, 'manual_module')
        assert phrase in group['description']
        assert ('una (1) actualización' in group['description']
                or 'one (1) content update' in group['description'])

    @pytest.mark.parametrize('lang,phrase', [
        ('es', 'Tomamos un (1) proceso'),
        ('en', 'We take one (1) process'),
    ])
    def test_ai_automation_module_explicit_single_process(self, lang, phrase):
        group = _fr_group(lang, 'ai_automation_module')
        assert phrase in group['description']

    @pytest.mark.parametrize('lang,module_id,phrase', [
        ('es', 'analytics_dashboard', 'hasta **6 reportes estándar**'),
        ('en', 'analytics_dashboard', 'up to **6 standard reports**'),
        ('es', 'kpi_dashboard_module', 'hasta **8 KPIs, 4 gráficos y 5 alertas**'),
        ('en', 'kpi_dashboard_module', 'up to **8 KPIs, 4 charts and 5 alerts**'),
        ('es', 'manual_module', 'hasta 15 artículos'),
        ('en', 'manual_module', 'up to 15 articles'),
        ('es', 'admin_module', 'gestores de contenido listados'),
        ('en', 'admin_module', 'content managers listed'),
        ('es', 'ai_automation_module', 'un (1) proceso de negocio'),
        ('en', 'ai_automation_module', 'one (1) business process'),
    ])
    def test_conditions_terms_carry_scope_caps(self, lang, module_id, phrase):
        cond = _conditions(lang, module_id)
        assert phrase in cond['terms']
