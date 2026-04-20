"""Targeted tests for the WebAppDiagnostic feature (JSON sections model)."""

import pytest

from content.models import DiagnosticChangeLog, DiagnosticSection, WebAppDiagnostic
from content.services import diagnostic_service


# ── Service tests ──────────────────────────────────────────────────────────

def test_create_diagnostic_seeds_eight_sections(diagnostic):
    """Creating a diagnostic must seed the full set of 8 JSON sections."""
    sections = diagnostic.sections.order_by('order')
    assert sections.count() == 8
    types = list(sections.values_list('section_type', flat=True))
    assert types == [
        'purpose', 'radiography', 'categories', 'delivery_structure',
        'executive_summary', 'cost', 'timeline', 'scope',
    ]
    # Each section has a content_json dict with at least a title.
    for section in sections:
        assert isinstance(section.content_json, dict)
        assert section.content_json.get('title')


def test_create_diagnostic_writes_creation_change_log(diagnostic):
    logs = diagnostic.change_logs.filter(
        change_type=DiagnosticChangeLog.ChangeType.CREATED,
    )
    assert logs.count() == 1


def test_categories_seed_includes_fourteen_entries(diagnostic):
    categories_section = diagnostic.sections.get(section_type='categories')
    entries = categories_section.content_json.get('categories', [])
    assert len(entries) == 14
    keys = {e['key'] for e in entries}
    # Sanity-check a few of the canonical categories.
    assert {'architecture', 'security', 'testing', 'documentation'} <= keys


def test_reset_section_restores_default_content(diagnostic):
    section = diagnostic.sections.get(section_type='scope')
    section.content_json = {'considerations': ['edited']}
    section.save()

    diagnostic_service.reset_section(section)
    section.refresh_from_db()
    assert section.content_json.get('considerations') != ['edited']
    assert section.content_json.get('title') == 'Alcance y Consideraciones'


def test_transition_status_validates_and_stamps_timestamp(diagnostic):
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    diagnostic.refresh_from_db()
    assert diagnostic.status == WebAppDiagnostic.Status.SENT
    assert diagnostic.initial_sent_at is not None

    # Invalid jump SENT → FINISHED must raise (FINISHED only after ACCEPTED).
    with pytest.raises(ValueError):
        diagnostic_service.transition_status(
            diagnostic, WebAppDiagnostic.Status.FINISHED,
        )


def test_transition_status_logs_change(diagnostic):
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    log = diagnostic.change_logs.filter(
        change_type=DiagnosticChangeLog.ChangeType.STATUS_CHANGE,
    ).first()
    assert log is not None
    assert log.old_value == WebAppDiagnostic.Status.DRAFT
    assert log.new_value == WebAppDiagnostic.Status.SENT


def test_register_view_increments_count(diagnostic):
    assert diagnostic.view_count == 0
    diagnostic_service.register_view(diagnostic)
    diagnostic_service.register_view(diagnostic)
    assert diagnostic.view_count == 2
    assert diagnostic.last_viewed_at is not None


def test_visible_sections_respects_status_and_phase(diagnostic):
    # DRAFT → no visible sections.
    assert diagnostic_service.visible_sections(diagnostic) == []

    # Initial SENT (no final_sent_at) → only `initial` + `both` visibility.
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    visible = diagnostic_service.visible_sections(diagnostic)
    visibilities = {s.visibility for s in visible}
    assert visibilities <= {'initial', 'both'}
    # Delivery structure is initial-only; executive summary is final-only.
    types = {s.section_type for s in visible}
    assert 'delivery_structure' in types
    assert 'executive_summary' not in types

    # Final SENT → swaps in `final` + `both`.
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.NEGOTIATING)
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    visible = diagnostic_service.visible_sections(diagnostic)
    types = {s.section_type for s in visible}
    assert 'executive_summary' in types
    assert 'delivery_structure' not in types


# ── API tests ──────────────────────────────────────────────────────────────

