"""Gap tests for content/views/diagnostic.py — targeting uncovered branches."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import UserProfile
from content.models import WebAppDiagnostic
from content.models.diagnostic_attachment import DiagnosticAttachment
from content.services import diagnostic_service

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_profile(db, username, email):
    user = User.objects.create_user(username=username, email=email, password='x')
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


# ---------------------------------------------------------------------------
# list_diagnostics — filter params
# ---------------------------------------------------------------------------

def test_list_diagnostics_with_status_filter_returns_matching_only(admin_client, diagnostic):
    diagnostic.status = WebAppDiagnostic.Status.SENT
    diagnostic.initial_sent_at = diagnostic.created_at
    diagnostic.save(update_fields=['status', 'initial_sent_at'])

    response = admin_client.get('/api/diagnostics/?status=sent')
    assert response.status_code == 200
    ids = [d['id'] for d in response.json()]
    assert diagnostic.id in ids


def test_list_diagnostics_with_client_id_filter_returns_matching_only(
    admin_client, diagnostic,
):
    response = admin_client.get(f'/api/diagnostics/?client={diagnostic.client_id}')
    assert response.status_code == 200
    ids = [d['id'] for d in response.json()]
    assert diagnostic.id in ids


def test_list_diagnostics_with_nonmatching_client_returns_empty(admin_client, diagnostic):
    response = admin_client.get('/api/diagnostics/?client=99999')
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# create_diagnostic — validation error branches
# ---------------------------------------------------------------------------

def test_create_diagnostic_returns_400_when_no_client_id(admin_client):
    response = admin_client.post('/api/diagnostics/create/', data={}, format='json')
    assert response.status_code == 400
    assert response.json()['error'] == 'client_id_required'


def test_create_diagnostic_returns_404_when_client_not_found(admin_client):
    response = admin_client.post('/api/diagnostics/create/', data={'client_id': 99999}, format='json')
    assert response.status_code == 404
    assert response.json()['error'] == 'client_not_found'


def test_create_diagnostic_returns_404_when_user_is_not_client_role(admin_client, admin_user):
    admin_profile = UserProfile.objects.filter(user=admin_user).first()
    if admin_profile is None:
        admin_profile = UserProfile.objects.create(user=admin_user, role=UserProfile.ROLE_ADMIN)
    response = admin_client.post(
        '/api/diagnostics/create/',
        data={'client_id': admin_profile.pk},
        format='json',
    )
    assert response.status_code == 404
    assert response.json()['error'] == 'client_not_found'


# ---------------------------------------------------------------------------
# bulk_update_diagnostic_sections — error and edge-case branches
# ---------------------------------------------------------------------------

def test_bulk_update_returns_400_when_sections_is_not_list(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        data={'sections': 'not_a_list'},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'sections_must_be_list'


def test_bulk_update_with_empty_list_returns_200(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        data={'sections': []},
        format='json',
    )
    assert response.status_code == 200


def test_bulk_update_skips_entries_without_id(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        data={'sections': [{'title': 'No ID entry'}]},
        format='json',
    )
    assert response.status_code == 200


def test_bulk_update_skips_non_dict_entries(admin_client, diagnostic):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/sections/bulk-update/',
        data={'sections': ['string_entry', None]},
        format='json',
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# create_diagnostic_activity — validation branches
# ---------------------------------------------------------------------------

def test_create_diagnostic_activity_returns_400_for_invalid_change_type(
    admin_client, diagnostic,
):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        data={'change_type': 'not_a_valid_type', 'description': 'Some note'},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_change_type'


def test_create_diagnostic_activity_returns_400_for_empty_description(
    admin_client, diagnostic,
):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        data={'change_type': 'note', 'description': ''},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'description_required'


def test_create_diagnostic_activity_returns_400_for_whitespace_description(
    admin_client, diagnostic,
):
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/activity/create/',
        data={'change_type': 'note', 'description': '   '},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'description_required'


# ---------------------------------------------------------------------------
# respond_public_diagnostic — validation and conflict branches
# ---------------------------------------------------------------------------

def test_respond_public_diagnostic_returns_400_for_invalid_decision(diagnostic):
    from rest_framework.test import APIClient
    client = APIClient()
    response = client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/respond/',
        data={'decision': 'maybe'},
        format='json',
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'invalid_decision'


def test_respond_public_diagnostic_returns_409_for_invalid_transition(diagnostic):
    from rest_framework.test import APIClient
    # diagnostic is in DRAFT — cannot accept from DRAFT
    client = APIClient()
    response = client.post(
        f'/api/diagnostics/public/{diagnostic.uuid}/respond/',
        data={'decision': 'accept'},
        format='json',
    )
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# delete_diagnostic_attachment — generated doc guard
# ---------------------------------------------------------------------------

def test_delete_diagnostic_attachment_returns_400_for_generated_attachment(
    admin_client, diagnostic,
):
    attachment = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=DiagnosticAttachment.DOC_TYPE_CONFIDENTIALITY,
        title='Auto-generated PDF',
        is_generated=True,
    )
    response = admin_client.delete(
        f'/api/diagnostics/{diagnostic.id}/attachments/{attachment.id}/delete/',
    )
    assert response.status_code == 400
    assert 'error' in response.json()


def test_delete_diagnostic_attachment_with_no_file_returns_204(admin_client, diagnostic):
    attachment = DiagnosticAttachment.objects.create(
        diagnostic=diagnostic,
        document_type=DiagnosticAttachment.DOC_TYPE_OTHER,
        title='No file attachment',
        is_generated=False,
    )
    response = admin_client.delete(
        f'/api/diagnostics/{diagnostic.id}/attachments/{attachment.id}/delete/',
    )
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# upload_diagnostic_attachment — validation branches
# ---------------------------------------------------------------------------

def test_upload_attachment_returns_400_for_invalid_document_type(admin_client, diagnostic):
    pdf_file = SimpleUploadedFile('test.pdf', b'%PDF-1.4', content_type='application/pdf')
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        data={'file': pdf_file, 'document_type': 'not_a_valid_type'},
        format='multipart',
    )
    assert response.status_code == 400
    assert 'Invalid document_type' in response.json()['error']


def test_upload_attachment_with_custom_type_label_stores_label(admin_client, diagnostic):
    pdf_file = SimpleUploadedFile('test.pdf', b'%PDF-1.4', content_type='application/pdf')
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        data={
            'file': pdf_file,
            'document_type': DiagnosticAttachment.DOC_TYPE_OTHER,
            'custom_type_label': 'My Custom Label',
        },
        format='multipart',
    )
    assert response.status_code == 201
    assert response.json()['custom_type_label'] == 'My Custom Label'


def test_upload_attachment_clears_custom_label_for_non_other_type(admin_client, diagnostic):
    pdf_file = SimpleUploadedFile('test.pdf', b'%PDF-1.4', content_type='application/pdf')
    response = admin_client.post(
        f'/api/diagnostics/{diagnostic.id}/attachments/upload/',
        data={
            'file': pdf_file,
            'document_type': DiagnosticAttachment.DOC_TYPE_LEGAL_ANNEX,
            'custom_type_label': 'Should be cleared',
        },
        format='multipart',
    )
    assert response.status_code == 201
    assert response.json().get('custom_type_label', '') == ''
