"""Tests for the CompanySettings singleton model."""
import pytest

from content.models import CompanySettings

pytestmark = pytest.mark.django_db


class TestCompanySettingsStr:
    def test_str_with_configured_name(self, company_settings):
        assert 'CARLOS MARIO BLANCO' in str(company_settings)

    def test_str_with_unconfigured_name(self, db):
        settings = CompanySettings.objects.create(pk=1)
        result = str(settings)
        assert result  # should not be empty


class TestCompanySettingsSingleton:
    def test_load_creates_singleton_on_first_call(self, db):
        assert CompanySettings.objects.count() == 0
        settings = CompanySettings.load()
        assert settings.pk == 1
        assert CompanySettings.objects.count() == 1

    def test_load_returns_existing_instance(self, company_settings):
        settings = CompanySettings.load()
        assert settings.pk == company_settings.pk
        assert settings.contractor_full_name == 'CARLOS MARIO BLANCO'

    def test_save_forces_pk_to_one(self, db):
        settings = CompanySettings(pk=99, contractor_full_name='Test')
        settings.save()
        assert settings.pk == 1


class TestCompanySettingsToDict:
    def test_to_dict_returns_all_fields(self, company_settings):
        result = company_settings.to_dict()
        expected_keys = {
            'contractor_full_name', 'contractor_cedula', 'contractor_email',
            'bank_name', 'bank_account_type', 'bank_account_number', 'contract_city',
        }
        assert expected_keys.issubset(set(result.keys()))
        assert result['contractor_full_name'] == 'CARLOS MARIO BLANCO'
        assert result['bank_name'] == 'Bancolombia'
