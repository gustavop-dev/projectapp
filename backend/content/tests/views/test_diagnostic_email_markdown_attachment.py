"""Tests for the diagnostic-email markdown→PDF attachment endpoint."""
from unittest.mock import patch

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def _url(diagnostic_id):
    return reverse(
        'generate-diagnostic-email-markdown-attachment',
        kwargs={'diagnostic_id': diagnostic_id},
    )


class TestGenerateDiagnosticEmailMarkdownAttachment:
    def test_requires_admin(self, api_client, diagnostic):
        response = api_client.post(
            _url(diagnostic.id),
            {'title': 'X', 'markdown': 'hello'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_missing_title_returns_400(self, admin_client, diagnostic):
        response = admin_client.post(
            _url(diagnostic.id),
            {'markdown': 'hello'},
            format='json',
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'title_required'

    def test_missing_markdown_returns_400(self, admin_client, diagnostic):
        response = admin_client.post(
            _url(diagnostic.id),
            {'title': 'X'},
            format='json',
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'markdown_required'

    def test_unknown_diagnostic_returns_404(self, admin_client):
        response = admin_client.post(
            _url(999999),
            {'title': 'X', 'markdown': 'hello'},
            format='json',
        )
        assert response.status_code == 404

    def test_pdf_response_has_correct_headers(self, admin_client, diagnostic):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate_from_markdown',
            return_value=b'%PDF-1.4 mock-bytes',
        ):
            response = admin_client.post(
                _url(diagnostic.id),
                {
                    'title': 'Resumen diagnóstico',
                    'markdown': '# Hola\n\nContenido.',
                    'include_portada': True,
                    'include_subportada': False,
                    'include_contraportada': True,
                },
                format='json',
            )
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content.startswith(b'%PDF')
        assert 'resumen-diagnostico.pdf' in response['Content-Disposition']

    def test_pdf_service_called_with_correct_params(self, admin_client, diagnostic):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate_from_markdown',
            return_value=b'%PDF-1.4 mock-bytes',
        ) as mock_gen:
            admin_client.post(
                _url(diagnostic.id),
                {
                    'title': 'Resumen diagnóstico',
                    'markdown': '# Hola\n\nContenido.',
                    'include_portada': True,
                    'include_subportada': False,
                    'include_contraportada': True,
                },
                format='json',
            )
        mock_gen.assert_called_once()
        kwargs = mock_gen.call_args.kwargs
        assert kwargs['title'] == 'Resumen diagnóstico'
        assert kwargs['client_name'] == 'Ana Cliente'
        assert kwargs['include_portada'] is True
        assert kwargs['include_subportada'] is False
        assert kwargs['include_contraportada'] is True
