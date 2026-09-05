"""Data-migration behavior for legacy project access classification."""

from importlib import import_module

import pytest
from django.apps import apps

from accounts.models import ProjectAdminAccess


pytestmark = pytest.mark.django_db
migration = import_module('accounts.migrations.0063_projectaccessnote_projectadminaccess')


def test_legacy_access_moves_when_production_hostname_matches(project):
    project.production_url = 'https://product.example.test'
    project.staging_url = 'https://staging.example.test'
    project.admin_url = 'https://product.example.test/admin/'
    project.admin_username = 'legacy-admin'
    project.admin_password_encrypted = 'encrypted-token'
    project.save(update_fields=[
        'production_url', 'staging_url', 'admin_url',
        'admin_username', 'admin_password_encrypted',
    ])

    migration.classify_legacy_project_access(apps, None)

    project.refresh_from_db()
    access = ProjectAdminAccess.objects.get(project=project)
    assert access.environment == ProjectAdminAccess.Environment.PRODUCTION
    assert access.admin_username == 'legacy-admin'
    assert access.admin_password_encrypted == 'encrypted-token'
    assert project.admin_url == ''


def test_legacy_access_stays_unclassified_when_hostname_is_ambiguous(project):
    project.production_url = 'https://shared.example.test'
    project.staging_url = 'https://shared.example.test/staging/'
    project.admin_url = 'https://shared.example.test/admin/'
    project.admin_username = 'legacy-admin'
    project.save(update_fields=[
        'production_url', 'staging_url', 'admin_url', 'admin_username',
    ])

    migration.classify_legacy_project_access(apps, None)

    project.refresh_from_db()
    assert ProjectAdminAccess.objects.filter(project=project).exists() is False
    assert project.admin_url == 'https://shared.example.test/admin/'
    assert project.admin_username == 'legacy-admin'
