"""Tests for the ProposalDefaultConfig model."""
import pytest

from content.models import ProposalDefaultConfig

pytestmark = pytest.mark.django_db


SAMPLE_SECTIONS = [
    {
        'section_type': 'greeting',
        'title': 'Saludo',
        'order': 0,
        'is_wide_panel': False,
        'content_json': {'proposalTitle': '', 'clientName': ''},
    },
]


class TestProposalDefaultConfigCreation:
    def test_create_config_for_es(self):
        config = ProposalDefaultConfig.objects.create(
            language='es',
            sections_json=SAMPLE_SECTIONS,
        )
        assert config.pk is not None
        assert config.language == 'es'
        assert config.sections_json == SAMPLE_SECTIONS
        assert config.created_at is not None
        assert config.updated_at is not None

    def test_create_config_for_en(self):
        config = ProposalDefaultConfig.objects.create(
            language='en',
            sections_json=SAMPLE_SECTIONS,
        )
        assert config.language == 'en'

    def test_str_representation(self):
        config = ProposalDefaultConfig.objects.create(
            language='es',
            sections_json=SAMPLE_SECTIONS,
        )
        assert 'Español' in str(config)


class TestProposalDefaultConfigUniqueness:
    def test_unique_language_constraint(self):
        ProposalDefaultConfig.objects.create(
            language='es',
            sections_json=SAMPLE_SECTIONS,
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError) as exc_info:
            ProposalDefaultConfig.objects.create(
                language='es',
                sections_json=SAMPLE_SECTIONS,
            )
        assert 'unique' in str(exc_info.value).lower()

    def test_allows_both_languages(self):
        ProposalDefaultConfig.objects.create(language='es', sections_json=SAMPLE_SECTIONS)
        ProposalDefaultConfig.objects.create(language='en', sections_json=SAMPLE_SECTIONS)
        assert ProposalDefaultConfig.objects.count() == 2


class TestProposalDefaultConfigDefaults:
    def test_sections_json_defaults_to_empty_list(self):
        config = ProposalDefaultConfig.objects.create(language='es')
        assert config.sections_json == []

    def test_expiration_days_defaults_to_21(self):
        config = ProposalDefaultConfig.objects.create(language='en')
        assert config.expiration_days == 21
