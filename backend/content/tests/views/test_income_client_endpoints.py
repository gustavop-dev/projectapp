"""Income client/origin filters and the bulk client-assignment endpoint."""
from decimal import Decimal

import pytest

from accounts.services.proposal_client_service import build_client_display_name
from content.models import AccountingChangeLog, IncomeRecord

pytestmark = pytest.mark.django_db

BULK_URL = '/api/accounting/incomes/bulk-assign-client/'


def _ids(response):
    return {row['id'] for row in response.data['results']}


class TestClientFilter:
    def test_filters_by_client_id(self, super_client, make_income, make_client_profile):
        acme = make_client_profile(company='Acme SAS')
        globex = make_client_profile(company='Globex')
        mine = make_income(concept='Acme - Inicio', client=acme)
        make_income(concept='Globex - Inicio', client=globex)
        make_income(concept='Sin cliente')

        response = super_client.get(f'/api/accounting/incomes/?client={acme.pk}')

        assert response.status_code == 200
        assert _ids(response) == {mine.pk}

    def test_client_none_isolates_the_unassigned_group(
        self, super_client, make_income, make_client_profile,
    ):
        make_income(concept='Acme - Inicio', client=make_client_profile())
        orphan = make_income(concept='Reembolso banco')

        response = super_client.get('/api/accounting/incomes/?client=none')

        assert _ids(response) == {orphan.pk}

    def test_client_all_and_blank_do_not_filter(
        self, super_client, make_income, make_client_profile,
    ):
        make_income(concept='Acme - Inicio', client=make_client_profile())
        make_income(concept='Reembolso banco')

        assert len(super_client.get('/api/accounting/incomes/?client=all').data['results']) == 2
        assert len(super_client.get('/api/accounting/incomes/?client=').data['results']) == 2

    def test_several_client_ids_filter_as_or(
        self, super_client, make_income, make_client_profile,
    ):
        acme = make_client_profile(company='Acme SAS')
        globex = make_client_profile(company='Globex')
        first = make_income(concept='Acme - Inicio', client=acme)
        second = make_income(concept='Globex - Inicio', client=globex)
        make_income(concept='Sin cliente')

        response = super_client.get(
            f'/api/accounting/incomes/?client={acme.pk},{globex.pk}',
        )

        assert _ids(response) == {first.pk, second.pk}

    def test_invalid_client_param_returns_400(self, super_client):
        response = super_client.get('/api/accounting/incomes/?client=abc')

        assert response.status_code == 400
        assert 'client' in response.data['error']

    def test_export_applies_the_same_client_filter(
        self, super_client, make_income, make_client_profile,
    ):
        acme = make_client_profile(company='Acme SAS')
        make_income(concept='Acme - Inicio', client=acme)
        make_income(concept='Reembolso banco')

        response = super_client.get(
            f'/api/accounting/export/?section=income&client={acme.pk}',
        )

        body = response.content.decode('utf-8-sig')
        assert 'Acme - Inicio' in body
        assert 'Reembolso banco' not in body
        # Appended columns: the header keeps its first five in place and the
        # client rides along in the same row, under its display name.
        assert body.splitlines()[0].endswith('Cliente,Origen,Proyecto')
        assert build_client_display_name(acme) in body


class TestOriginFilter:
    def test_filters_by_origin_and_supports_multi_value(
        self, super_client, make_income,
    ):
        dev = make_income(concept='Kore', origin=IncomeRecord.Origin.DEVELOPMENT)
        hosting = make_income(concept='Hosting Kore', origin=IncomeRecord.Origin.HOSTING)
        make_income(concept='Sin clasificar')

        single = super_client.get('/api/accounting/incomes/?origin=development')
        multi = super_client.get(
            '/api/accounting/incomes/?origin=development,hosting',
        )

        assert _ids(single) == {dev.pk}
        assert _ids(multi) == {dev.pk, hosting.pk}

    def test_origin_none_isolates_the_unclassified_group(
        self, super_client, make_income,
    ):
        """Fails (silently, zero rows) if 'none' stops isolating blank-origin rows."""
        dev = make_income(concept='Kore', origin=IncomeRecord.Origin.DEVELOPMENT)
        unclassified = make_income(concept='Sin clasificar')

        none_only = super_client.get('/api/accounting/incomes/?origin=none')
        dev_only = super_client.get('/api/accounting/incomes/?origin=development')

        assert _ids(none_only) == {unclassified.pk}
        assert _ids(dev_only) == {dev.pk}

    def test_origin_label_is_exposed(self, super_client, make_income):
        make_income(concept='Kore', origin=IncomeRecord.Origin.DIAGNOSTIC)

        row = super_client.get('/api/accounting/incomes/').data['results'][0]

        assert row['origin'] == 'diagnostic'
        assert row['origin_label'] == 'Diagnóstico'


