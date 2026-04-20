"""Tests for the expanded diagnostic analytics endpoint and CSV export."""

from datetime import timedelta

import pytest
from django.utils import timezone

from content.models import (
    DiagnosticChangeLog,
    DiagnosticSectionView,
    DiagnosticViewEvent,
    WebAppDiagnostic,
)
from content.services import diagnostic_service


# ── Helpers ────────────────────────────────────────────────────────────────

def _track_session(diagnostic, session_id, *, section_type='purpose',
                   section_title='Propósito', time_spent=10.0,
                   user_agent='', ip=None):
    """Create a ViewEvent + one SectionView directly (fast, deterministic)."""
    event = DiagnosticViewEvent.objects.create(
        diagnostic=diagnostic,
        session_id=session_id,
        ip_address=ip,
        user_agent=user_agent,
    )
    DiagnosticSectionView.objects.create(
        view_event=event,
        section_type=section_type,
        section_title=section_title,
        time_spent_seconds=time_spent,
        entered_at=timezone.now(),
    )
    return event


# ── Empty / default state ──────────────────────────────────────────────────

def test_analytics_empty_diagnostic_returns_zeros(admin_client, diagnostic):
    response = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    )
    assert response.status_code == 200
    body = response.json()

    assert body['total_views'] == 0
    assert body['unique_sessions'] == 0
    assert body['first_viewed_at'] is None
    assert body['time_to_first_view_hours'] is None
    assert body['time_to_response_hours'] is None
    assert body['sections'] == []
    # All 8 enabled sections are skipped when nothing has been tracked.
    assert len(body['skipped_sections']) == 8
    assert body['device_breakdown'] == {'desktop': 0, 'mobile': 0, 'tablet': 0}
    assert body['sessions'] == []
    assert body['funnel'] != []  # funnel rows exist even when empty
    assert all(step['reached_count'] == 0 for step in body['funnel'])
    assert body['comparison'] == {
        'avg_time_to_first_view_hours': None,
        'avg_time_to_response_hours': None,
        'avg_views': None,
    }
    assert body['engagement_score'] == 0


# ── first_viewed_at / time_to_first_view ──────────────────────────────────

def test_analytics_first_viewed_at_and_time_to_first_view(
    admin_client, diagnostic,
):
    # Simulate a diagnostic sent 5 hours before the first visit.
    now = timezone.now()
    diagnostic.initial_sent_at = now - timedelta(hours=5)
    diagnostic.save(update_fields=['initial_sent_at'])

    event = _track_session(diagnostic, 'sess-ttfv')
    # Backdate viewed_at to match our scenario.
    DiagnosticViewEvent.objects.filter(pk=event.pk).update(
        viewed_at=now - timedelta(hours=3),
    )

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    assert body['first_viewed_at'] is not None
    # Sent at now-5h, viewed at now-3h → 2h delta.
    assert body['time_to_first_view_hours'] == pytest.approx(2.0, abs=0.1)


# ── skipped_sections ───────────────────────────────────────────────────────

def test_analytics_skipped_sections_excludes_visited(admin_client, diagnostic):
    _track_session(diagnostic, 'sess-a', section_type='purpose')
    _track_session(diagnostic, 'sess-b', section_type='cost')

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    visited = {s['section_type'] for s in body['sections']}
    skipped = {s['section_type'] for s in body['skipped_sections']}

    assert visited == {'purpose', 'cost'}
    # Visited types are not in skipped_sections.
    assert visited.isdisjoint(skipped)
    # Remaining enabled sections are reported as skipped.
    assert len(skipped) == 6


# ── device_breakdown ───────────────────────────────────────────────────────

