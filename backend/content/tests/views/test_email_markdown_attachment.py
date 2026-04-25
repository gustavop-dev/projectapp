"""Tests for the proposal-email markdown→PDF attachment endpoint."""
from unittest.mock import patch

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def _url(proposal_id):
    return reverse(
        'generate-email-markdown-attachment',
        kwargs={'proposal_id': proposal_id},
    )


class TestGenerateEmailMarkdownAttachment:
    def test_requires_admin(self, client, proposal):
        response = client.post(
            _url(proposal.id),
            {'title': 'X', 'markdown': 'hello'},
            format='json',
        )
        assert response.status_code in (401, 403)

    def test_missing_title_returns_400(self, admin_client, proposal):
        response = admin_client.post(
            _url(proposal.id),
            {'markdown': 'hello'},
            format='json',
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'title_required'

    def test_missing_markdown_returns_400(self, admin_client, proposal):
        response = admin_client.post(
            _url(proposal.id),
            {'title': 'X'},
            format='json',
        )
        assert response.status_code == 400
        assert response.json()['error'] == 'markdown_required'

    def test_unknown_proposal_returns_404(self, admin_client):
        response = admin_client.post(
            _url(999999),
            {'title': 'X', 'markdown': 'hello'},
            format='json',
        )
        assert response.status_code == 404

    def test_returns_pdf_with_correct_headers(self, admin_client, proposal):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate_from_markdown',
            return_value=b'%PDF-1.4 mock-bytes',
        ):
            response = admin_client.post(
                _url(proposal.id),
                {
                    'title': 'Resumen de cambios',
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
        assert 'resumen-de-cambios.pdf' in response['Content-Disposition']

    def test_pdf_service_called_with_correct_params(self, admin_client, proposal):
        with patch(
            'content.services.document_pdf_service.DocumentPdfService.generate_from_markdown',
            return_value=b'%PDF-1.4 mock-bytes',
        ) as mock_gen:
            admin_client.post(
                _url(proposal.id),
                {
                    'title': 'Resumen de cambios',
                    'markdown': '# Hola\n\nContenido.',
                    'include_portada': True,
                    'include_subportada': False,
                    'include_contraportada': True,
                },
                format='json',
            )
        mock_gen.assert_called_once()
        kwargs = mock_gen.call_args.kwargs
        assert kwargs['title'] == 'Resumen de cambios'
        assert kwargs['include_portada'] is True
        assert kwargs['include_subportada'] is False
        assert kwargs['include_contraportada'] is True
