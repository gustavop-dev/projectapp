"""Tests for the DiagnosticDefaultConfig model."""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from content.models import DiagnosticDefaultConfig


pytestmark = pytest.mark.django_db


SAMPLE_SECTIONS = [
    {
        'section_type': 'purpose',
        'title': 'Propósito',
        'order': 0,
        'is_enabled': True,
        'visibility': 'both',
        'content_json': {'heading': 'Hola'},
    },
]


class TestDiagnosticDefaultConfigCreation:
    def test_create_es_with_defaults(self):
        config = DiagnosticDefaultConfig.objects.create(language='es')
        assert config.pk is not None
        assert config.payment_initial_pct == 60
        assert config.payment_final_pct == 40
        assert config.default_currency == 'COP'
        assert config.expiration_days == 21
        assert config.reminder_days == 7
        assert config.urgency_reminder_days == 14
        assert config.sections_json == []

    def test_create_en(self):
        config = DiagnosticDefaultConfig.objects.create(
            language='en', sections_json=SAMPLE_SECTIONS,
        )
        assert config.language == 'en'
        assert config.sections_json == SAMPLE_SECTIONS

    def test_str_representation(self):
        config = DiagnosticDefaultConfig.objects.create(language='es')
        assert 'Español' in str(config)


class TestDiagnosticDefaultConfigUniqueness:
    def test_language_is_unique(self):
        DiagnosticDefaultConfig.objects.create(language='es')
        with pytest.raises(IntegrityError) as exc:
            DiagnosticDefaultConfig.objects.create(language='es')
        assert 'unique' in str(exc.value).lower()

    def test_allows_both_languages(self):
        DiagnosticDefaultConfig.objects.create(language='es')
        DiagnosticDefaultConfig.objects.create(language='en')
        assert DiagnosticDefaultConfig.objects.count() == 2


class TestDiagnosticDefaultConfigPaymentValidation:
    def test_clean_accepts_60_40(self):
        config = DiagnosticDefaultConfig(
            language='es', payment_initial_pct=60, payment_final_pct=40,
        )
        assert config.clean() is None

    def test_clean_accepts_50_50(self):
        config = DiagnosticDefaultConfig(
            language='es', payment_initial_pct=50, payment_final_pct=50,
        )
        assert config.clean() is None

    def test_clean_rejects_unbalanced(self):
        config = DiagnosticDefaultConfig(
            language='es', payment_initial_pct=70, payment_final_pct=40,
        )
        with pytest.raises(ValidationError) as excinfo:
            config.clean()
        assert 'payment' in str(excinfo.value).lower()
