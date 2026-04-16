"""Targeted tests for the WebAppDiagnostic feature."""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from content.models import DiagnosticDocument, WebAppDiagnostic
from content.services import diagnostic_service


User = get_user_model()


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def client_user(db):
    user = User.objects.create_user(
        username='client1', email='client1@example.com',
        first_name='María', last_name='Cliente',
    )
    profile, _ = UserProfile.objects.get_or_create(
        user=user, defaults={'role': UserProfile.ROLE_CLIENT, 'company_name': 'Acme'},
    )
    profile.role = UserProfile.ROLE_CLIENT
    profile.save()
    return profile


@pytest.fixture
def diagnostic(db, client_user):
    return diagnostic_service.create_diagnostic(client=client_user, language='es')


# ── Service tests ──────────────────────────────────────────────────────────

def test_create_diagnostic_loads_three_documents_from_templates(diagnostic):
    """Creating a diagnostic must load all 3 markdown documents."""
    docs = diagnostic.documents.order_by('order')
    assert docs.count() == 3
    types = list(docs.values_list('doc_type', flat=True))
    assert types == [
        DiagnosticDocument.DocType.INITIAL_PROPOSAL,
        DiagnosticDocument.DocType.TECHNICAL_PROPOSAL,
        DiagnosticDocument.DocType.SIZING_ANNEX,
    ]
    # Each document must contain non-trivial content from the template files.
    for doc in docs:
        assert len(doc.content_md) > 500
        assert '##' in doc.content_md  # markdown headings present
        # All three docs ship with a TOC (Índice) at the top.
        assert '## Índice' in doc.content_md


def test_render_document_substitutes_pricing_and_falls_back_to_placeholder(diagnostic):
    """{{vars}} get substituted; missing pricing values become a placeholder."""
    diagnostic.investment_amount = 2500000
    diagnostic.currency = 'COP'
    diagnostic.payment_terms = {'initial_pct': 40, 'final_pct': 60}
    diagnostic.duration_label = '1 semana'
    diagnostic.save()

    initial_doc = diagnostic.documents.get(
        doc_type=DiagnosticDocument.DocType.INITIAL_PROPOSAL,
    )
    rendered = diagnostic_service.render_document(initial_doc)

    assert "2'500.000" in rendered
    assert 'COP' in rendered
    assert '40%' in rendered
    assert '60%' in rendered
    assert '1 semana' in rendered
    # No raw {{var}} tokens should leak.
    assert '{{' not in rendered

    # Empty pricing → placeholder for fields marked as human-fillable.
    diagnostic.investment_amount = None
    diagnostic.duration_label = ''
    diagnostic.save()
    rendered2 = diagnostic_service.render_document(initial_doc)
    assert diagnostic_service.PLACEHOLDER in rendered2


def test_transition_status_validates_and_stamps_timestamp(diagnostic):
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    diagnostic.refresh_from_db()
    assert diagnostic.status == WebAppDiagnostic.Status.SENT
    assert diagnostic.initial_sent_at is not None

    # Invalid jump (SENT → FINISHED) should raise — FINISHED is only
    # reachable from ACCEPTED.
    with pytest.raises(ValueError):
        diagnostic_service.transition_status(
            diagnostic, WebAppDiagnostic.Status.FINISHED,
        )


def test_register_view_increments_count(diagnostic):
    assert diagnostic.view_count == 0
    diagnostic_service.register_view(diagnostic)
    diagnostic_service.register_view(diagnostic)
    assert diagnostic.view_count == 2
    assert diagnostic.last_viewed_at is not None


def test_visible_documents_respects_status(diagnostic):
    # DRAFT → no visible docs.
    assert diagnostic_service.visible_documents(diagnostic) == []

    # Initial SENT (no final_sent_at) → only the initial proposal.
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    visible = diagnostic_service.visible_documents(diagnostic)
    assert len(visible) == 1
    assert visible[0].doc_type == DiagnosticDocument.DocType.INITIAL_PROPOSAL

    # Final SENT (final_sent_at stamped) with no docs marked ready → falls back to all 3.
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.NEGOTIATING,
    )
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    visible = diagnostic_service.visible_documents(diagnostic)
    assert len(visible) == 3


# ── API tests ──────────────────────────────────────────────────────────────

def test_create_diagnostic_endpoint(admin_client, client_user):
    response = admin_client.post(
        '/api/diagnostics/create/',
        {'client_id': client_user.id, 'language': 'es'},
        format='json',
    )
    assert response.status_code == 201
    body = response.json()
    assert body['status'] == 'draft'
    assert len(body['documents']) == 3


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
    # Email actually went through (real client email exists in fixture).
    assert len(mailoutbox) == 1
    assert 'client1@example.com' in mailoutbox[0].to


def test_public_retrieve_increments_view_count(api_client, diagnostic):
    diagnostic_service.transition_status(
        diagnostic, WebAppDiagnostic.Status.SENT,
    )
    # Public GET both returns the doc and bumps view_count atomically.
    response = api_client.get(f'/api/diagnostics/public/{diagnostic.uuid}/')
    assert response.status_code == 200
    body = response.json()
    assert body['client_name']
    # Initial-sent state shows only the initial proposal doc.
    assert len(body['documents']) == 1
    diagnostic.refresh_from_db()
    assert diagnostic.view_count == 1

    # Explicit track endpoint still works (e.g., for SPA re-mounts).
    api_client.post(f'/api/diagnostics/public/{diagnostic.uuid}/track/')
    diagnostic.refresh_from_db()
    assert diagnostic.view_count == 2


def test_public_respond_accept_finalizes_status(api_client, diagnostic):
    # Walk forward to the final-sent state first (SENT → NEGOTIATING → SENT).
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


def test_update_document_persists_content(admin_client, diagnostic):
    doc = diagnostic.documents.first()
    response = admin_client.patch(
        f'/api/diagnostics/{diagnostic.id}/documents/{doc.id}/update/',
        {'content_md': '# Custom edited content', 'is_ready': True},
        format='json',
    )
    assert response.status_code == 200
    doc.refresh_from_db()
    assert doc.content_md == '# Custom edited content'
    assert doc.is_ready is True
