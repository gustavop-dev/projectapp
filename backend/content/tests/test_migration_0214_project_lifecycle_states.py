"""Regression coverage for the legacy Project status backfill."""
from importlib import import_module

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model

from accounts.models import Project
from content.models import (
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
)

pytestmark = pytest.mark.django_db
User = get_user_model()
migration = import_module('content.migrations.0214_seed_project_lifecycle_states')


@pytest.fixture
def migrated_legacy_projects():
    Project.objects.all().delete()
    DocumentStateEpisode.objects.filter(project__isnull=False).delete()
    DocumentState.objects.filter(catalog='projects').delete()
    DocumentStateGroup.objects.filter(catalog='projects').delete()

    client = User.objects.create_user(
        username='migration-projects@example.com',
        email='migration-projects@example.com',
    )
    Project.objects.bulk_create([
        Project(name='Operando', client=client, status=Project.STATUS_ACTIVE),
        Project(name='En pausa', client=client, status='paused'),
        Project(name='Cerrado bien', client=client, status=Project.STATUS_COMPLETED),
        Project(name='Archivo ambiguo', client=client, status=Project.STATUS_ARCHIVED),
    ])

    migration.seed_project_states(apps, None)
    return {
        project.name: Project.objects.select_related('current_state').get(
            name=project.name,
        )
        for project in Project.objects.all()
    }


def test_known_legacy_statuses_receive_matching_states(migrated_legacy_projects):
    assert migrated_legacy_projects['Operando'].current_state.system_key == 'active'
    assert migrated_legacy_projects['En pausa'].current_state.system_key == 'paused'
    assert (
        migrated_legacy_projects['Cerrado bien'].current_state.system_key
        == 'completed'
    )


def test_migrated_projects_require_manual_review(migrated_legacy_projects):
    assert all(
        project.state_review_required
        for project in migrated_legacy_projects.values()
    )


def test_archived_legacy_project_stays_unclassified(migrated_legacy_projects):
    archived = migrated_legacy_projects['Archivo ambiguo']

    assert archived.current_state_id is None
    assert not DocumentStateEpisode.objects.filter(project=archived).exists()


def test_migrated_state_history_keeps_unknown_opening_time(
    migrated_legacy_projects,
):
    project = migrated_legacy_projects['Operando']
    episode = DocumentStateEpisode.objects.get(project=project)
    event = DocumentStateEpisodeEvent.objects.get(episode=episode)

    assert episode.opened_at is None
    assert episode.origin == DocumentStateEpisode.Origin.MIGRATION
    assert event.effective_at is None
    assert event.details['opening_time_known'] is False