def test_create_diagnostic_endpoint(admin_client, diag_client_profile):
    response = admin_client.post(
        '/api/diagnostics/create/',
        {'client_id': diag_client_profile.id, 'language': 'es'},
        format='json',
    )
    assert response.status_code == 201
    body = response.json()
    assert body['status'] == 'draft'
    assert len(body['sections']) == 8


def test_create_diagnostic_requires_client_id(admin_client):
    response = admin_client.post('/api/diagnostics/create/', {}, format='json')
    assert response.status_code == 400
    assert response.json()['error'] == 'client_id_required'


def test_send_initial_transitions_status(admin_client, diagnostic, mailoutbox):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/send-initial/', {}, format='json',
    )
    assert response.status_code == 200
    diagnostic.refresh_from_db()
    assert diagnostic.status == 'sent'
    assert diagnostic.initial_sent_at is not None
    assert len(mailoutbox) == 1
    assert 'diag@example.com' in mailoutbox[0].to


def test_public_retrieve_increments_view_count(api_client, diagnostic):
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    response = api_client.get(f'/api/diagnostics/public/{diagnostic.uuid}/')
    assert response.status_code == 200
    body = response.json()
    assert body['client_name']
    # Initial phase: exposes sections with visibility ∈ {initial, both}.
    returned_types = {s['section_type'] for s in body['sections']}
    assert 'executive_summary' not in returned_types
    diagnostic.refresh_from_db()
    assert diagnostic.view_count == 1

    # Explicit track endpoint creates a view event + bumps counter.
    api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track/',
        {'session_id': 'abc123'}, format='json',
    )
    diagnostic.refresh_from_db()
    assert diagnostic.view_count == 2
    assert diagnostic.view_events.count() == 1


def test_public_respond_accept_finalizes_status(api_client, diagnostic):
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.NEGOTIATING)
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)

    response = api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/respond/',
        {'decision': 'accept'},
        format='json',
    )
    assert response.status_code == 200
    diagnostic.refresh_from_db()
    assert diagnostic.status == 'accepted'
    assert diagnostic.responded_at is not None


def test_update_section_persists_content_json(admin_client, diagnostic):
    section = diagnostic.sections.get(section_type='scope')
    response = admin_client.patch(
        f'/api/diagnostics/{diagnostic.id}/sections/{section.id}/update/',
        {
            'content_json': {
                'title': 'Alcance y Consideraciones',
                'considerations': ['Uno', 'Dos'],
            },
            'is_enabled': True,
        },
        format='json',
    )
    assert response.status_code == 200
    section.refresh_from_db()
    assert section.content_json['considerations'] == ['Uno', 'Dos']


def test_bulk_update_sections(admin_client, diagnostic):
    sections = list(diagnostic.sections.order_by('order'))
    payload = [
        {'id': sections[0].id, 'is_enabled': False},
        {'id': sections[1].id, 'title': 'Radiografía editada'},
    ]
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        {'sections': payload},
        format='json',
    )
    assert response.status_code == 200
    sections[0].refresh_from_db()
    sections[1].refresh_from_db()
    assert sections[0].is_enabled is False
    assert sections[1].title == 'Radiografía editada'


def test_activity_log_endpoints(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        {'change_type': 'note', 'description': 'Primer seguimiento con el cliente.'},
        format='json',
    )
    assert response.status_code == 201

    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/activity/')
    assert response.status_code == 200
    body = response.json()
    assert any(entry['change_type'] == 'note' for entry in body)


def test_track_section_view_records_time(api_client, diagnostic):
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track/',
        {'session_id': 'sess-1'}, format='json',
    )
    response = api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track-section/',
        {
            'session_id': 'sess-1',
            'section_type': 'purpose',
            'section_title': 'Propósito',
            'time_spent_seconds': 12.5,
        },
        format='json',
    )
    assert response.status_code == 200
    diagnostic.refresh_from_db()
    event = diagnostic.view_events.first()
    assert event is not None
    view = event.section_views.first()
    assert view is not None
    assert view.section_type == 'purpose'
    assert view.time_spent_seconds == pytest.approx(12.5)


