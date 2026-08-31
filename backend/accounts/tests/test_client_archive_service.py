"""Archiving a client and the project cascade it drags behind it.

The behaviours worth pinning here are the ones that cost money if they drift:
which projects the cascade touches, that the operator's confirmation matches
what the preview showed, and that coming back does NOT quietly reactivate
projects whose future billing the cascade already cancelled.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Project, UserProfile
from accounts.services import client_archive_service
from accounts.services.client_archive_service import (
    ClientArchiveError,
    archive_client,
    archive_client_preview,
    unarchive_client,
)
from content.models import DocumentState, IncomeRecord
from content.models.accounting_change_log import AccountingChangeLog
from content.services.project_state_service import (
    apply_transition,
    preview_transition,
)

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def actor():
    return User.objects.create_superuser(
        username='archive-admin@example.com',
        email='archive-admin@example.com',
        password='pass12345',
    )


@pytest.fixture
def client_profile():
    user = User.objects.create_user(
        username='archive-client@example.com',
        email='archive-client@example.com',
        password='pass12345',
        first_name='Cliente',
        last_name='Archivable',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def state(key):
    return DocumentState.objects.get(catalog='projects', system_key=key)


def make_project(client_profile, name, status=Project.STATUS_ACTIVE):
    return Project.objects.create(
        name=name, client=client_profile.user, status=status,
    )


def future_income(project, client_profile, *, days=40):
    """An unpaid income dated after today — exactly what the cascade cancels."""
    return IncomeRecord.objects.create(
        concept='Hosting futuro',
        kind=IncomeRecord.Kind.EXPECTED,
        client=client_profile,
        project=project,
        origin=IncomeRecord.Origin.HOSTING,
        period_date=timezone.localdate() + timedelta(days=days),
        total_amount=Decimal('900000.00'),
        gustavo_amount=Decimal('450000.00'),
        carlos_amount=Decimal('450000.00'),
    )


def confirm(preview):
    """The transitions payload the modal would send back."""
    return [
        {'project_id': p['project_id'], 'impact_token': p['impact_token']}
        for p in preview['projects']
    ]


class TestPreview:
    def test_lists_only_the_still_active_projects(
        self, client_profile, actor,
    ):
        live = make_project(client_profile, 'Vivo')
        parked = make_project(client_profile, 'Ya suspendido')
        # Park the second one through the real service so its episode history
        # is the one the cascade will read.
        parked_preview = preview_transition(parked, state('suspended'))
        apply_transition(
            parked, state('suspended'), actor=actor,
            impact_token=parked_preview['impact_token'],
        )

        preview = archive_client_preview(client_profile)

        assert [p['project_id'] for p in preview['projects']] == [live.pk]
        assert [s['project_id'] for s in preview['skipped']] == [parked.pk]
        assert preview['skipped'][0]['reason'] == 'ya_no_activo'

    def test_counts_the_future_billing_the_cascade_would_cancel(
        self, client_profile,
    ):
        project = make_project(client_profile, 'Con ingreso futuro')
        future_income(project, client_profile)

        preview = archive_client_preview(client_profile)

        # The number the modal shows. If this silently drops to 0 the operator
        # confirms a cancellation nobody warned them about.
        assert preview['totals']['future_incomes'] == 1

    def test_a_project_without_state_is_skipped_not_guessed(
        self, client_profile,
    ):
        legacy = Project.objects.create(
            name='Legacy sin estado',
            client=client_profile.user,
            status=Project.STATUS_ARCHIVED,
        )
        Project.objects.filter(pk=legacy.pk).update(current_state=None)

        preview = archive_client_preview(client_profile)

        assert preview['projects'] == []
        assert preview['skipped'][0]['reason'] == 'sin_estado'

    def test_writes_nothing(self, client_profile):
        project = make_project(client_profile, 'Intacto')

        archive_client_preview(client_profile)

        project.refresh_from_db()
        client_profile.refresh_from_db()
        assert project.current_state.system_key == 'active'
        assert client_profile.archived_at is None

    def test_refuses_an_already_archived_client(self, client_profile):
        client_profile.archived_at = timezone.now()
        client_profile.save(update_fields=['archived_at'])

        with pytest.raises(ClientArchiveError) as exc:
            archive_client_preview(client_profile)

        assert exc.value.code == 'client_already_archived'


class TestArchive:
    def test_suspends_every_eligible_project_and_marks_the_client(
        self, client_profile, actor,
    ):
        one = make_project(client_profile, 'Uno')
        two = make_project(client_profile, 'Dos')
        preview = archive_client_preview(client_profile)

        result = archive_client(
            client_profile, transitions=confirm(preview), actor=actor,
        )

        client_profile.refresh_from_db()
        one.refresh_from_db()
        two.refresh_from_db()
        assert client_profile.archived_at is not None
        assert client_profile.archived_by == actor
        assert sorted(result['suspended_projects']) == sorted([one.pk, two.pk])
        assert one.current_state.system_key == 'suspended'
        assert two.current_state.system_key == 'suspended'

    def test_cancels_the_future_income_it_warned_about(
        self, client_profile, actor,
    ):
        project = make_project(client_profile, 'Con ingreso')
        income = future_income(project, client_profile)
        preview = archive_client_preview(client_profile)

        archive_client(
            client_profile, transitions=confirm(preview), actor=actor,
        )

        income.refresh_from_db()
        assert income.kind == IncomeRecord.Kind.CANCELLED

    def test_a_client_with_no_projects_archives_cleanly(
        self, client_profile, actor,
    ):
        # 24 of the 32 real clients have no project at all: the empty cascade
        # is the common case, not an edge one.
        preview = archive_client_preview(client_profile)

        result = archive_client(client_profile, transitions=[], actor=actor)

        client_profile.refresh_from_db()
        assert preview['projects'] == []
        assert result['suspended_projects'] == []
        assert client_profile.archived_at is not None

    def test_rejects_a_confirmation_that_misses_a_project(
        self, client_profile, actor,
    ):
        make_project(client_profile, 'Uno')
        two = make_project(client_profile, 'Dos')
        preview = archive_client_preview(client_profile)
        partial = [
            t for t in confirm(preview) if t['project_id'] != two.pk
        ]

        with pytest.raises(ClientArchiveError) as exc:
            archive_client(client_profile, transitions=partial, actor=actor)

        assert exc.value.code == 'projects_changed'
        client_profile.refresh_from_db()
        assert client_profile.archived_at is None

    def test_rejects_a_project_that_appeared_after_the_preview(
        self, client_profile, actor,
    ):
        make_project(client_profile, 'Uno')
        preview = archive_client_preview(client_profile)
        # A second session creates a project between preview and confirm. It
        # must not be suspended under a confirmation that never listed it.
        make_project(client_profile, 'Llegó tarde')

        with pytest.raises(ClientArchiveError) as exc:
            archive_client(
                client_profile, transitions=confirm(preview), actor=actor,
            )

        assert exc.value.code == 'projects_changed'

    def test_leaves_nothing_written_when_a_token_is_stale(
        self, client_profile, actor,
    ):
        project = make_project(client_profile, 'Uno')
        preview = archive_client_preview(client_profile)
        stale = [
            {'project_id': project.pk, 'impact_token': 'no-es-el-token'},
        ]

        with pytest.raises(Exception):
            archive_client(client_profile, transitions=stale, actor=actor)

        client_profile.refresh_from_db()
        project.refresh_from_db()
        assert client_profile.archived_at is None
        assert project.current_state.system_key == 'active'

    def test_writes_one_audit_row_naming_the_cascade(
        self, client_profile, actor,
    ):
        project = make_project(client_profile, 'Uno')
        preview = archive_client_preview(client_profile)

        archive_client(
            client_profile, transitions=confirm(preview), actor=actor,
        )

        row = AccountingChangeLog.objects.get(
            entity_type=AccountingChangeLog.EntityType.CLIENT,
            object_id=client_profile.pk,
        )
        assert row.actor == actor
        fields = [c['field'] for c in row.changes]
        assert 'cascaded_projects' in fields
        cascaded = [
            c for c in row.changes if c['field'] == 'cascaded_projects'
        ][0]
        assert str(project.pk) in cascaded['new']


class TestUnarchive:
    def test_brings_the_client_back_without_touching_projects(
        self, client_profile, actor,
    ):
        project = make_project(client_profile, 'Uno')
        preview = archive_client_preview(client_profile)
        archive_client(
            client_profile, transitions=confirm(preview), actor=actor,
        )

        result = unarchive_client(client_profile, actor=actor)

        client_profile.refresh_from_db()
        project.refresh_from_db()
        assert client_profile.archived_at is None
        assert client_profile.archived_by is None
        # The cascade cancelled this project's future income on the way in and
        # nothing un-cancels it, so silently returning it to 'active' would
        # restore the label while the figures stay cancelled.
        assert project.current_state.system_key == 'suspended'
        assert result['still_suspended'] == [project.pk]

    def test_the_audit_row_survives_the_round_trip(
        self, client_profile, actor,
    ):
        archive_client(client_profile, transitions=[], actor=actor)
        unarchive_client(client_profile, actor=actor)

        client_profile.refresh_from_db()
        # The profile forgot, on purpose — the trail did not.
        assert client_profile.archived_at is None
        assert AccountingChangeLog.objects.filter(
            entity_type=AccountingChangeLog.EntityType.CLIENT,
            object_id=client_profile.pk,
        ).count() == 2

    def test_refuses_a_client_that_is_not_archived(
        self, client_profile, actor,
    ):
        with pytest.raises(ClientArchiveError) as exc:
            unarchive_client(client_profile, actor=actor)

        assert exc.value.code == 'client_not_archived'


def test_the_target_state_is_resolved_by_system_key(client_profile):
    # Never by walking operational_effect: LEGACY_STATUS_BY_EFFECT has no entry
    # for the empty effect, so a user-made "Sin efecto automático" state picked
    # up dynamically would blow up inside apply_transition.
    assert client_archive_service.suspended_state().system_key == 'suspended'
