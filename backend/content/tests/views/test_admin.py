"""Tests for Django admin configuration.

Covers: ProjectAppAdminSite.get_app_list() custom grouping,
model registrations, CompanySettings contractor identity rule.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from content.admin import CompanySettingsForm, admin_site

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestProjectAppAdminSiteGetAppList:
    def _make_superuser_request(self, db):
        user = User.objects.create_superuser(
            username='super_admin', email='super@test.com', password='pass123',
        )
        request = RequestFactory().get('/admin/')
        request.user = user
        return request

    def test_returns_13_custom_groups(self, db):
        request = self._make_superuser_request(db)
        app_list = admin_site.get_app_list(request)
        assert len(app_list) == 13

    def test_group_names_match_expected_labels(self, db):
        request = self._make_superuser_request(db)
        app_list = admin_site.get_app_list(request)
        names = {app['name'] for app in app_list}
        expected = {
            'Contact Management', 'Portfolio Works Management',
            'Business Proposals', 'Proposals (Extended)',
            'Blog', 'Documents', 'Document Management',
            'Tasks', 'Diagnostics', 'Contract Settings',
            'System', 'Users & Auth', 'Platform',
        }
        assert names == expected


class TestCompanySettingsFormContractorIdentity:
    """The contract names EL CONTRATISTA by one of two documents; the admin
    form is the only place a human sets them, so the rule is enforced there."""

    def _payload(self, **overrides):
        data = {
            'contractor_full_name': 'GUSTAVO ADOLFO PEREZ PEREZ',
            'contractor_nit': '',
            'contractor_cedula': '',
            'contractor_email': 'team@projectapp.co',
            'bank_name': 'Bancolombia',
            'bank_account_type': 'Ahorros',
            'bank_account_number': '123456789',
            'contract_city': 'Medellín',
        }
        data.update(overrides)
        return data

    def test_rejects_a_contractor_with_neither_document(self, db):
        form = CompanySettingsForm(data=self._payload())
        assert not form.is_valid()
        assert 'contractor_nit' in form.errors

    def test_accepts_a_contractor_with_only_a_nit(self, db):
        form = CompanySettingsForm(data=self._payload(contractor_nit='900.123.456-7'))
        assert form.is_valid(), form.errors

    def test_accepts_a_contractor_with_only_a_cedula(self, db):
        form = CompanySettingsForm(data=self._payload(contractor_cedula='1037635428'))
        assert form.is_valid(), form.errors

    def test_whitespace_does_not_count_as_a_document(self, db):
        form = CompanySettingsForm(data=self._payload(contractor_nit='   '))
        assert not form.is_valid()
        assert 'contractor_nit' in form.errors