def test_analytics_endpoint_summary(admin_client, api_client, diagnostic):
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track/',
        {'session_id': 'sess-x'}, format='json',
    )
    api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track-section/',
        {
            'session_id': 'sess-x',
            'section_type': 'purpose',
            'section_title': 'Propósito',
            'time_spent_seconds': 9.0,
        },
        format='json',
    )

    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/analytics/')
    assert response.status_code == 200
    body = response.json()
    assert body['unique_sessions'] == 1
    purpose_row = next(
        (row for row in body['sections'] if row['section_type'] == 'purpose'),
        None,
    )
    assert purpose_row is not None
    assert purpose_row['total_time_seconds'] == pytest.approx(9.0)


# ── Edge cases ─────────────────────────────────────────────────────────────

def test_bulk_update_rejects_non_list_payload(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        {'sections': {'id': 1}},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'sections_must_be_list'


def test_bulk_update_skips_unknown_section_ids(admin_client, diagnostic):
    valid = diagnostic.sections.first()
    payload = [
        {'id': 999_999, 'title': 'ghost'},  # skipped silently
        {'id': valid.id, 'title': 'Edited'},
    ]
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        {'sections': payload}, format='json',
    )
    assert response.status_code == 200
    valid.refresh_from_db()
    assert valid.title == 'Edited'


def test_respond_public_rejects_invalid_decision(api_client, diagnostic):
    response = api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/respond/',
        {'decision': 'maybe'}, format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_decision'


def test_respond_public_conflict_when_status_not_sent(api_client, diagnostic):
    # DRAFT cannot transition to ACCEPTED — expect 409 from the view.
    response = api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/respond/',
        {'decision': 'accept'}, format='json',
    )
    assert response.status_code == 409


def test_create_activity_rejects_invalid_change_type(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        {'change_type': 'bogus', 'description': 'x'}, format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_change_type'


def test_create_activity_requires_description(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        {'change_type': 'note', 'description': '   '}, format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'description_required'


def test_track_section_requires_session_and_type(api_client, diagnostic):
    response = api_client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/track-section/',
        {'section_type': 'purpose'}, format='json',
    )
    assert response.status_code == 400


def test_public_retrieve_on_draft_returns_empty_sections(api_client, diagnostic):
    response = api_client.get(f'/api/diagnostics/public/{diagnostic.uuid}/')
    assert response.status_code == 200
    assert response.json()['sections'] == []


def test_public_render_context_is_whitelisted(api_client, diagnostic):
    diagnostic_service.transition_status(diagnostic, WebAppDiagnostic.Status.SENT)
    response = api_client.get(f'/api/diagnostics/public/{diagnostic.uuid}/')
    assert response.status_code == 200
    keys = set(response.json()['render_context'].keys())
    # Admin-only fields must NOT bleed into the public response.
    assert 'controllers_disconnected' not in keys
    assert 'routes_protected' not in keys
    assert 'routes_public' not in keys
    # A client-facing staple must be present.
    assert 'client_name' in keys


def test_update_section_logs_section_updated_change(admin_client, diagnostic):
    section = diagnostic.sections.get(section_type='scope')
    admin_client.patch(
        f'/api/diagnostics/{diagnostic.id}/sections/{section.id}/update/',
        {'content_json': {'title': 'Alcance', 'considerations': ['x']}},
        format='json',
    )
    log = diagnostic.change_logs.filter(
        change_type=DiagnosticChangeLog.ChangeType.SECTION_UPDATED,
    ).first()
    assert log is not None
    assert log.field_name == 'scope'


def test_send_initial_response_exposes_email_ok(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/send-initial/', {}, format='json',
    )
    assert response.status_code == 200
    assert 'email_ok' in response.json()
