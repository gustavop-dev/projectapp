"""Spot-checks that user-facing panel error messages are in Spanish.

Locks the EN->ES translation sweep across the tasks, documents, blog, portfolio
and email-template modules so the strings can't silently regress to English.
"""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_tasks_invalid_board_is_spanish(admin_client):
    resp = admin_client.get(reverse('list-tasks') + '?board=nope')
    assert resp.status_code == 400
    assert resp.json()['board'] == 'Tipo de tablero no válido.'


def test_documents_upload_markdown_without_file_is_spanish(admin_client):
    resp = admin_client.post(reverse('upload-document-markdown'), {}, format='multipart')
    assert resp.status_code == 400
    assert resp.json()['file'] == 'No se adjuntó ningún archivo.'


def test_document_folders_reorder_non_list_is_spanish(admin_client):
    resp = admin_client.post(
        reverse('reorder-document-folders'), {'ids': 'not-a-list'}, format='json',
    )
    assert resp.status_code == 400
    assert resp.json()['ids'] == 'Debe ser una lista.'


def test_blog_cover_upload_without_file_is_spanish(admin_client, blog_post):
    url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.id})
    resp = admin_client.post(url, {}, format='multipart')
    assert resp.status_code == 400
    assert resp.json()['cover_image'] == 'No se adjuntó ninguna imagen.'


def test_portfolio_cover_upload_without_file_is_spanish(admin_client, portfolio_work):
    url = reverse('upload-portfolio-cover-image', kwargs={'work_id': portfolio_work.id})
    resp = admin_client.post(url, {}, format='multipart')
    assert resp.status_code == 400
    assert resp.json()['cover_image'] == 'No se adjuntó ninguna imagen.'


def test_email_template_not_found_is_spanish(admin_client):
    url = reverse('email-template-detail', kwargs={'template_key': 'nonexistent_key_xyz'})
    resp = admin_client.get(url)
    assert resp.status_code == 404
    assert 'no existe en el registro.' in resp.json()['detail']


def test_diagnostic_create_without_client_is_spanish(admin_client):
    resp = admin_client.post(reverse('create-diagnostic'), {}, format='json')
    assert resp.status_code == 400
    data = resp.json()
    assert data['error'] == 'Selecciona un cliente antes de continuar.'
    assert data['code'] == 'client_id_required'


def test_diagnostic_respond_invalid_decision_is_spanish(client, diagnostic):
    url = reverse(
        'respond-public-diagnostic',
        kwargs={'diagnostic_uuid': diagnostic.uuid},
    )
    resp = client.post(url, {'decision': 'maybe'}, format='json')
    assert resp.status_code == 400
    data = resp.json()
    assert data['error'] == 'La decisión debe ser aceptar o rechazar.'
    assert data['code'] == 'invalid_decision'
