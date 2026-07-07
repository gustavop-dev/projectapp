"""Unit tests for the extracted diagnostic analytics service.

Complements the HTTP-level shape tests in
``content/tests/views/test_diagnostic_analytics.py`` by exercising the service
helpers directly: the engagement score weights and the N+1-free title resolver.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from content.models import (
    DiagnosticSectionView,
    DiagnosticViewEvent,
    WebAppDiagnostic,
)
from content.services import diagnostic_analytics_service as svc

pytestmark = pytest.mark.django_db


def _track(diagnostic, session_id, *, section_type='purpose',
           section_title='Propósito', time_spent=10.0, ip=None,
           entered_at=None):
    # (diagnostic, session_id) is unique — reuse the event for repeat visits
    # in the same session, adding another SectionView each time.
    event, _ = DiagnosticViewEvent.objects.get_or_create(
        diagnostic=diagnostic,
        session_id=session_id,
        defaults={'ip_address': ip},
    )
    DiagnosticSectionView.objects.create(
        view_event=event,
        section_type=section_type,
        section_title=section_title,
        time_spent_seconds=time_spent,
        entered_at=entered_at or timezone.now(),
    )
    return event


def test_section_engagement_uses_latest_title_in_one_pass(diagnostic):
    now = timezone.now()
    _track(diagnostic, 's1', section_title='Título viejo',
           entered_at=now - timedelta(hours=2))
    _track(diagnostic, 's2', section_title='Título nuevo',
           entered_at=now - timedelta(minutes=5))

    # A single -entered_at pass resolves the latest title per section type,
    # replacing the old per-section subquery (an N+1).
    rows = svc.section_engagement(diagnostic)

    purpose = next(r for r in rows if r['section_type'] == 'purpose')
    assert purpose['section_title'] == 'Título nuevo'
    assert purpose['visit_count'] == 2


def test_section_engagement_reach_flag_adds_reached_sessions(diagnostic):
    _track(diagnostic, 's1')
    _track(diagnostic, 's1')  # same session, one distinct reach
    _track(diagnostic, 's2')

    rows = svc.section_engagement(diagnostic, with_reach=True)
    purpose = next(r for r in rows if r['section_type'] == 'purpose')
    assert purpose['reached_sessions'] == 2
    assert purpose['visit_count'] == 3


def test_engagement_score_rewards_cost_time_ip_and_recency(diagnostic):
    diagnostic.status = WebAppDiagnostic.Status.SENT
    diagnostic.save(update_fields=['status'])
    events = diagnostic.view_events.all()

    sections_data = [{'section_type': 'cost', 'total_time_seconds': 35}]
    score = svc.compute_engagement_score(
        diagnostic, events, sections_data,
        unique_sessions=1, first_viewed_at=timezone.now(), coverage_ratio=0.5,
    )
    # cost>=30 → +10, total>=40? no (35) ; coverage 0.5 → +10 ; SENT day0 → +15
    assert score >= 20
    assert 0 <= score <= 100


def test_engagement_score_is_zero_without_activity(diagnostic):
    events = diagnostic.view_events.all()
    score = svc.compute_engagement_score(
        diagnostic, events, [], unique_sessions=0,
        first_viewed_at=None, coverage_ratio=0,
    )
    assert score == 0


def test_active_status_grants_flat_bonus(diagnostic):
    diagnostic.status = WebAppDiagnostic.Status.NEGOTIATING
    diagnostic.save(update_fields=['status'])
    events = diagnostic.view_events.all()
    score = svc.compute_engagement_score(
        diagnostic, events, [], unique_sessions=0,
        first_viewed_at=None, coverage_ratio=0,
    )
    assert score == svc.ENGAGEMENT_ACTIVE_STATUS_BONUS


def test_session_history_respects_limit(diagnostic):
    for i in range(5):
        _track(diagnostic, f'sess-{i}')
    assert len(svc.session_history(diagnostic, limit=3)) == 3
    assert len(svc.session_history(diagnostic, limit=10)) == 5


def test_build_analytics_returns_the_expected_keys(diagnostic):
    data = svc.build_diagnostic_analytics(diagnostic)
    expected = {
        'total_views', 'unique_sessions', 'first_viewed_at', 'last_viewed_at',
        'time_to_first_view_hours', 'time_to_response_hours', 'responded_at',
        'sections', 'skipped_sections', 'device_breakdown', 'sessions',
        'timeline', 'funnel', 'comparison', 'engagement_score',
    }
    assert set(data.keys()) == expected
    # sections rows must NOT leak the internal reach counter
    for row in data['sections']:
        assert 'reached_sessions' not in row
