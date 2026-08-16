"""Bulk project assignment from the accounting lists: the project mirror of
bulk-assign-client.

Covers assigning, clearing with null, idempotent re-runs, the two 409
contracts (vanished ids and client mismatch — a stale plan never opens the
atomic block), the cascade to liquid children (which also travel in
``results`` so the panel can rebuild every touched row), and the audit
trail per record.
"""
from decimal import Decimal

import pytest
from accounts.models import Project

from content.models import AccountingChangeLog, HostingRecord, IncomeRecord

pytestmark = pytest.mark.django_db

EntityType = AccountingChangeLog.EntityType

INCOMES_URL = '/api/accounting/incomes/bulk-assign-project/'
HOSTINGS_URL = '/api/accounting/hostings/bulk-assign-project/'


def make_project(profile, name='Vastago'):
    return Project.objects.create(name=name, client=profile.user)


def make_income(profile, **overrides):
    fields = {
        'concept': 'Desarrollo Vastago',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-07-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
        'client': profile,
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_hosting(profile, **overrides):
    fields = {
        'client': profile,
        'client_name': 'Ana - Vastago',
        'monthly_value': Decimal('120000.00'),
    }
    fields.update(overrides)
    return HostingRecord.objects.create(**fields)


def audit_rows(entity_type, object_id):
    return AccountingChangeLog.objects.filter(
        entity_type=entity_type, object_id=object_id,
    )


class TestBulkAssignIncomeProject:
    def test_assigns_and_returns_the_updated_rows(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        income = make_income(profile)
        other = make_income(profile, concept='Vastago - Fase 2')

        response = super_client.post(
            INCOMES_URL,
            {'income_ids': [income.pk, other.pk], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['updated'] == 2
        assert {row['id'] for row in response.data['results']} == {
            income.pk, other.pk,
        }
        assert all(
            row['project'] == project.pk for row in response.data['results']
        )
        income.refresh_from_db()
        assert income.project_id == project.pk

    def test_null_clears_the_project_and_audits_the_removal(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        income = make_income(profile, project=project)

        response = super_client.post(
            INCOMES_URL, {'income_ids': [income.pk], 'project': None},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['updated'] == 1
        income.refresh_from_db()
        assert income.project_id is None
        row = audit_rows(EntityType.INCOME, income.pk).get()
        change = next(c for c in row.changes if c['field'] == 'project')
        assert change['old'] == project.name
        assert change['new'] == ''

    def test_rerunning_the_same_assignment_writes_nothing(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        income = make_income(profile, project=project)

        response = super_client.post(
            INCOMES_URL, {'income_ids': [income.pk], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['updated'] == 0
        assert audit_rows(EntityType.INCOME, income.pk).count() == 0

    def test_a_vanished_id_answers_409_and_writes_nothing(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        income = make_income(profile)

        response = super_client.post(
            INCOMES_URL,
            {'income_ids': [income.pk, 99999], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'records_not_found'
        assert response.data['missing_ids'] == [99999]
        income.refresh_from_db()
        assert income.project_id is None

    def test_a_foreign_or_clientless_record_answers_409_client_mismatch(
        self, super_client, make_client_profile,
    ):
        owner = make_client_profile()
        stranger = make_client_profile()
        project = make_project(owner)
        mine = make_income(owner)
        foreign = make_income(stranger, concept='Ajeno')
        clientless = make_income(None, concept='Suelto')

        response = super_client.post(
            INCOMES_URL,
            {
                'income_ids': [mine.pk, foreign.pk, clientless.pk],
                'project': project.pk,
            },
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'client_mismatch'
        assert response.data['mismatched_ids'] == sorted(
            [foreign.pk, clientless.pk],
        )
        mine.refresh_from_db()
        assert mine.project_id is None

    def test_clearing_skips_the_ownership_check(
        self, super_client, make_client_profile,
    ):
        """Rows of DIFFERENT clients can be cleared together: removing a
        link needs no owner."""
        owner = make_client_profile()
        stranger = make_client_profile()
        income = make_income(owner, project=make_project(owner))
        foreign = make_income(
            stranger, project=make_project(stranger, name='Otro'),
            concept='Ajeno',
        )

        response = super_client.post(
            INCOMES_URL,
            {'income_ids': [income.pk, foreign.pk], 'project': None},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['updated'] == 2

    def test_cascaded_liquid_children_travel_in_results(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        expected = make_income(profile)
        liquid = make_income(
            profile,
            kind=IncomeRecord.Kind.LIQUID,
            expected_income=expected,
            concept='Vastago (abono)',
        )

        response = super_client.post(
            INCOMES_URL, {'income_ids': [expected.pk], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['updated'] == 1
        assert {row['id'] for row in response.data['results']} == {
            expected.pk, liquid.pk,
        }
        liquid.refresh_from_db()
        assert liquid.project_id == project.pk
        assert audit_rows(EntityType.INCOME, liquid.pk).count() == 1


class TestBulkAssignHostingProject:
    def test_assigns_and_answers_the_bulk_contract(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile()
        project = make_project(profile)
        hosting = make_hosting(profile)

        response = super_client.post(
            HOSTINGS_URL, {'hosting_ids': [hosting.pk], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 200, response.data
        assert response.data['updated'] == 1
        assert response.data['results'][0]['project_name'] == project.name
        hosting.refresh_from_db()
        assert hosting.project_id == project.pk
        assert audit_rows(EntityType.HOSTING, hosting.pk).count() == 1

    def test_the_mismatch_contract_holds_for_hostings(
        self, super_client, make_client_profile,
    ):
        owner = make_client_profile()
        stranger = make_client_profile()
        project = make_project(owner)
        foreign = make_hosting(stranger)

        response = super_client.post(
            HOSTINGS_URL, {'hosting_ids': [foreign.pk], 'project': project.pk},
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'client_mismatch'
        foreign.refresh_from_db()
        assert foreign.project_id is None

    def test_requires_a_superuser(self, api_client):
        response = api_client.post(
            HOSTINGS_URL, {'hosting_ids': [1], 'project': None}, format='json',
        )

        assert response.status_code in (401, 403)
