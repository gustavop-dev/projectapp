"""Tests for the client-facing document portal (platform / JWT).

Covers list scoping, PDF download auth, the email-validation OTP flow, the
signature gate + audit fields, and team/client notifications.
"""
from unittest.mock import patch

import pytest
from django.core import mail

from accounts.models import Notification, UserProfile, VerificationCode
from content.models import Document

pytestmark = pytest.mark.django_db


def _make_document(client_user, project=None, *, title='Contrato', published=True,
                   requires_signature=False):
    return Document.objects.create(
        title=title,
        status=Document.Status.PUBLISHED if published else Document.Status.DRAFT,
        client_user=client_user,
        project=project,
        requires_signature=requires_signature,
        content_json={'blocks': [{'type': 'paragraph', 'text': 'Hola'}]},
    )


@pytest.fixture
def other_client(db, admin_user):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username='other-client@test.com',
        email='other-client@test.com',
        password='pass12345',
        first_name='Other',
        last_name='Client',
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT,
        is_onboarded=True, profile_completed=True, created_by=admin_user,
    )
    return user


# ---------------------------------------------------------------------------
# Listing & scoping
# ---------------------------------------------------------------------------

def test_list_returns_own_documents_and_email_state(api_client, client_user, client_headers, project):
    _make_document(client_user, project, title='Main', requires_signature=True)
    resp = api_client.get('/api/accounts/documents/', **client_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body['email'] == client_user.email
    assert body['email_verified'] is False
    assert len(body['documents']) == 1
    assert body['documents'][0]['title'] == 'Main'


def test_list_excludes_other_clients_documents(api_client, client_user, client_headers, project, other_client):
    _make_document(other_client, title='Not yours')
    resp = api_client.get('/api/accounts/documents/', **client_headers)
    assert resp.status_code == 200
    assert resp.json()['documents'] == []


def test_list_excludes_unpublished(api_client, client_user, client_headers, project):
    _make_document(client_user, project, title='Draft', published=False)
    resp = api_client.get('/api/accounts/documents/', **client_headers)
    assert resp.json()['documents'] == []


def test_list_orders_signable_document_first(api_client, client_user, client_headers, project):
    _make_document(client_user, project, title='Annex A')
    _make_document(client_user, project, title='Contract', requires_signature=True)
    resp = api_client.get('/api/accounts/documents/', **client_headers)
    titles = [d['title'] for d in resp.json()['documents']]
    assert titles[0] == 'Contract'


# ---------------------------------------------------------------------------
# Detail & PDF
# ---------------------------------------------------------------------------

def test_detail_owner_ok_other_client_404(api_client, client_user, client_headers, project, other_client):
    mine = _make_document(client_user, project, title='Mine')
    theirs = _make_document(other_client, title='Theirs')
    ok = api_client.get(f'/api/accounts/documents/{mine.uuid}/', **client_headers)
    assert ok.status_code == 200
    denied = api_client.get(f'/api/accounts/documents/{theirs.uuid}/', **client_headers)
    assert denied.status_code == 404


def test_pdf_download_owner_ok(api_client, client_user, client_headers, project):
    doc = _make_document(client_user, project, title='PDF Doc')
    with patch(
        'accounts.document_views.DocumentPdfService.generate',
        return_value=b'%PDF-1.4 fake',
    ):
        resp = api_client.get(f'/api/accounts/documents/{doc.uuid}/pdf/', **client_headers)
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'application/pdf'
    assert 'attachment;' in resp['Content-Disposition']


def test_pdf_other_client_404(api_client, client_headers, other_client):
    doc = _make_document(other_client, title='Theirs')
    resp = api_client.get(f'/api/accounts/documents/{doc.uuid}/pdf/', **client_headers)
    assert resp.status_code == 404


def test_pdf_uses_document_persisted_style_no_override(
    api_client, client_user, client_headers, project,
):
    """Platform PDF download has no ?template= param — it must rely on
    DocumentPdfService.generate() defaulting to document.template_style,
    not pass an explicit override."""
    doc = _make_document(client_user, project, title='Friendly Doc')
    doc.template_style = 'friendly'
    doc.save(update_fields=['template_style'])
    with patch(
        'accounts.document_views.DocumentPdfService.generate',
        return_value=b'%PDF-1.4 fake',
    ) as gen:
        resp = api_client.get(f'/api/accounts/documents/{doc.uuid}/pdf/', **client_headers)
    assert resp.status_code == 200
    gen.assert_called_once_with(doc)


# ---------------------------------------------------------------------------
# Email validation (OTP)
# ---------------------------------------------------------------------------

def test_email_verify_request_sends_otp(api_client, client_user, client_headers, mailoutbox):
    resp = api_client.post('/api/accounts/email/verify/request/', **client_headers)
    assert resp.status_code == 200
    assert VerificationCode.objects.filter(
        user=client_user, purpose=VerificationCode.PURPOSE_EMAIL_VALIDATION,
    ).exists()
    assert len(mailoutbox) == 1
    assert client_user.email in mailoutbox[0].to


def test_email_verify_confirm_success_marks_verified_and_enqueues_notice(
    api_client, client_user, client_headers,
):
    code = VerificationCode.create_for_user(
        client_user, purpose=VerificationCode.PURPOSE_EMAIL_VALIDATION,
    )
    with patch('accounts.tasks.notify_team_email_validated_task') as task:
        resp = api_client.post(
            '/api/accounts/email/verify/confirm/', {'code': code.code}, **client_headers,
        )
    assert resp.status_code == 200
    client_user.profile.refresh_from_db()
    assert client_user.profile.email_verified is True
    assert client_user.profile.email_verified_at is not None
    task.assert_called_once_with(client_user.id)


def test_email_verify_confirm_bad_code(api_client, client_user, client_headers):
    VerificationCode.create_for_user(
        client_user, purpose=VerificationCode.PURPOSE_EMAIL_VALIDATION,
    )
    resp = api_client.post(
        '/api/accounts/email/verify/confirm/', {'code': '000000'}, **client_headers,
    )
    assert resp.status_code == 400
    client_user.profile.refresh_from_db()
    assert client_user.profile.email_verified is False


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

def test_sign_blocked_when_email_not_verified(api_client, client_user, client_headers, project):
    doc = _make_document(client_user, project, requires_signature=True)
    resp = api_client.post(
        f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': True}, **client_headers,
    )
    assert resp.status_code == 403
    doc.refresh_from_db()
    assert doc.signed_at is None


def test_sign_rejected_for_non_signable_document(api_client, client_user, client_headers, project):
    client_user.profile.email_verified = True
    client_user.profile.save()
    doc = _make_document(client_user, project, requires_signature=False)
    resp = api_client.post(
        f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': True}, **client_headers,
    )
    assert resp.status_code == 400


def test_sign_success_sets_fields_and_enqueues_notice(
    api_client, client_user, client_headers, project,
):
    client_user.profile.email_verified = True
    client_user.profile.save()
    doc = _make_document(client_user, project, requires_signature=True)
    with patch('accounts.tasks.notify_team_document_signed_task') as task:
        resp = api_client.post(
            f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': True}, **client_headers,
        )
    assert resp.status_code == 200
    doc.refresh_from_db()
    assert doc.signed_at is not None
    assert doc.signed_by_id == client_user.id
    assert doc.signature_name  # populated from user name
    assert doc.signature_ip  # audit trail captured
    task.assert_called_once_with(doc.id)


def test_sign_requires_accept_true(api_client, client_user, client_headers, project):
    client_user.profile.email_verified = True
    client_user.profile.save()
    doc = _make_document(client_user, project, requires_signature=True)
    resp = api_client.post(
        f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': False}, **client_headers,
    )
    assert resp.status_code == 400


def test_sign_is_idempotent(api_client, client_user, client_headers, project):
    client_user.profile.email_verified = True
    client_user.profile.save()
    doc = _make_document(client_user, project, requires_signature=True)
    first = api_client.post(
        f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': True}, **client_headers,
    )
    assert first.status_code == 200
    doc.refresh_from_db()
    first_signed_at = doc.signed_at
    second = api_client.post(
        f'/api/accounts/documents/{doc.uuid}/sign/', {'accept': True}, **client_headers,
    )
    assert second.status_code == 200
    doc.refresh_from_db()
    assert doc.signed_at == first_signed_at  # unchanged


# ---------------------------------------------------------------------------
# Notification service (exercised directly — decoupled from the async queue)
# ---------------------------------------------------------------------------

def test_service_email_validated_notifies_admins_and_team(
    client_user, admin_user, project, mailoutbox,
):
    from accounts.services.client_flow_notifications import (
        send_client_email_validated_notification,
    )
    send_client_email_validated_notification(client_user.id)
    assert Notification.objects.filter(user=admin_user, type=Notification.TYPE_GENERAL).exists()
    assert len(mailoutbox) == 1  # team email


def test_service_document_signed_notifies_and_confirms_to_client(
    client_user, admin_user, project, mailoutbox,
):
    from accounts.services.client_flow_notifications import (
        send_document_signed_notification,
    )
    doc = _make_document(client_user, project, requires_signature=True)
    doc.signed_by = client_user
    doc.signature_name = 'Client User'
    from django.utils import timezone
    doc.signed_at = timezone.now()
    doc.save()

    send_document_signed_notification(doc.id)
    assert Notification.objects.filter(user=admin_user, type=Notification.TYPE_GENERAL).exists()
    # One confirmation to the client + one to the team.
    recipients = {addr for m in mailoutbox for addr in m.to}
    assert client_user.email in recipients
    assert len(mailoutbox) == 2
