"""Regression coverage for consolidating Pausado into Suspendido."""

from datetime import date
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection

from accounts.models import HostingSubscription, Payment, Project, UserProfile
from content.models import (
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
    IncomeRecord,
)


pytestmark = pytest.mark.django_db
User = get_user_model()
migration = import_module(
    'content.migrations.0229_remove_paused_project_state',
)


@pytest.fixture
def client_profile():
    user = User.objects.create_user(
        username='paused-migration@example.com',
        email='paused-migration@example.com',
    )
    return UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
    )


@pytest.fixture
def paused_state():
    group = DocumentStateGroup.objects.get(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        selection_mode=DocumentStateGroup.SelectionMode.EXCLUSIVE,
    )
    return DocumentState.objects.create(
        name='Pausado',
        description='El trabajo estaba detenido temporalmente.',
        color=DocumentState.Color.YELLOW,
        group=group,
        order=3,
        system_key='paused',
        operational_effect='paused',
    )


def run_data_migration():
    migration.consolidate_paused_project_state(
        apps,
        SimpleNamespace(connection=connection),
    )


def make_paused_project(client_profile, paused_state):
    return Project.objects.create(
        name='Proyecto detenido',
        client=client_profile.user,
        current_state=paused_state,
        status='paused',
    )


def make_income(project, client_profile, *, period_date):
    return IncomeRecord.objects.create(
        concept='Hosting del proyecto',
        kind=IncomeRecord.Kind.EXPECTED,
        client=client_profile,
        project=project,
        origin=IncomeRecord.Origin.HOSTING,
        period_date=period_date,
        total_amount=Decimal('120000.00'),
        gustavo_amount=Decimal('60000.00'),
        carlos_amount=Decimal('60000.00'),
    )


def make_payment(project, *, due_date):
    subscription = HostingSubscription.objects.create(
        project=project,
        plan=HostingSubscription.PLAN_QUARTERLY,
        base_monthly_amount=Decimal('120000.00'),
        discount_percent=10,
        effective_monthly_amount=Decimal('108000.00'),
        billing_amount=Decimal('324000.00'),
        status=HostingSubscription.STATUS_ACTIVE,
        start_date=date(2026, 1, 1),
        next_billing_date=due_date,
    )
    return Payment.objects.create(
        subscription=subscription,
        amount=Decimal('324000.00'),
        billing_period_start=due_date,
        billing_period_end=due_date,
        due_date=due_date,
        status=Payment.STATUS_PENDING,
    )


def test_data_migration_replaces_the_paused_current_state(
    client_profile,
    paused_state,
):
    project = make_paused_project(client_profile, paused_state)

    run_data_migration()

    project.refresh_from_db()
    assert project.current_state.system_key == 'suspended'
    assert project.status == Project.STATUS_SUSPENDED
    assert not DocumentState.objects.filter(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        operational_effect='paused',
    ).exists()


def test_data_migration_repoints_history_with_a_merge_event(
    client_profile,
    paused_state,
):
    project = make_paused_project(client_profile, paused_state)
    episode = DocumentStateEpisode.objects.create(
        project=project,
        state=paused_state,
        origin=DocumentStateEpisode.Origin.MANUAL,
    )

    run_data_migration()

    episode.refresh_from_db()
    event = DocumentStateEpisodeEvent.objects.get(
        episode=episode,
        event_type=DocumentStateEpisodeEvent.EventType.MERGED,
    )
    assert episode.state.system_key == 'suspended'
    assert event.details['reason'] == 'paused_state_removed'


def test_data_migration_cancels_future_billing_artifacts(
    client_profile,
    paused_state,
):
    project = make_paused_project(client_profile, paused_state)
    income = make_income(
        project,
        client_profile,
        period_date=date(2099, 1, 1),
    )
    payment = make_payment(project, due_date=date(2099, 1, 1))

    run_data_migration()

    income.refresh_from_db()
    payment.refresh_from_db()
    assert income.kind == IncomeRecord.Kind.CANCELLED
    assert payment.is_archived is True


def test_data_migration_preserves_caused_debt(
    client_profile,
    paused_state,
):
    project = make_paused_project(client_profile, paused_state)
    income = make_income(
        project,
        client_profile,
        period_date=date(2020, 1, 1),
    )
    payment = make_payment(project, due_date=date(2020, 1, 1))

    run_data_migration()

    income.refresh_from_db()
    payment.refresh_from_db()
    assert income.kind == IncomeRecord.Kind.EXPECTED
    assert payment.is_archived is False


def test_data_migration_preserves_a_partially_paid_future_income(
    client_profile,
    paused_state,
):
    project = make_paused_project(client_profile, paused_state)
    income = make_income(
        project,
        client_profile,
        period_date=date(2099, 1, 1),
    )
    IncomeRecord.objects.create(
        concept='Abono recibido',
        kind=IncomeRecord.Kind.LIQUID,
        client=client_profile,
        project=project,
        origin=IncomeRecord.Origin.HOSTING,
        period_date=date(2026, 8, 30),
        total_amount=Decimal('20000.00'),
        gustavo_amount=Decimal('10000.00'),
        carlos_amount=Decimal('10000.00'),
        expected_income=income,
    )

    run_data_migration()

    income.refresh_from_db()
    assert income.kind == IncomeRecord.Kind.EXPECTED


def test_data_migration_classifies_a_legacy_paused_project_without_state(
    client_profile,
):
    project = Project.objects.create(
        name='Proyecto legado sin estado',
        client=client_profile.user,
    )
    Project.objects.filter(pk=project.pk).update(
        current_state=None,
        status='paused',
        state_review_required=True,
    )

    run_data_migration()

    project.refresh_from_db()
    episode = DocumentStateEpisode.objects.get(
        project=project,
        state__system_key='suspended',
        origin=DocumentStateEpisode.Origin.MIGRATION,
    )
    assert project.status == Project.STATUS_SUSPENDED
    assert project.state_review_required is False
    assert episode.opened_at is None


def test_data_migration_removes_custom_paused_effect_states(
    client_profile,
    paused_state,
):
    custom = DocumentState.objects.create(
        name='En espera',
        description='Otra pausa administrable.',
        color=DocumentState.Color.YELLOW,
        group=paused_state.group,
        order=9,
        operational_effect='paused',
    )
    project = Project.objects.create(
        name='Proyecto en espera',
        client=client_profile.user,
        current_state=custom,
        status='paused',
    )

    run_data_migration()

    project.refresh_from_db()
    assert project.current_state.system_key == 'suspended'
    assert not DocumentState.objects.filter(pk=custom.pk).exists()
