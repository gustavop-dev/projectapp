"""Tests for content/services/panel_dashboard_service.py — global panel dashboard."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from django.utils import timezone

from accounts.services import proposal_client_service
from content.models import (
    BusinessProposal,
    Document,
    DocumentType,
    EmailLog,
    HourPackage,
    RecurringPayment,
    Task,
    WebAppDiagnostic,
)
from content.services.panel_dashboard_service import (
    _days_until_billing,
    build_panel_dashboard,
)
from content.services.proposal_analytics_service import (
    build_dashboard,
    build_dashboard_core,
)
from content.utils import today_bogota

pytestmark = pytest.mark.django_db


# ── Fixtures ──

@pytest.fixture
def collection_doc_type(db):
    obj, _ = DocumentType.objects.get_or_create(
        code='collection_account',
        defaults={'name': 'Collection Account', 'label': 'Cuenta de cobro'},
    )
    return obj


def _make_collection_account(doc_type, *, due_date, total):
    return Document.objects.create(
        title=f'CC {due_date}',
        document_type=doc_type,
        client_name='ACME Corp',
        language='es',
        commercial_status=Document.CommercialStatus.ISSUED,
        due_date=due_date,
        total=total,
    )


# ── build_panel_dashboard: shape ──

class TestPayloadShape:
    def test_empty_db_skips_finance_and_attention(self):
        payload = build_panel_dashboard(include_finance=False)
        assert payload['finance'] is None
        assert payload['attention'] == []

    def test_empty_db_zeroes_the_proposals_block(self):
        payload = build_panel_dashboard(include_finance=False)
        assert payload['proposals']['total_proposals'] == 0
        assert payload['proposals']['pipeline_count'] == 0
        assert payload['proposals']['recent'] == []

    def test_empty_db_zeroes_the_operations_block(self):
        ops = build_panel_dashboard(include_finance=False)['operations']
        assert ops['tasks']['open'] == 0
        assert ops['tasks']['overdue'] == 0
        assert ops['documents']['collection_accounts']['issued_count'] == 0
        assert ops['diagnostics']['active_pipeline'] == 0
        assert ops['emails']['total_30d'] == 0
        assert ops['emails']['success_rate'] is None
        # Hour packages are seeded by migration; mirror the live count.
        assert ops['hour_packages']['active_count'] == (
            HourPackage.objects.filter(is_active=True).count()
        )

    def test_finance_block_present_when_included(self):
        payload = build_panel_dashboard(include_finance=True)

        finance = payload['finance']
        assert finance['year'] == today_bogota().year
        assert finance['liquid_total'] == Decimal('0')
        assert finance['pocket_balance'] == Decimal('0')
        assert 'total' in finance['card_debt']
        assert len(finance['monthly']) == 12


# ── operations: tasks ──

class TestTasksSummary:
    def test_overdue_excludes_done_and_archived(self):
        yesterday = today_bogota() - timedelta(days=1)
        Task.objects.create(title='Late', due_date=yesterday, position=0)
        Task.objects.create(
            title='Done late', due_date=yesterday,
            status=Task.Status.DONE, position=1,
        )
        Task.objects.create(
            title='Archived late', due_date=yesterday,
            is_archived=True, position=2,
        )

        tasks = build_panel_dashboard(include_finance=False)['operations']['tasks']

        assert tasks['overdue'] == 1
        assert tasks['open'] == 1

    def test_overdue_high_priority_marks_attention_danger(self):
        yesterday = today_bogota() - timedelta(days=1)
        Task.objects.create(
            title='Urgent late', due_date=yesterday,
            priority=Task.Priority.HIGH, position=0,
        )

        attention = build_panel_dashboard(include_finance=False)['attention']

        item = next(i for i in attention if i['type'] == 'tasks_overdue')
        assert item['severity'] == 'danger'
        assert item['count'] == 1


# ── operations: documents + attention ──

class TestDocumentsSummary:
    def test_overdue_collection_account_counts_and_alerts(self, collection_doc_type):
        today = today_bogota()
        _make_collection_account(
            collection_doc_type,
            due_date=today - timedelta(days=3), total=Decimal('500000'),
        )
        _make_collection_account(
            collection_doc_type,
            due_date=today + timedelta(days=10), total=Decimal('300000'),
        )

        payload = build_panel_dashboard(include_finance=False)

        accounts = payload['operations']['documents']['collection_accounts']
        assert accounts['issued_count'] == 2
        assert accounts['overdue_issued'] == 1
        assert accounts['outstanding_total'] == Decimal('800000')
        item = next(
            i for i in payload['attention'] if i['type'] == 'documents_overdue'
        )
        assert item['severity'] == 'danger'
        assert item['count'] == 1


# ── operations: emails ──

class TestEmailsSummary:
    def test_success_rate_and_failed_attention(self):
        for _ in range(3):
            EmailLog.objects.create(
                template_key='proposal_send', recipient='a@b.co', status='sent',
            )
        EmailLog.objects.create(
            template_key='proposal_send', recipient='a@b.co', status='failed',
        )

        payload = build_panel_dashboard(include_finance=False)

        emails = payload['operations']['emails']
        assert emails['total_30d'] == 4
        assert emails['failed_count'] == 1
        assert emails['success_rate'] == 75.0
        item = next(
            i for i in payload['attention'] if i['type'] == 'emails_failed'
        )
        assert item['count'] == 1


# ── operations: diagnostics ──

class TestDiagnosticsSummary:
    def test_pipeline_and_accepted_value(self):
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name='Cliente Diag', email='diag@example.com',
        )
        WebAppDiagnostic.objects.create(client=profile, status='sent')
        WebAppDiagnostic.objects.create(client=profile, status='negotiating')
        WebAppDiagnostic.objects.create(
            client=profile, status='accepted',
            investment_amount=Decimal('2000000'),
        )

        diagnostics = build_panel_dashboard(
            include_finance=False,
        )['operations']['diagnostics']

        assert diagnostics['active_pipeline'] == 2
        assert diagnostics['accepted_value'] == Decimal('2000000')


# ── attention: stale proposals ──

class TestStaleProposals:
    @freeze_time('2026-01-15 12:00:00')
    def test_sent_unviewed_over_seven_days_alerts(self):
        stale = BusinessProposal.objects.create(
            title='Olvidada', client_name='Cliente', status='sent',
        )
        BusinessProposal.objects.filter(pk=stale.pk).update(
            sent_at=timezone.now() - timedelta(days=8),
        )
        fresh = BusinessProposal.objects.create(
            title='Reciente', client_name='Cliente', status='sent',
        )
        BusinessProposal.objects.filter(pk=fresh.pk).update(
            sent_at=timezone.now() - timedelta(days=2),
        )

        attention = build_panel_dashboard(include_finance=False)['attention']

        item = next(i for i in attention if i['type'] == 'proposals_stale')
        assert item['count'] == 1
        assert item['severity'] == 'warning'


# ── attention: recurring due (finance-gated) ──

class TestRecurringDue:
    def test_due_soon_only_reported_with_finance(self):
        RecurringPayment.objects.create(
            name='Hosting', price=Decimal('50000.00'),
            cop_equivalent=Decimal('50000.00'), frequency='monthly',
            billing_day=today_bogota().day,
        )

        with_finance = build_panel_dashboard(include_finance=True)['attention']
        without_finance = build_panel_dashboard(include_finance=False)['attention']

        item = next(i for i in with_finance if i['type'] == 'recurring_due')
        assert item['count'] == 1
        assert item['meta']['next_days'] == 0
        assert all(i['type'] != 'recurring_due' for i in without_finance)


# ── _days_until_billing ──

class TestDaysUntilBilling:
    def test_same_month_upcoming_day(self):
        assert _days_until_billing(15, date(2026, 7, 10)) == 5

    def test_wraps_into_next_month(self):
        assert _days_until_billing(5, date(2026, 7, 10)) == 26

    def test_clamps_to_short_month_length(self):
        assert _days_until_billing(31, date(2026, 2, 10)) == 18


# ── build_dashboard core parity (refactor lock) ──

class TestDashboardCoreParity:
    def test_full_dashboard_contains_core_values(self):
        BusinessProposal.objects.create(
            title='Uno', client_name='Cliente', status='accepted',
            total_investment=Decimal('1000000'),
        )
        BusinessProposal.objects.create(
            title='Dos', client_name='Cliente', status='sent',
            total_investment=Decimal('2000000'),
        )

        core = build_dashboard_core(include_recent=False)
        full = build_dashboard()

        for key, value in core.items():
            assert full[key] == value
        assert 'recent' not in full

    def test_core_recent_lists_latest_proposals(self):
        for idx in range(6):
            BusinessProposal.objects.create(
                title=f'P{idx}', client_name='Cliente',
            )

        recent = build_dashboard_core()['recent']

        assert len(recent) == 5
        assert recent[0]['title'] == 'P5'
        assert set(recent[0]) == {'id', 'title', 'client_name', 'status'}
