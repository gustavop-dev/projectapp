"""The deterministic half of the hosting → project consolidation.

Runs the migration's forward function against the live app registry (it
only speaks ``apps.get_model``) to pin the behavior: the ``' - '`` split
creates and links, accent/case variants reuse the client's existing
project instead of duplicating it, ambiguous rows are skipped for manual
completion, and re-running is a no-op.
"""
from decimal import Decimal
from importlib import import_module

import pytest
from accounts.models import Project, UserProfile
from django.apps import apps
from django.contrib.auth import get_user_model

from content.models import HostingRecord

User = get_user_model()
pytestmark = pytest.mark.django_db

migration = import_module(
    'content.migrations.0192_link_hosting_projects_from_client_name',
)


def make_client(email, *, first='German', last='Rojas'):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name=last,
    )
    return UserProfile.objects.create(user=user)


def make_hosting(profile, name, **overrides):
    fields = {
        'client': profile,
        'client_name': name,
        'monthly_value': Decimal('120000.00'),
    }
    fields.update(overrides)
    return HostingRecord.objects.create(**fields)


def run_forward():
    migration.link_projects_from_client_name(apps, None)


class TestHostingProjectConsolidation:
    def test_the_brand_half_becomes_a_linked_project(self):
        owner = make_client('german@example.com')
        first = make_hosting(owner, 'German - Kore')
        second = make_hosting(owner, 'German Rojas - Kore')

        run_forward()

        first.refresh_from_db()
        second.refresh_from_db()
        project = Project.objects.get(name='Kore')
        assert first.project_id == project.pk
        # Same brand for the same client: one project, both rows linked.
        assert second.project_id == project.pk
        assert project.client_id == owner.user_id

    def test_an_accent_or_case_variant_reuses_the_existing_project(self):
        owner = make_client('daniel@example.com')
        existing = Project.objects.create(name='Mimittos', client=owner.user)
        hosting = make_hosting(owner, 'Jimmy & Daniel - MIMÍTTOS')

        run_forward()

        hosting.refresh_from_db()
        assert hosting.project_id == existing.pk
        assert Project.objects.count() == 1

    def test_ambiguous_rows_are_skipped_for_manual_completion(self):
        owner = make_client('nestor@example.com')
        no_separator = make_hosting(owner, 'Xpandia')
        empty_brand = make_hosting(owner, 'Néstor - ')
        unlinked = HostingRecord.objects.create(
            client=None, client_name='Wilson - Gimnasio',
            monthly_value=Decimal('90000.00'),
        )

        run_forward()

        no_separator.refresh_from_db()
        empty_brand.refresh_from_db()
        unlinked.refresh_from_db()
        assert no_separator.project_id is None
        assert empty_brand.project_id is None
        assert unlinked.project_id is None
        assert Project.objects.count() == 0

    def test_rerunning_changes_nothing(self):
        owner = make_client('german@example.com')
        make_hosting(owner, 'German - Kore')

        run_forward()
        run_forward()

        assert Project.objects.filter(name='Kore').count() == 1

    def test_an_already_linked_row_is_never_touched(self):
        owner = make_client('german@example.com')
        chosen = Project.objects.create(name='Elegido a mano', client=owner.user)
        hosting = make_hosting(owner, 'German - Kore', project=chosen)

        run_forward()

        hosting.refresh_from_db()
        assert hosting.project_id == chosen.pk
        assert not Project.objects.filter(name='Kore').exists()
