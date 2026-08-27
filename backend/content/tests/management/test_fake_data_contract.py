"""Behavioral contract for the representative development dataset."""

from collections import Counter
from datetime import date
from io import StringIO

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Count, F, Q

from accounts.models import (
    BugReport,
    ChangeRequest,
    Deliverable,
    Project,
    Requirement,
    UserProfile,
)
from content.fake_data import SeedContext, covered_model_labels
from content.models import (
    BlogPost,
    BusinessProposal,
    CommunicationMessage,
    CommunicationMessageDateCorrection,
    CommunicationThread,
    Contact,
    Document,
    DocumentCollectionAccount,
    HostingRecord,
    IncomeRecord,
    LinkedInPost,
    Linktree,
    McpConnector,
    McpRequestLog,
    ProposalShareLink,
    QRCard,
    Task,
    WebAppDiagnostic,
)


pytestmark = pytest.mark.django_db


def run_command(name, *args, **options):
    options.setdefault('stdout', StringIO())
    options.setdefault('verbosity', 0)
    call_command(name, *args, **options)


@pytest.fixture
def seeded_accounting():
    """Create the full accounting distribution for one focused assertion."""

    run_command(
        'create_fake_accounting', '--count', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )


@pytest.fixture
def seeded_documents():
    """Create related clients, accounting rows and documents."""

    run_command(
        'create_fake_clients_projects', '--count', '30',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command(
        'create_fake_accounting', '--count', '30',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command(
        'create_fake_documents', '--count', '15',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )


@pytest.fixture
def seeded_communications():
    """Create the representative communication-history distribution."""

    get_user_model().objects.create_user(
        username='fake-admin', email='fake-admin@example.test', is_staff=True,
    )
    run_command(
        'create_fake_clients_projects', '--count', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command(
        'create_fake_communications', '--count', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )


def complete_dataset_snapshot():
    """Return stable business values, excluding PKs and auto-managed clocks."""

    return {
        'contacts': list(Contact.objects.order_by('email').values_list(
            'email', 'subject', 'message',
        )),
        'blog_posts': list(BlogPost.objects.order_by('title_es').values_list(
            'title_es', 'category', 'read_time_minutes', 'is_published',
            'published_at', 'sources',
        )),
        'projects': list(Project.objects.order_by(
            'client__email', 'name',
        ).values_list(
            'client__email', 'name', 'status', 'start_date', 'estimated_end_date',
        )),
        'documents': list(Document.objects.order_by(
            'title', 'document_type__code', 'client_user__email', 'uuid',
        ).values_list(
            'uuid', 'document_type__code', 'title', 'status', 'commercial_status',
            'public_number', 'folder__name', 'project__name', 'client_user__email',
            'income_record__concept', 'income_record__period_date',
            'issue_date', 'due_date', 'subtotal', 'tax_total', 'total',
        )),
        'incomes': list(IncomeRecord.objects.filter(
            source_ref='fake:accounting',
        ).order_by(
            'concept', 'kind', 'period_date', 'client__user__email',
        ).values_list(
            'concept', 'kind', 'client__user__email', 'project__name',
            'period_date', 'total_amount', 'expected_income__concept',
            'expected_income__period_date', 'source_ref',
        )),
        'proposals': list(BusinessProposal.objects.order_by(
            'title', 'uuid',
        ).values_list(
            'uuid', 'title', 'client__user__email', 'status', 'expires_at',
            'sent_at', 'first_viewed_at', 'responded_at',
        )),
        'proposal_shares': list(ProposalShareLink.objects.order_by(
            'proposal__title', 'recipient_email', 'uuid',
        ).values_list(
            'uuid', 'proposal__title', 'recipient_email', 'view_count',
            'first_viewed_at',
        )),
        'diagnostics': list(WebAppDiagnostic.objects.order_by(
            'title', 'client__user__email', 'uuid',
        ).values_list(
            'uuid', 'title', 'client__user__email', 'status', 'currency',
            'investment_amount', 'duration_label', 'size_category', 'view_count',
        )),
        'threads': list(CommunicationThread.objects.order_by(
            'title',
        ).values_list(
            'title', 'client__user__email', 'project__name', 'status',
            'last_activity_at', 'closed_at',
        )),
        'mcp_history': list(McpRequestLog.objects.order_by(
            'connector__slug', 'detail',
        ).values_list(
            'connector__slug', 'event', 'ok', 'detail', 'created_at',
        )),
    }


def test_model_contract_classifies_every_concrete_business_model():
    actual = {
        model._meta.label
        for app_name in ('accounts', 'content')
        for model in apps.get_app_config(app_name).get_models()
        if not model._meta.proxy
    }

    assert covered_model_labels() == actual


def test_seed_context_replays_the_same_random_stream():
    first = SeedContext(20260826, date(2026, 8, 26), 'documents')
    second = SeedContext(20260826, date(2026, 8, 26), 'documents')

    assert [first.rng.randint(1, 10_000) for _ in range(5)] == [
        second.rng.randint(1, 10_000) for _ in range(5)
    ]


def test_fake_command_fails_closed_without_explicit_capability(settings):
    settings.FAKE_DATA_ALLOWED = False

    with pytest.raises(CommandError, match='FAKE_DATA_ALLOWED=True'):
        run_command('create_contacts', '1')

    assert not Contact.objects.exists()


def test_contact_seed_replays_identical_natural_data():
    args = ('4', '--seed', '19', '--anchor-date', '2026-08-26')
    run_command('create_contacts', *args)
    first = list(Contact.objects.order_by('pk').values_list(
        'email', 'subject', 'message',
    ))

    run_command('delete_fake_data', '--confirm')
    run_command('create_contacts', *args)
    second = list(Contact.objects.order_by('pk').values_list(
        'email', 'subject', 'message',
    ))

    assert second == first


def test_client_project_seed_has_the_target_skew():
    run_command(
        'create_fake_clients_projects', '--count', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    project_counts = Counter(
        UserProfile.objects.clients()
        .annotate(project_total=Count('user__projects'))
        .values_list('project_total', flat=True)
    )

    assert UserProfile.objects.clients().count() == 60
    assert Project.objects.count() == 67
    assert project_counts == Counter({0: 30, 1: 20, 3: 9, 20: 1})


def test_client_project_seed_covers_the_real_lifecycle():
    run_command(
        'create_fake_clients_projects', '--count', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )

    assert set(Project.objects.values_list(
        'current_state__system_key', flat=True,
    )) == {
        'development', 'active', 'evolving', 'paused', 'suspended',
        'completed', 'decommissioned',
    }
    assert not Project.objects.filter(current_state__isnull=True).exists()
    assert not Project.objects.filter(state_review_required=True).exists()


def test_accounting_seed_links_each_record_to_a_client(seeded_accounting):
    assert not IncomeRecord.objects.filter(client__isnull=True).exists()
    assert not HostingRecord.objects.filter(client__isnull=True).exists()


def test_accounting_seed_spans_past_future_dates(seeded_accounting):
    assert IncomeRecord.objects.filter(period_date__lt=date(2026, 8, 26)).exists()
    assert IncomeRecord.objects.filter(period_date__gt=date(2026, 8, 26)).exists()
    assert HostingRecord.objects.filter(valid_to__lt=date(2026, 8, 26)).exists()
    assert HostingRecord.objects.filter(valid_to__gt=date(2026, 8, 26)).exists()


def test_platform_seed_reaches_the_per_list_volume_target():
    run_command(
        'seed_platform_data', '--skip-collection-accounts',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command(
        'enrich_platform_data', '--count', '60', '--notifications', '60',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    project = Project.objects.order_by('pk').first()

    assert Requirement.objects.filter(phase__project=project).count() == 60
    assert Deliverable.objects.filter(project=project).count() == 60
    assert ChangeRequest.objects.filter(project=project).count() == 60
    assert BugReport.objects.filter(project=project).count() == 60


def test_document_seed_links_every_document_to_client_project(seeded_documents):
    assert not Document.objects.filter(client_user__isnull=True).exists()
    assert not Document.objects.filter(project__isnull=True).exists()


def test_document_seed_distributes_folder_presence(seeded_documents):
    assert Document.objects.filter(folder__isnull=True).exists()
    assert Document.objects.filter(folder__isnull=False).exists()


def test_collection_account_seed_links_each_income_origin(seeded_documents):
    assert DocumentCollectionAccount.objects.count() == 10
    assert not DocumentCollectionAccount.objects.filter(
        document__income_record__isnull=True,
    ).exists()


def test_collection_account_seed_matches_income_total(seeded_documents):
    assert not Document.objects.filter(
        collection_account__isnull=False,
    ).exclude(total=F('income_record__total_amount')).exists()


def test_document_seed_honors_a_small_volume_target():
    run_command(
        'create_fake_documents', '--count', '2',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )

    assert Document.objects.count() == 2


def test_communication_seed_distributes_thread_lengths(seeded_communications):
    lengths = Counter(
        CommunicationThread.objects.annotate(total=Count('messages'))
        .values_list('total', flat=True)
    )

    assert lengths == Counter({1: 12, 3: 36, 12: 12})


def test_communication_seed_covers_message_statuses(seeded_communications):
    assert set(CommunicationMessage.objects.values_list('status', flat=True)) == {
        CommunicationMessage.Status.DRAFT,
        CommunicationMessage.Status.FAILED,
        CommunicationMessage.Status.RECEIVED,
        CommunicationMessage.Status.SENT,
    }


def test_communication_seed_closes_quarter_of_threads(seeded_communications):
    assert CommunicationThread.objects.filter(closed_at__isnull=False).count() == 15


def test_communication_seed_creates_date_corrections(seeded_communications):
    assert CommunicationMessageDateCorrection.objects.exists()


def test_communication_seed_creates_voided_messages(seeded_communications):
    assert CommunicationMessage.objects.filter(voided_at__isnull=False).exists()


def test_auxiliary_seed_populates_visible_history_without_credentials():
    run_command(
        'create_fake_clients_projects', '--count', '12',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command(
        'create_fake_auxiliary', '--count', '12',
        '--seed', '19', '--anchor-date', '2026-08-26',
    )

    assert Linktree.objects.count() == 2
    assert QRCard.objects.count() == 6
    assert McpRequestLog.objects.count() == 12
    assert McpConnector.objects.filter(is_active=True).count() == 0


def test_orchestrator_rolls_back_a_failed_stage(monkeypatch):
    from content.management.commands import create_fake_data as orchestrator

    real_call_command = orchestrator.call_command

    def fail_in_contacts(command, *args, **options):
        if command == 'create_contacts':
            Contact.objects.create(
                email='rollback@example.test', subject='rollback', message='rollback',
            )
            raise RuntimeError('seed stage failed')
        return real_call_command(command, *args, **options)

    monkeypatch.setattr(orchestrator, 'call_command', fail_in_contacts)

    with pytest.raises(RuntimeError, match='seed stage failed'):
        run_command(
            'create_fake_data', '--count', '3', '--skip-platform',
            '--skip-proposals', '--skip-blog', '--skip-portfolio', '--skip-tasks',
            '--skip-diagnostics', '--skip-accounting', '--skip-documents',
            '--skip-communications', '--skip-auxiliary',
        )

    assert not Contact.objects.exists()
    assert not UserProfile.objects.clients().exists()


def test_orchestrator_replace_rebuilds_the_existing_graph():
    run_command('create_fake_clients_projects', '--count', '3')
    run_command('create_contacts', '1')

    run_command(
        'create_fake_data', '--replace', '--count', '2', '--skip-platform',
        '--skip-proposals', '--skip-blog', '--skip-portfolio', '--skip-tasks',
        '--skip-diagnostics', '--skip-accounting', '--skip-documents',
        '--skip-communications', '--skip-auxiliary',
    )

    assert UserProfile.objects.clients().count() == 2
    assert Contact.objects.count() == 2


def test_orchestrator_rejects_an_existing_graph_without_replace():
    Contact.objects.create(
        email='existing@example.test',
        subject='existing',
        message='existing business data',
    )

    with pytest.raises(CommandError, match='Run again with --replace'):
        run_command(
            'create_fake_data', '--count', '2', '--skip-platform',
            '--skip-proposals', '--skip-blog', '--skip-portfolio', '--skip-tasks',
            '--skip-diagnostics', '--skip-accounting', '--skip-documents',
            '--skip-communications', '--skip-auxiliary',
        )

    assert Contact.objects.count() == 1


def test_orchestrator_replays_cross_module_natural_values():
    seed_args = (
        '--count', '5', '--seed', '19', '--anchor-date', '2026-08-26',
    )
    run_command('create_fake_data', *seed_args)
    first_snapshot = complete_dataset_snapshot()

    run_command('create_fake_data', '--replace', *seed_args)

    assert complete_dataset_snapshot() == first_snapshot


def test_orchestrator_keeps_cross_module_relationships_coherent():
    run_command(
        'create_fake_data', '--count', '5', '--seed', '19',
        '--anchor-date', '2026-08-26',
    )

    violations = {
        'income_without_client': tuple(IncomeRecord.objects.filter(
            source_ref='fake:accounting', client__isnull=True,
        ).values_list('concept', 'period_date')),
        'income_project_owner_mismatch': tuple(IncomeRecord.objects.filter(
            source_ref='fake:accounting', project__isnull=False,
        ).exclude(
            project__client=F('client__user'),
        ).values_list('concept', 'period_date')),
        'hosting_without_client': tuple(HostingRecord.objects.filter(
            source_ref='fake:accounting', client__isnull=True,
        ).values_list('domain_url', 'valid_to')),
        'hosting_project_owner_mismatch': tuple(HostingRecord.objects.filter(
            source_ref='fake:accounting', project__isnull=False,
        ).exclude(
            project__client=F('client__user'),
        ).values_list('domain_url', 'valid_to')),
        'document_missing_client_or_project': tuple(Document.objects.filter(
            Q(client_user__isnull=True) | Q(project__isnull=True),
        ).values_list('title', flat=True)),
        'document_project_owner_mismatch': tuple(Document.objects.filter(
            project__isnull=False,
        ).exclude(
            project__client=F('client_user'),
        ).values_list('title', flat=True)),
        'collection_account_missing_origin': tuple(
            DocumentCollectionAccount.objects.filter(
                document__income_record__isnull=True,
            ).values_list('document__title', flat=True)
        ),
        'collection_account_total_mismatch': tuple(
            DocumentCollectionAccount.objects.exclude(
                document__total=F('document__income_record__total_amount'),
            ).values_list('document__title', flat=True)
        ),
        'thread_project_owner_mismatch': tuple(
            CommunicationThread.objects.filter(
                project__isnull=False,
            ).exclude(
                project__client=F('client__user'),
            ).values_list('title', flat=True)
        ),
    }

    assert all(not rows for rows in violations.values()), violations


def test_orchestrator_populates_every_visible_module_root():
    run_command(
        'create_fake_data', '--count', '5', '--seed', '19',
        '--anchor-date', '2026-08-26',
    )

    assert UserProfile.objects.clients().exists()
    assert Project.objects.exists()
    assert Contact.objects.count() == 5
    assert BusinessProposal.objects.exists()
    assert BlogPost.objects.count() == 5
    assert Task.objects.count() == 5
    # The diagnostic seeder adds one linked, backdated edge record in addition
    # to the requested list volume.
    assert WebAppDiagnostic.objects.count() == 6
    assert IncomeRecord.objects.exists()
    assert HostingRecord.objects.exists()
    assert Document.objects.exists()
    assert CommunicationThread.objects.count() == 5
    assert Linktree.objects.exists()
    assert QRCard.objects.exists()
    assert LinkedInPost.objects.exists()
    assert McpRequestLog.objects.count() == 5