class TestClientNameExposure:
    def test_client_name_uses_the_display_name_and_is_null_when_absent(
        self, super_client, make_income, make_client_profile,
    ):
        linked = make_income(concept='Acme - Inicio', client=make_client_profile())
        bare = make_income(concept='Reembolso banco')

        rows = {row['id']: row for row in super_client.get('/api/accounting/incomes/').data['results']}

        assert rows[linked.pk]['client_name']
        assert rows[bare.pk]['client_name'] is None
        assert rows[bare.pk]['client'] is None


class TestBulkAssignClient:
    def test_assigns_the_client_to_every_selected_income(
        self, super_client, make_income, make_client_profile,
    ):
        profile = make_client_profile(company='Acme SAS')
        first = make_income(concept='Acme - Inicio')
        second = make_income(concept='Acme - Entrega')
        untouched = make_income(concept='Otro ingreso')

        response = super_client.post(
            BULK_URL,
            {'income_ids': [first.pk, second.pk], 'client': profile.pk},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['updated'] == 2
        first.refresh_from_db()
        second.refresh_from_db()
        untouched.refresh_from_db()
        assert first.client_id == profile.pk
        assert second.client_id == profile.pk
        assert untouched.client_id is None

    def test_writes_one_audit_row_per_income(
        self, super_client, make_income, make_client_profile,
    ):
        profile = make_client_profile()
        first = make_income(concept='Acme - Inicio')
        second = make_income(concept='Acme - Entrega')

        super_client.post(
            BULK_URL,
            {'income_ids': [first.pk, second.pk], 'client': profile.pk},
            format='json',
        )

        logs = AccountingChangeLog.objects.filter(
            entity_type=AccountingChangeLog.EntityType.INCOME,
            action=AccountingChangeLog.Action.UPDATED,
        )
        assert logs.count() == 2
        assert {log.object_id for log in logs} == {first.pk, second.pk}
        assert any(
            change['field'] == 'client' for change in logs.first().changes
        )

    def test_null_client_unlinks(
        self, super_client, make_income, make_client_profile,
    ):
        income = make_income(concept='Acme - Inicio', client=make_client_profile())

        response = super_client.post(
            BULK_URL, {'income_ids': [income.pk], 'client': None}, format='json',
        )

        assert response.data['updated'] == 1
        income.refresh_from_db()
        assert income.client_id is None

    def test_reassigning_the_same_client_is_a_no_op(
        self, super_client, make_income, make_client_profile,
    ):
        profile = make_client_profile()
        income = make_income(concept='Acme - Inicio', client=profile)

        response = super_client.post(
            BULK_URL, {'income_ids': [income.pk], 'client': profile.pk},
            format='json',
        )

        assert response.data['updated'] == 0
        assert not AccountingChangeLog.objects.filter(
            action=AccountingChangeLog.Action.UPDATED,
        ).exists()

    def test_unknown_ids_are_rejected_and_nothing_is_written(
        self, super_client, make_income, make_client_profile,
    ):
        # A mass edit is confirmed against a named scope, so a vanished row
        # aborts the whole batch instead of quietly writing the rest.
        profile = make_client_profile()
        income = make_income(concept='Acme - Inicio')

        response = super_client.post(
            BULK_URL,
            {'income_ids': [income.pk, 999999], 'client': profile.pk},
            format='json',
        )

        assert response.status_code == 409
        assert response.data['code'] == 'records_not_found'
        assert response.data['missing_ids'] == [999999]
        income.refresh_from_db()
        assert income.client_id is None
        assert not AccountingChangeLog.objects.filter(
            action=AccountingChangeLog.Action.UPDATED,
        ).exists()

    def test_the_error_names_every_missing_id(
        self, super_client, make_income, make_client_profile,
    ):
        profile = make_client_profile()
        income = make_income(concept='Acme - Inicio')

        response = super_client.post(
            BULK_URL,
            {'income_ids': [income.pk, 999998, 999999], 'client': profile.pk},
            format='json',
        )

        assert response.data['missing_ids'] == [999998, 999999]
        assert '2 de los ingresos seleccionados ya no existen' in response.data['error']

    def test_unlinking_is_held_to_the_same_contract(
        self, super_client, make_income, make_client_profile,
    ):
        # The check runs before `client` is read, so clearing it is covered
        # by the same guard as assigning.
        income = make_income(concept='Acme - Inicio', client=make_client_profile())

        response = super_client.post(
            BULK_URL,
            {'income_ids': [income.pk, 999999], 'client': None},
            format='json',
        )

        assert response.status_code == 409
        income.refresh_from_db()
        assert income.client_id is not None

    def test_empty_id_list_is_rejected(self, super_client, make_client_profile):
        response = super_client.post(
            BULK_URL,
            {'income_ids': [], 'client': make_client_profile().pk},
            format='json',
        )

        assert response.status_code == 400

    def test_requires_superuser(self, admin_client, make_income, make_client_profile):
        income = make_income(concept='Acme - Inicio')

        response = admin_client.post(
            BULK_URL,
            {'income_ids': [income.pk], 'client': make_client_profile().pk},
            format='json',
        )

        assert response.status_code == 403


class TestSerializerWrites:
    def test_create_and_patch_accept_client_and_origin(
        self, super_client, make_client_profile,
    ):
        profile = make_client_profile(company='Acme SAS')

        created = super_client.post(
            '/api/accounting/incomes/create/',
            {
                'concept': 'Acme - Inicio 40%',
                'kind': 'expected',
                'period_date': '2026-08',
                'total_amount': '1000000.00',
                'client': profile.pk,
                'origin': 'development',
            },
            format='json',
        )

        assert created.status_code == 201, created.data
        assert created.data['client'] == profile.pk
        assert created.data['origin'] == 'development'

        patched = super_client.patch(
            f"/api/accounting/incomes/{created.data['id']}/update/",
            {'client': None},
            format='json',
        )

        assert patched.status_code == 200
        assert patched.data['client'] is None

    def test_a_non_client_profile_is_rejected(self, super_client, django_user_model):
        from accounts.models import UserProfile

        staff = django_user_model.objects.create_user(
            username='staffer@example.com', email='staffer@example.com',
        )
        admin_profile = UserProfile.objects.create(
            user=staff, role=UserProfile.ROLE_ADMIN,
        )

        response = super_client.post(
            '/api/accounting/incomes/create/',
            {
                'concept': 'Acme - Inicio 40%',
                'kind': 'expected',
                'period_date': '2026-08',
                'total_amount': '1000000.00',
                'client': admin_profile.pk,
            },
            format='json',
        )

        assert response.status_code == 400
        assert 'client' in response.data


class TestClientNameSearch:
    def test_q_reaches_the_linked_client_name_and_company(
        self, super_client, make_income, make_client_profile,
    ):
        """Fails if `q` stops walking the client's name/company (concept-only)."""
        deivis = make_client_profile(
            company='Vastago SAS', first_name='Deivis', last_name='Rios',
        )
        mine = make_income(concept='Cuota 1/12', client=deivis)
        make_income(concept='Reembolso banco')

        by_company = super_client.get('/api/accounting/incomes/?q=vastago')
        by_first_name = super_client.get('/api/accounting/incomes/?q=deivis')

        assert _ids(by_company) == {mine.pk}
        assert _ids(by_first_name) == {mine.pk}


class TestWithoutClientMeta:
    def test_counts_unassigned_rows_across_the_whole_filtered_set(
        self, super_client, make_income, make_client_profile,
    ):
        """The completion-debt KPI must see legacy rows outside the KPI year."""
        from datetime import date

        acme = make_client_profile()
        make_income(concept='Con cliente', client=acme)
        make_income(concept='Huérfano actual')
        make_income(concept='Huérfano viejo', period_date=date(2020, 5, 1))

        unfiltered = super_client.get('/api/accounting/incomes/')
        assert unfiltered.data['meta']['without_client_count'] == 2

        # The count follows the active filters, like the rest of the meta.
        filtered = super_client.get(f'/api/accounting/incomes/?client={acme.pk}')
        assert filtered.data['meta']['without_client_count'] == 0


class TestClientCascadeToLiquids:
    def test_bulk_assign_cascades_to_the_settled_liquids(
        self, super_client, make_income, make_client_profile,
    ):
        """Reassigning the expected must carry the money already collected."""
        acme = make_client_profile(company='Acme SAS')
        expected = make_income(concept='Kore - Inicio', kind='expected')
        liquid = make_income(
            concept='Kore - Inicio', kind='liquid', expected_income=expected,
        )

        response = super_client.post(
            BULK_URL,
            {'income_ids': [expected.pk], 'client': acme.pk},
            format='json',
        )

        assert response.status_code == 200, response.data
        liquid.refresh_from_db()
        assert liquid.client_id == acme.pk
        # One audit row per touched record: the child keeps its own history.
        assert AccountingChangeLog.objects.filter(
            entity_type='income', object_id=liquid.pk, action='updated',
        ).exists()

    def test_update_endpoint_cascades_too(
        self, super_client, make_income, make_client_profile,
    ):
        acme = make_client_profile(company='Acme SAS')
        expected = make_income(concept='Kore - Inicio', kind='expected')
        liquid = make_income(
            concept='Kore - Inicio', kind='liquid', expected_income=expected,
        )

        response = super_client.patch(
            f'/api/accounting/incomes/{expected.pk}/update/',
            {'client': acme.pk},
            format='json',
        )

        assert response.status_code == 200, response.data
        liquid.refresh_from_db()
        assert liquid.client_id == acme.pk