def test_analytics_device_breakdown_distinguishes_tablet_mobile_desktop(
    admin_client, diagnostic,
):
    # iPad UA contains "Mobile" — must be classified as tablet, not mobile.
    ipad_ua = (
        'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 '
        '(KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    )
    android_ua = (
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) Mobile Safari/537.36'
    )
    desktop_ua = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like '
        'Gecko) Chrome/120.0 Safari/537.36'
    )

    _track_session(diagnostic, 'sess-ipad', user_agent=ipad_ua)
    _track_session(diagnostic, 'sess-android', user_agent=android_ua)
    _track_session(diagnostic, 'sess-desktop', user_agent=desktop_ua)

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    assert body['device_breakdown'] == {
        'tablet': 1, 'mobile': 1, 'desktop': 1,
    }


# ── funnel drop-off ────────────────────────────────────────────────────────

def test_analytics_funnel_reports_drop_off(admin_client, diagnostic):
    # Two sessions reach "purpose"; only one reaches "cost".
    _track_session(diagnostic, 'sess-1', section_type='purpose')
    _track_session(diagnostic, 'sess-2', section_type='purpose')
    # Add a cost view for session 2 only — reuse the same ViewEvent.
    event2 = diagnostic.view_events.get(session_id='sess-2')
    DiagnosticSectionView.objects.create(
        view_event=event2,
        section_type='cost',
        section_title='Costo',
        time_spent_seconds=15.0,
        entered_at=timezone.now(),
    )

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    funnel = {step['section_type']: step for step in body['funnel']}
    assert funnel['purpose']['reached_count'] == 2
    assert funnel['purpose']['drop_off_percent'] == 0.0
    assert funnel['cost']['reached_count'] == 1
    # 1 - 1/2 = 50% drop-off for "cost".
    assert funnel['cost']['drop_off_percent'] == 50.0


# ── engagement_score ───────────────────────────────────────────────────────

def test_analytics_engagement_score_in_valid_range(admin_client, diagnostic):
    # Mild engagement: single session with a bit of cost time.
    _track_session(
        diagnostic, 'sess-e', section_type='cost',
        section_title='Costo', time_spent=40.0, ip='10.0.0.1',
    )

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    score = body['engagement_score']
    assert isinstance(score, int)
    assert 0 <= score <= 100
    # At minimum: 8 (1 recent session) + 10 (cost ≥ 30s) + 8 (unique IP) = 26
    assert score >= 20


# ── Change-log timeline ────────────────────────────────────────────────────

def test_analytics_timeline_includes_change_logs(admin_client, diagnostic):
    diagnostic_service.log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.NOTE,
        description='Follow-up call scheduled',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    types = [entry['change_type'] for entry in body['timeline']]
    assert 'note' in types
    note_entry = next(e for e in body['timeline'] if e['change_type'] == 'note')
    assert note_entry['description'] == 'Follow-up call scheduled'
    assert note_entry['actor_type'] == 'seller'


# ── Comparison with global averages ────────────────────────────────────────

def test_analytics_comparison_excludes_self(
    admin_client, diagnostic, diag_client_profile,
):
    # Create a second diagnostic with a known view_count so the global
    # average is derived only from the *other* diagnostics.
    other = diagnostic_service.create_diagnostic(
        client=diag_client_profile, language='es',
    )
    other.view_count = 10
    other.save(update_fields=['view_count'])

    body = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/',
    ).json()

    assert body['comparison']['avg_views'] == 10.0


# ── CSV export ─────────────────────────────────────────────────────────────

def test_analytics_csv_export_returns_attachment(admin_client, diagnostic):
    _track_session(diagnostic, 'sess-csv', section_type='purpose')

    response = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/csv/',
    )
    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    assert 'attachment' in response['Content-Disposition']

    body = response.content.decode('utf-8')
    assert '--- SECTION ENGAGEMENT ---' in body
    assert '--- SESSION HISTORY ---' in body
    assert '--- CHANGE LOG ---' in body
    assert 'sess-csv' in body
    assert 'purpose' in body


# ── Permission check ───────────────────────────────────────────────────────

def test_analytics_csv_requires_admin(api_client, diagnostic):
    response = api_client.get(
        f'/api/diagnostics/{diagnostic.id}/analytics/csv/',
    )
    assert response.status_code in (401, 403)
