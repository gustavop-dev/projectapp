"""Tests for `_calculate_effective_total_investment` and its two wrappers.

The gate that distinguishes "use persisted literally" from "fall back to
admin defaults" is `has_confirmed`. These tests pin that contract so any
future regression in the backend (PDF, serializer, email service) is
caught.
"""
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSection,
)
from content.views.proposal import (
    _build_effective_totals_map,
    _calculate_effective_total_investment,
    _effective_total_for_proposal,
)

pytestmark = pytest.mark.django_db


FR_CONTENT_WITH_REPORTS_DEFAULT = {
    'additionalModules': [
        {
            'id': 'reports_alerts_module',
            'title': 'Reportes y Alertas',
            'is_visible': True,
            'is_calculator_module': True,
            'default_selected': True,
            'price_percent': 20,
        },
        {
            'id': 'pwa_module',
            'title': 'PWA',
            'is_visible': True,
            'is_calculator_module': True,
            'default_selected': False,
            'price_percent': 40,
        },
    ],
    'groups': [],
}


class TestCalculateEffectiveTotalInvestment:
    def test_without_confirmed_uses_admin_defaults(self):
        """has_confirmed=False → admin's default_selected modules drive the total."""
        result = _calculate_effective_total_investment(
            base_total=Decimal('1800000'),
            selected_modules=[],
            fr_content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
            has_confirmed=False,
        )
        # base + reports_alerts (20%) = 1.8M + 360k = 2.16M
        assert result == Decimal('2160000.00')

    def test_confirmed_with_empty_selection_returns_base(self):
        """has_confirmed=True + []  → literal empty selection, effective=base."""
        result = _calculate_effective_total_investment(
            base_total=Decimal('1800000'),
            selected_modules=[],
            fr_content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
            has_confirmed=True,
        )
        assert result == Decimal('1800000.00')

    def test_confirmed_with_explicit_list_uses_that_list(self):
        """has_confirmed=True + [pwa] → effective = base + pwa(40%)."""
        result = _calculate_effective_total_investment(
            base_total=Decimal('1800000'),
            selected_modules=['module-pwa_module'],
            fr_content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
            has_confirmed=True,
        )
        # base + pwa (40%) = 1.8M + 720k = 2.52M
        assert result == Decimal('2520000.00')

    def test_confirmed_ignores_admin_default_when_not_in_list(self):
        """Even though reports_alerts.default_selected=True, with
        has_confirmed=True and an explicit list that excludes it, the
        admin default is ignored."""
        result = _calculate_effective_total_investment(
            base_total=Decimal('1800000'),
            selected_modules=['module-pwa_module'],
            fr_content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
            has_confirmed=True,
        )
        assert result == Decimal('2520000.00')

    def test_explicit_selected_false_overrides_default_selected(self):
        """``default_selected=True`` is only an initial admin hint. If the
        admin later sets ``selected=False``, that explicit choice wins —
        mirrors the frontend nullish-coalescing rule and prevents the
        client-facing total from including modules the FR section does
        not list as selected (case of prop 86 with corporate_branding)."""
        fr_content = {
            'additionalModules': [
                {
                    'id': 'branding',
                    'title': 'Branding',
                    'is_visible': True,
                    'is_calculator_module': True,
                    'default_selected': True,
                    'selected': False,
                    'price_percent': 35,
                },
            ],
            'groups': [],
        }
        result = _calculate_effective_total_investment(
            base_total=Decimal('6000000'),
            selected_modules=[],
            fr_content_json=fr_content,
            has_confirmed=False,
        )
        assert result == Decimal('6000000.00')


class TestEffectiveTotalForProposal:
    """Integration-lite: exercises the single-proposal wrapper that reads
    the flag from the model itself."""

    def _make_proposal(self, selected_modules, with_confirmed_log):
        proposal = BusinessProposal.objects.create(
            title='Test',
            client_name='Client',
            client_email='client@test.com',
            language='es',
            total_investment=Decimal('1800000'),
            currency='COP',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=15),
            selected_modules=selected_modules,
        )
        ProposalSection.objects.create(
            proposal=proposal,
            section_type='functional_requirements',
            title='FR', order=1, is_enabled=True,
            content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
        )
        if with_confirmed_log:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type=ProposalChangeLog.ChangeType.CALCULATOR_CONFIRMED,
            )
        return proposal

    def test_legacy_unconfirmed_proposal_uses_defaults(self):
        proposal = self._make_proposal(selected_modules=[], with_confirmed_log=False)
        assert _effective_total_for_proposal(proposal) == Decimal('2160000.00')

    def test_confirmed_empty_proposal_returns_base(self):
        proposal = self._make_proposal(selected_modules=[], with_confirmed_log=True)
        assert _effective_total_for_proposal(proposal) == Decimal('1800000.00')


class TestBuildEffectiveTotalsMap:
    """Batch wrapper must evaluate the has_confirmed flag per proposal
    (not use a single stale value for all rows)."""

    @freeze_time('2026-01-15 12:00:00')
    def test_mixed_inputs_resolve_each_proposal_independently(self):
        p_unconfirmed = BusinessProposal.objects.create(
            title='A', client_name='A', client_email='a@test.com',
            language='es', total_investment=Decimal('1800000'), currency='COP',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=15),
            selected_modules=[],
        )
        ProposalSection.objects.create(
            proposal=p_unconfirmed, section_type='functional_requirements',
            title='FR', order=1, is_enabled=True,
            content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
        )

        p_confirmed_empty = BusinessProposal.objects.create(
            title='B', client_name='B', client_email='b@test.com',
            language='es', total_investment=Decimal('1800000'), currency='COP',
            status='sent',
            expires_at=timezone.now() + timezone.timedelta(days=15),
            selected_modules=[],
        )
        ProposalSection.objects.create(
            proposal=p_confirmed_empty, section_type='functional_requirements',
            title='FR', order=1, is_enabled=True,
            content_json=FR_CONTENT_WITH_REPORTS_DEFAULT,
        )
        ProposalChangeLog.objects.create(
            proposal=p_confirmed_empty,
            change_type=ProposalChangeLog.ChangeType.CALCULATOR_CONFIRMED,
        )

        result = _build_effective_totals_map([p_unconfirmed, p_confirmed_empty])

        assert result[p_unconfirmed.id] == Decimal('2160000.00')
        assert result[p_confirmed_empty.id] == Decimal('1800000.00')
