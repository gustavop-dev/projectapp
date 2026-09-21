"""The demo library contains downloadable resources without duplicate files."""
from datetime import date
from io import StringIO
import pytest
from django.core.management import call_command
from accounts.models import Project
from content.models import Linktree, ProjectBrandAsset

pytestmark = pytest.mark.django_db


def test_auxiliary_seed_creates_project_resources_and_preserves_them_on_repeat(admin_user):
    Project.objects.create(name='Demo project', client=admin_user)
    options = {'count': 12, 'seed': 19, 'anchor_date': date(2026, 8, 26), 'stdout': StringIO()}
    call_command('create_fake_auxiliary', **options)
    asset = ProjectBrandAsset.objects.get(category='manual')
    stored_name = asset.file.name
    with asset.file.open('rb') as stream:
        assert b'Demo project' in stream.read()
    call_command('create_fake_auxiliary', **options)
    asset.refresh_from_db()
    assert asset.file.name == stored_name
    assert ProjectBrandAsset.objects.count() == 3
    assert Linktree.objects.filter(project__isnull=False).count() == 1
    assert Linktree.objects.filter(project__isnull=True).count() == 1
