"""Tests for diagnostic attachments + email composer endpoints."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import UserProfile
from content.models import DiagnosticAttachment, EmailLog
from content.services import diagnostic_service


User = get_user_model()


@pytest.fixture
def diag_client_profile(db):
    user = User.objects.create_user(
        username='diag_client', email='diag@example.com',
        first_name='Ana', last_name='Cliente',
    )
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': UserProfile.ROLE_CLIENT, 'company_name': 'Acme'},
    )
    profile.role = UserProfile.ROLE_CLIENT
    profile.save()
    return profile


@pytest.fixture
def diagnostic(db, diag_client_profile):
    return diagnostic_service.create_diagnostic(
        client=diag_client_profile, language='es',
    )


def _upload_file(content=b'%PDF-1.4 fake'):
    return SimpleUploadedFile('annex.pdf', content, content_type='application/pdf')


# ── Attachments ──────────────────────────────────────────────────────────

def test_upload_attachment_creates_row(admin_client, diagnostic):
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        {'file': _upload_file(), 'title': 'Anexo',
         'document_type': 'legal_annex'},
        format='multipart',
    )
    assert resp.status_code == 201
    assert resp.data['title'] == 'Anexo'
    assert DiagnosticAttachment.objects.filter(diagnostic=diagnostic).count() == 1


def test_upload_attachment_rejects_bad_extension(admin_client, diagnostic):
    bad = SimpleUploadedFile('script.exe', b'nope', content_type='application/octet-stream')
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        {'file': bad, 'title': 'X', 'document_type': 'other'},
        format='multipart',
    )
    assert resp.status_code == 400


def test_list_attachments_returns_rows_for_diagnostic(admin_client, diagnostic):
    DiagnosticAttachment.objects.create(
        diagnostic=diagnostic, title='One', document_type='other',
        file=_upload_file(),
    )
    resp = admin_client.get(f'/api/diagnostics/{diagnostic.id}/attachments/')
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]['title'] == 'One'


def test_delete_attachment_removes_row(admin_client, diagnostic):
    att = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic, title='Del', document_type='other',
        file=_upload_file(),
    )
    resp = admin_client.delete(
        f'/api/diagnostics/{diagnostic.id}/attachments/{att.id}/delete/',
    )
    assert resp.status_code == 204
    assert not DiagnosticAttachment.objects.filter(pk=att.id).exists()


def test_non_admin_cannot_upload(api_client, diagnostic):
    resp = api_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        {'file': _upload_file(), 'title': 'x'},
        format='multipart',
    )
    assert resp.status_code in (401, 403)


def test_send_attachments_logs_email_with_diagnostic_uuid(
    admin_client, diagnostic,
):
    att = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic, title='Anexo', document_type='legal_annex',
        file=_upload_file(),
    )
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/send/',
        {'attachment_ids': [att.id], 'subject': 'Docs',
         'greeting': 'Hola', 'body': 'Cuerpo', 'footer': 'Gracias'},
        format='json',
    )
    assert resp.status_code == 200
    logs = EmailLog.objects.filter(
        template_key='diagnostic_documents_sent',
        metadata__diagnostic_uuid=str(diagnostic.uuid),
    )
    assert logs.count() == 1
    assert att.id in logs.first().metadata['attached_doc_ids']


def test_send_attachments_requires_at_least_one_id(admin_client, diagnostic):
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/send/',
        {'attachment_ids': []},
        format='json',
    )
    assert resp.status_code == 400


# ── Email composer ───────────────────────────────────────────────────────

def test_email_defaults_returns_recipient_and_subject(admin_client, diagnostic):
    resp = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/email/defaults/',
    )
    assert resp.status_code == 200
    assert resp.data['recipient_email'] == 'diag@example.com'
    assert 'Ana' in resp.data['subject']


def test_send_custom_email_logs_with_diagnostic_uuid(
    admin_client, diagnostic, settings,
):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/email/send/',
        {
            'recipient_email': 'diag@example.com',
            'subject': 'Seguimiento',
            'greeting': 'Hola Ana',
            'sections': json.dumps(['Primer bloque del correo.']),
            'footer': 'Un abrazo.',
        },
        format='multipart',
    )
    assert resp.status_code == 200
    logs = EmailLog.objects.filter(
        template_key='diagnostic_custom_email',
        metadata__diagnostic_uuid=str(diagnostic.uuid),
    )
    assert logs.count() == 1
    assert logs.first().status == 'sent'
    assert len(mail.outbox) == 1


def test_send_custom_email_rejects_empty_sections(admin_client, diagnostic):
    resp = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/email/send/',
        {
            'recipient_email': 'diag@example.com',
            'subject': 'Seguimiento',
            'greeting': 'Hola',
            'sections': json.dumps([]),
            'footer': '',
        },
        format='multipart',
    )
    assert resp.status_code == 400


def test_email_history_filters_by_diagnostic_uuid(
    admin_client, diagnostic, diag_client_profile,
):
    # Log an email for this diagnostic and an unrelated log without the uuid
    EmailLog.objects.create(
        template_key='diagnostic_custom_email',
        recipient='diag@example.com', subject='A', status='sent',
        metadata={'diagnostic_uuid': str(diagnostic.uuid)},
    )
    EmailLog.objects.create(
        template_key='diagnostic_custom_email',
        recipient='other@example.com', subject='B', status='sent',
        metadata={'diagnostic_uuid': 'other-uuid'},
    )
    resp = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/email/history/',
    )
    assert resp.status_code == 200
    assert resp.data['total'] == 1
    assert resp.data['results'][0]['subject'] == 'A'
