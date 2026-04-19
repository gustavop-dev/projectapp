"""Tests for the diagnostic markdown template admin endpoints."""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


class TestListDiagnosticTemplates:
    def test_returns_three_templates(self, admin_client):
        url = reverse('list-diagnostic-templates')
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        slugs = {item['slug'] for item in data}
        assert slugs == {'diagnostico-aplicacion', 'diagnostico-tecnico', 'anexo'}
        for item in data:
            assert item['title']
            assert item['filename'].endswith('.md')
            assert item['size_bytes'] > 0
            assert item['updated_at']

    def test_requires_admin(self, client):
        url = reverse('list-diagnostic-templates')
        response = client.get(url)
        assert response.status_code in (401, 403)


class TestGetDiagnosticTemplate:
    def test_returns_markdown_content(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'diagnostico-aplicacion'},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data['slug'] == 'diagnostico-aplicacion'
        assert data['filename'] == 'diagnostico_aplicacion_es.md'
        assert isinstance(data['content_markdown'], str)
        assert len(data['content_markdown']) > 100

    def test_returns_404_for_unknown_slug(self, admin_client):
        url = reverse(
            'get-diagnostic-template',
            kwargs={'slug': 'inexistente'},
        )
        response = admin_client.get(url)
        assert response.status_code == 404
