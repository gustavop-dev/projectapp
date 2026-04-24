"""Coverage gap tests for content/views/diagnostic.py — simple endpoints and error branches."""

from unittest.mock import patch

import pytest

from content.models import WebAppDiagnostic
from content.services import diagnostic_service


# -- list_diagnostic_sections ------------------------------------------------


@pytest.mark.django_db
def test_list_diagnostic_sections_returns_200(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/sections/')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_list_diagnostic_sections_returns_eight_entries(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/sections/')
    assert len(response.json()) == 8


# -- delete_diagnostic -------------------------------------------------------


@pytest.mark.django_db
def test_delete_diagnostic_returns_204(admin_client, diagnostic):
    diagnostic_id = diagnostic.id
    response = admin_client.delete(f'/api/diagnostics/{diagnostic_id}/delete/')
    assert response.status_code == 204
    assert not WebAppDiagnostic.objects.filter(pk=diagnostic_id).exists()


# -- list_diagnostic_activity ------------------------------------------------


@pytest.mark.django_db
def test_list_diagnostic_activity_returns_200(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/activity/')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# -- list_diagnostic_attachments ---------------------------------------------


@pytest.mark.django_db
def test_list_diagnostic_attachments_returns_empty_list(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/attachments/')
    assert response.status_code == 200
    assert response.json() == []


# -- get_diagnostic_email_defaults -------------------------------------------


@pytest.mark.django_db
@patch(
    'content.services.diagnostic_email_service.DiagnosticEmailService.get_defaults',
    return_value={'subject': 'Test', 'body': ''},
)
def test_get_diagnostic_email_defaults_returns_200(_mock_defaults, admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/email/defaults/')
    assert response.status_code == 200
    assert 'subject' in response.json()


# -- list_diagnostic_emails --------------------------------------------------


@pytest.mark.django_db
@patch(
    'content.services.diagnostic_email_service.DiagnosticEmailService.list_emails',
    return_value={'results': [], 'total': 0},
)
def test_list_diagnostic_emails_returns_200(_mock_list, admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/email/history/')
    assert response.status_code == 200


@pytest.mark.django_db
@patch(
    'content.services.diagnostic_email_service.DiagnosticEmailService.list_emails',
    return_value={'results': [], 'total': 0},
)
def test_list_diagnostic_emails_invalid_page_defaults_to_page_one(_mock_list, admin_client, diagnostic):
    response = admin_client.get(
        f'/api/diagnostics/{diagnostic.id}/email/history/?page=notanumber',
    )
    assert response.status_code == 200
    _mock_list.assert_called_once_with(diagnostic, page=1)


# -- retrieve_public_diagnostic_by_slug --------------------------------------


@pytest.mark.django_db
def test_retrieve_public_diagnostic_by_slug_returns_200(api_client, diagnostic):
    diagnostic.slug = 'test-diag-slug'
    diagnostic.save(update_fields=['slug'])
    response = api_client.get('/api/diagnostics/public/by-slug/test-diag-slug/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_retrieve_public_diagnostic_by_slug_returns_404_for_unknown_slug(api_client):
    response = api_client.get('/api/diagnostics/public/by-slug/this-slug-does-not-exist/')
    assert response.status_code == 404


# -- download_confidentiality_pdf --------------------------------------------


@pytest.mark.django_db
def test_download_confidentiality_pdf_returns_404_when_no_attachment(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/confidentiality/pdf/')
    assert response.status_code == 404
    assert response.json()['error'] == 'El acuerdo aún no ha sido generado.'


# -- generate_confidentiality_pdf_view error path ----------------------------


@pytest.mark.django_db
@patch(
    'content.views.diagnostic._generate_and_save_confidentiality_pdf',
    return_value=None,
)
def test_generate_confidentiality_pdf_returns_500_when_generation_fails(
    _mock_gen, admin_client, diagnostic,
):
    response = admin_client.post(f'/api/diagnostics/{diagnostic.id}/confidentiality/generate/')
    assert response.status_code == 500
    assert 'error' in response.json()


# -- download_draft_confidentiality_pdf error path ---------------------------


@pytest.mark.django_db
@patch(
    'content.services.confidentiality_pdf_service.generate_confidentiality_pdf',
    return_value=None,
)
def test_download_draft_confidentiality_pdf_returns_500_when_generation_fails(
    _mock_gen, admin_client, diagnostic,
):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/confidentiality/draft-pdf/')
    assert response.status_code == 500
    assert 'error' in response.json()


# -- _send_and_transition error branches -------------------------------------


@pytest.mark.django_db
@patch(
    'content.views.diagnostic.diagnostic_service.transition_status',
    side_effect=ValueError('invalid_transition: diagnostic in wrong state'),
)
def test_send_initial_returns_400_when_status_transition_is_invalid(
    _mock_transition, admin_client, diagnostic,
):
    response = admin_client.post(f'/api/diagnostics/{diagnostic.id}/send-initial/', {}, format='json')
    assert response.status_code == 400
    assert 'error' in response.json()


@pytest.mark.django_db
@patch(
    'content.services.diagnostic_email_service.DiagnosticEmailService.send_initial_to_client',
    side_effect=Exception('SMTP connection refused'),
)
def test_send_initial_returns_200_with_email_ok_false_when_email_raises(
    _mock_send, admin_client, diagnostic,
):
    response = admin_client.post(f'/api/diagnostics/{diagnostic.id}/send-initial/', {}, format='json')
    assert response.status_code == 200
    assert response.json()['email_ok'] is False


# -- export_diagnostic_analytics_csv ----------------------------------------


@pytest.mark.django_db
def test_export_diagnostic_analytics_csv_returns_200(admin_client, diagnostic):
    response = admin_client.get(f'/api/diagnostics/{diagnostic.id}/analytics/csv/')
    assert response.status_code == 200
    assert 'text/csv' in response.get('Content-Type', '')
