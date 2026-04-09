"""Tests for the platform onboarding PDF service.

Covers: generate_platform_onboarding_pdf() — success paths with full
and minimal parameters, error path (returns None on exception), and
PDF byte integrity check.
"""
from unittest.mock import patch

from content.services.platform_onboarding_pdf import generate_platform_onboarding_pdf


class TestGeneratePlatformOnboardingPdf:
    def test_returns_bytes_with_all_params(self):
        result = generate_platform_onboarding_pdf(
            client_name='Acme Corp',
            client_email='acme@example.com',
            project_name='Portal Acme',
            deliverable_title='Fase 1 — Diseño',
            platform_login_url='https://app.projectapp.co/login',
        )
        assert isinstance(result, bytes)

    def test_returns_bytes_with_empty_optional_params(self):
        result = generate_platform_onboarding_pdf(
            client_name='',
            client_email='',
            project_name='',
            deliverable_title='',
            platform_login_url='',
        )
        assert isinstance(result, bytes)

    def test_pdf_starts_with_pdf_magic_bytes(self):
        result = generate_platform_onboarding_pdf(client_name='Test Client')
        assert result is not None
        assert result[:4] == b'%PDF'

    def test_long_client_name_does_not_crash(self):
        long_name = 'A' * 500
        result = generate_platform_onboarding_pdf(client_name=long_name)
        assert isinstance(result, bytes)

    def test_returns_none_on_exception(self):
        with patch(
            'content.services.platform_onboarding_pdf._register_fonts',
            side_effect=RuntimeError('font error'),
        ):
            result = generate_platform_onboarding_pdf(client_name='Test')
        assert result is None
