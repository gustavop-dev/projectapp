"""Gap tests for content/services/diagnostic_service.py — uncovered branches."""
import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from content.models import WebAppDiagnostic
from content.models.diagnostic_section import DiagnosticSection
from content.services import diagnostic_service

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def client_profile(db):
    user = User.objects.create_user(
        username='svc_client@test.com', email='svc_client@test.com', password='x',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


@pytest.fixture
def diag(client_profile):
    return diagnostic_service.create_diagnostic(client=client_profile, language='es')


# ---------------------------------------------------------------------------
# _classify_size — each size bucket
# ---------------------------------------------------------------------------

class TestClassifySize:
    def test_zero_value_returns_empty_string(self):
        result = diagnostic_service._classify_size(0, (15, 50))
        assert result == ''

    def test_value_below_low_threshold_returns_pequeña(self):
        result = diagnostic_service._classify_size(5, (15, 50))
        assert result == 'Pequeña'

    def test_value_at_low_threshold_returns_mediana(self):
        result = diagnostic_service._classify_size(15, (15, 50))
        assert result == 'Mediana'

    def test_value_between_thresholds_returns_mediana(self):
        result = diagnostic_service._classify_size(30, (15, 50))
        assert result == 'Mediana'

    def test_value_above_high_threshold_returns_grande(self):
        result = diagnostic_service._classify_size(100, (15, 50))
        assert result == 'Grande'


# ---------------------------------------------------------------------------
# build_render_context — missing optional fields default gracefully
# ---------------------------------------------------------------------------

class TestBuildRenderContext:
    def test_diagnostic_with_empty_radiography_returns_zero_defaults(self, diag):
        diag.radiography = {}
        diag.save(update_fields=['radiography'])

        ctx = diagnostic_service.build_render_context(diag)

        assert ctx['modules_count'] == 0
        assert ctx['modules_list'] == ''
        assert ctx['entities_count'] == 0

    def test_diagnostic_with_modules_as_list_builds_modules_list(self, diag):
        diag.radiography = {'modules': ['Auth', 'Payments', 'Reports']}
        diag.save(update_fields=['radiography'])

        ctx = diagnostic_service.build_render_context(diag)

        assert ctx['modules_count'] == 3
        assert '1. Auth' in ctx['modules_list']

    def test_diagnostic_with_empty_payment_terms_returns_empty_pcts(self, diag):
        diag.payment_terms = {}
        diag.save(update_fields=['payment_terms'])

        ctx = diagnostic_service.build_render_context(diag)

        assert ctx['payment_initial_pct'] == ''
        assert ctx['payment_final_pct'] == ''


# ---------------------------------------------------------------------------
# seed_sections — idempotency (calling twice does not duplicate)
# ---------------------------------------------------------------------------

class TestSeedSections:
    def test_seed_sections_on_cleared_diagnostic_creates_sections(self, diag):
        diag.sections.all().delete()
        assert diag.sections.count() == 0

        diagnostic_service.seed_sections(diag)

        assert diag.sections.count() > 0


# ---------------------------------------------------------------------------
# transition_status — invalid and valid transitions
# ---------------------------------------------------------------------------

class TestTransitionStatus:
    def test_invalid_transition_raises_value_error(self, diag):
        with pytest.raises(ValueError, match='invalid_transition'):
            diagnostic_service.transition_status(
                diag, WebAppDiagnostic.Status.ACCEPTED,
            )

    def test_valid_transition_draft_to_sent_updates_status(self, diag):
        updated = diagnostic_service.transition_status(
            diag, WebAppDiagnostic.Status.SENT,
        )

        assert updated.status == WebAppDiagnostic.Status.SENT
        assert updated.initial_sent_at is not None

    def test_second_sent_transition_sets_final_sent_at(self, diag):
        diagnostic_service.transition_status(diag, WebAppDiagnostic.Status.SENT)
        diag.refresh_from_db()

        diagnostic_service.transition_status(diag, WebAppDiagnostic.Status.NEGOTIATING)
        diag.refresh_from_db()

        diagnostic_service.transition_status(diag, WebAppDiagnostic.Status.SENT)
        diag.refresh_from_db()

        assert diag.final_sent_at is not None


# ---------------------------------------------------------------------------
# visible_sections — filters by visibility rules
# ---------------------------------------------------------------------------

class TestVisibleSections:
    def test_draft_diagnostic_returns_empty_list(self, diag):
        result = diagnostic_service.visible_sections(diag)

        assert result == []

    def test_sent_diagnostic_returns_initial_and_both_sections(self, diag):
        diag.sections.all().delete()
        DiagnosticSection.objects.create(
            diagnostic=diag, section_type='overview', title='Overview',
            order=0, is_enabled=True,
            visibility=DiagnosticSection.Visibility.INITIAL,
        )
        DiagnosticSection.objects.create(
            diagnostic=diag, section_type='cost', title='Cost',
            order=1, is_enabled=True,
            visibility=DiagnosticSection.Visibility.BOTH,
        )
        DiagnosticSection.objects.create(
            diagnostic=diag, section_type='final_notes', title='Final Notes',
            order=2, is_enabled=True,
            visibility=DiagnosticSection.Visibility.FINAL,
        )

        diagnostic_service.transition_status(diag, WebAppDiagnostic.Status.SENT)

        result = diagnostic_service.visible_sections(diag)

        section_types = [s.section_type for s in result]
        assert 'overview' in section_types
        assert 'cost' in section_types
        assert 'final_notes' not in section_types
