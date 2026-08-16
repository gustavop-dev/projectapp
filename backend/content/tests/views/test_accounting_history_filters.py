"""The questions the Historial tab has to be able to answer.

Not "does the filter run" but the four things somebody actually walks up to
it with: did this client's notice go out, what has been sent about this
hosting, what failed today, and how many rows is each preset tab worth —
including the honest zero.
"""
from decimal import Decimal

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model

from content.models import (
    EmailBody,
    EmailLog,
    EmailLogTarget,
    HostingRecord,
    IncomeRecord,
)

User = get_user_model()
pytestmark = pytest.mark.django_db

SENDS = '/api/accounting/email-log/'
CHANGES = '/api/accounting/change-logs/'
COUNTS = '/api/accounting/history/tab-counts/'


def make_client(email, *, first='Ana'):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name='Pérez',
    )
    return UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)


def make_income(**overrides):
    fields = {
        'concept': 'Desarrollo módulo de reportes',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-08-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_log(template_key='accounting_change', targets=(), **kwargs):
    fields = {
        'recipient': 'ana@test.com',
        'subject': '[Contabilidad] Ingreso creado: Kore',
        'status': EmailLog.Status.SENT,
    }
    fields.update(kwargs)
    log = EmailLog.objects.create(template_key=template_key, **fields)
    for entity_type, object_id in targets:
        EmailLogTarget.objects.create(
            email_log=log, entity_type=entity_type, object_id=object_id,
        )
    return log


def recipients(response):
    return {row['recipient'] for row in response.data['results']}


class TestFilteringBySourceRecord:
    def test_narrows_to_the_emails_sent_about_one_record(self, super_client):
        hosting = HostingRecord.objects.create(
            client_name='Kore', monthly_value=Decimal('77760.00'),
        )
        other = HostingRecord.objects.create(
            client_name='Mimittos', monthly_value=Decimal('50000.00'),
        )
        make_log(recipient='suyo@test.com',
                 targets=[('hosting', hosting.pk)])
        make_log(recipient='ajeno@test.com', targets=[('hosting', other.pk)])

        response = super_client.get(
            f'{SENDS}?entity_type=hosting&object_id={hosting.pk}',
        )

        assert response.status_code == 200
        assert recipients(response) == {'suyo@test.com'}

    def test_a_digest_naming_the_record_many_times_is_listed_once(
        self, super_client,
    ):
        """The payment calendar links every record it mentions, and several
        of them can match the same filter."""
        first, second = make_income(), make_income(concept='Otro')
        make_log(
            'accounting_payment_calendar',
            targets=[('income', first.pk), ('income', second.pk)],
        )

        response = super_client.get(f'{SENDS}?entity_type=income')

        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

    def test_filters_by_client_across_incomes_and_hostings(self, super_client):
        client = make_client('kore@test.com')
        stranger = make_client('otro@test.com', first='Nés')
        income = make_income(client=client)
        hosting = HostingRecord.objects.create(
            client=client, client_name='Kore',
            monthly_value=Decimal('77760.00'),
        )
        theirs = make_income(client=stranger, concept='De otro')

        make_log(recipient='por-ingreso@test.com',
                 targets=[('income', income.pk)])
        make_log(recipient='por-hosting@test.com',
                 targets=[('hosting', hosting.pk)])
        make_log(recipient='de-otro@test.com', targets=[('income', theirs.pk)])

        response = super_client.get(f'{SENDS}?client={client.pk}')

        assert recipients(response) == {
            'por-ingreso@test.com', 'por-hosting@test.com',
        }

    def test_filters_by_project(self, super_client):
        client = make_client('kore@test.com')
        project = Project.objects.create(name='KORE', client=client.user)
        income = make_income(client=client, project=project)
        loose = make_income(client=client, concept='Sin proyecto')

        make_log(recipient='del-proyecto@test.com',
                 targets=[('income', income.pk)])
        make_log(recipient='suelto@test.com', targets=[('income', loose.pk)])

        response = super_client.get(f'{SENDS}?project={project.pk}')

        assert recipients(response) == {'del-proyecto@test.com'}

    def test_a_record_of_another_client_does_not_leak_through_the_type(
        self, super_client,
    ):
        """Client and record type describe one link, not two independent ones.

        Applied separately they would match an email that mentions some
        hosting and, unrelatedly, something of this client.
        """
        client = make_client('kore@test.com')
        income = make_income(client=client)
        foreign_hosting = HostingRecord.objects.create(
            client_name='Ajeno', monthly_value=Decimal('1000.00'),
        )
        make_log(
            'accounting_payment_calendar',
            recipient='mezclado@test.com',
            targets=[('income', income.pk), ('hosting', foreign_hosting.pk)],
        )

        response = super_client.get(
            f'{SENDS}?client={client.pk}&entity_type=hosting',
        )

        assert response.data['count'] == 0

    def test_rejects_a_non_numeric_record(self, super_client):
        assert super_client.get(f'{SENDS}?object_id=abc').status_code == 400


class TestFreeTextAndOriginFilters:
    def test_searches_the_subject(self, super_client):
        make_log(recipient='kore@test.com',
                 subject='[Contabilidad] Hosting creado: Kore')
        make_log(recipient='otro@test.com',
                 subject='[Contabilidad] Gasto creado: Dominios')

        response = super_client.get(f'{SENDS}?subject=hosting')

        assert recipients(response) == {'kore@test.com'}

    def test_isolates_the_notices_born_from_a_deletion(self, super_client):
        make_log(recipient='borrado@test.com', origin_action='deleted')
        make_log(recipient='creado@test.com', origin_action='created')

        response = super_client.get(f'{SENDS}?origin_action=deleted')

        assert recipients(response) == {'borrado@test.com'}

    def test_one_tab_can_span_several_notice_types(self, super_client):
        """"Recordatorios de cobro" covers the calendar and the cuentas."""
        make_log('accounting_payment_calendar', recipient='calendario@test.com')
        make_log('collection_account_sent', recipient='cuenta@test.com')
        make_log('accounting_card_reminder', recipient='tarjetas@test.com')

        response = super_client.get(
            f'{SENDS}?template_key=accounting_payment_calendar,'
            'collection_account_sent',
        )

        assert recipients(response) == {
            'calendario@test.com', 'cuenta@test.com',
        }


class TestSendRowContents:
    def test_exposes_the_records_the_email_was_about(self, super_client):
        hosting = HostingRecord.objects.create(
            client_name='Kore', monthly_value=Decimal('77760.00'),
        )
        log = make_log()
        EmailLogTarget.objects.create(
            email_log=log, entity_type='hosting', object_id=hosting.pk,
            object_repr='Kore',
        )

        row = super_client.get(SENDS).data['results'][0]

        assert row['targets'] == [{
            'entity_type': 'hosting',
            'entity_type_label': 'Hosting',
            'object_id': hosting.pk,
            'object_repr': 'Kore',
        }]

    def test_says_whether_the_message_itself_was_kept(self, super_client):
        body = EmailBody.objects.create(html='<p>Hola</p>', text='Hola')
        make_log(recipient='con@test.com', body=body)
        make_log(recipient='sin@test.com')

        rows = {r['recipient']: r for r in super_client.get(SENDS).data['results']}

        assert rows['con@test.com']['has_body'] is True
        assert rows['sin@test.com']['has_body'] is False

    def test_only_a_failed_single_record_notice_offers_a_retry(
        self, super_client,
    ):
        make_log(recipient='reintentable@test.com',
                 status=EmailLog.Status.FAILED)
        make_log('accounting_payment_calendar', recipient='digest@test.com',
                 status=EmailLog.Status.FAILED)
        make_log(recipient='ok@test.com')

        rows = {r['recipient']: r for r in super_client.get(SENDS).data['results']}

        assert rows['reintentable@test.com']['is_retryable'] is True
        assert rows['ok@test.com']['is_retryable'] is False
        digest = rows['digest@test.com']
        assert digest['is_retryable'] is False
        assert 'resumen' in digest['retry_blocked_reason']


class TestChangeLogFilters:
    def test_finds_the_record_by_name(self, super_client):
        from content.models import AccountingChangeLog

        AccountingChangeLog.objects.create(
            entity_type='hosting', object_id=1, object_repr='Kore SAS',
            action='updated',
        )
        AccountingChangeLog.objects.create(
            entity_type='hosting', object_id=2, object_repr='Mimittos',
            action='updated',
        )

        response = super_client.get(f'{CHANGES}?object_repr=kore')

        assert [r['object_repr'] for r in response.data['results']] == [
            'Kore SAS',
        ]

    def test_narrows_to_one_record(self, super_client):
        from content.models import AccountingChangeLog

        AccountingChangeLog.objects.create(
            entity_type='income', object_id=7, object_repr='Uno',
            action='created',
        )
        AccountingChangeLog.objects.create(
            entity_type='income', object_id=9, object_repr='Otro',
            action='created',
        )

        response = super_client.get(f'{CHANGES}?entity_type=income&object_id=7')

        assert [r['object_repr'] for r in response.data['results']] == ['Uno']


class TestTabCounts:
    def test_counts_each_tab_including_the_empty_one(self, super_client):
        make_log(recipient='falla@test.com', status=EmailLog.Status.FAILED)
        make_log(recipient='ok@test.com')

        response = super_client.post(COUNTS, {
            'scope': 'sends',
            'tabs': [
                {'id': 'all', 'filters': {}},
                {'id': 'failed', 'filters': {'status': ['failed']}},
                {'id': 'bounced', 'filters': {'status': ['bounced']}},
            ],
        }, format='json')

        assert response.status_code == 200
        assert response.data['counts'] == {'all': 2, 'failed': 1, 'bounced': 0}

    def test_counts_the_change_log_too(self, super_client):
        from content.models import AccountingChangeLog

        AccountingChangeLog.objects.create(
            entity_type='income', object_id=1, object_repr='Uno',
            action='deleted',
        )

        response = super_client.post(COUNTS, {
            'scope': 'changes',
            'tabs': [{'id': 'deleted', 'filters': {'action': ['deleted']}}],
        }, format='json')

        assert response.data['counts'] == {'deleted': 1}

    def test_ignores_filter_keys_a_tab_has_no_business_setting(
        self, super_client,
    ):
        """A stored tab must not become a way to query arbitrary columns."""
        make_log(recipient='ana@test.com')

        response = super_client.post(COUNTS, {
            'scope': 'sends',
            'tabs': [{'id': 'raro', 'filters': {'metadata': {'x': 1}}}],
        }, format='json')

        assert response.status_code == 200
        assert response.data['counts'] == {'raro': 1}

    def test_rejects_an_unknown_scope(self, super_client):
        response = super_client.post(
            COUNTS, {'scope': 'nope', 'tabs': [{'id': 'a', 'filters': {}}]},
            format='json',
        )
        assert response.status_code == 400

    def test_rejects_more_tabs_than_the_strip_can_hold(self, super_client):
        response = super_client.post(COUNTS, {
            'scope': 'sends',
            'tabs': [{'id': str(i), 'filters': {}} for i in range(25)],
        }, format='json')

        assert response.status_code == 400

    def test_is_superuser_only(self, admin_client):
        response = admin_client.post(
            COUNTS, {'scope': 'sends', 'tabs': []}, format='json',
        )
        assert response.status_code == 403


class TestChangesFilteredByClientAndProject:
    """The question a reassignment raises — "qué le pasó a ESTE cliente" —
    finally answerable on the audit trail, not just on the send log."""

    def test_narrows_the_trail_to_one_clients_records_and_projects(
        self, super_client,
    ):
        from content.models import AccountingChangeLog

        ana = make_client('ana@test.com')
        otro = make_client('otro@test.com', first='Otro')
        project = Project.objects.create(name='Kore Web', client=ana.user)
        mine = make_income(concept='Kore - Inicio', client=ana)
        foreign = make_income(concept='Ajeno', client=otro)
        for entity, object_id, repr_ in (
            ('income', mine.pk, 'Kore - Inicio'),
            ('income', foreign.pk, 'Ajeno'),
            ('project', project.pk, 'Kore Web'),
        ):
            AccountingChangeLog.objects.create(
                entity_type=entity, object_id=object_id,
                object_repr=repr_, action='updated',
            )

        response = super_client.get(f'{CHANGES}?client={ana.pk}')

        assert response.status_code == 200, response.data
        assert {row['object_repr'] for row in response.data['results']} == {
            'Kore - Inicio', 'Kore Web',
        }

    def test_narrows_the_trail_to_one_projects_rows(self, super_client):
        from content.models import AccountingChangeLog

        ana = make_client('ana@test.com')
        project = Project.objects.create(name='Kore Web', client=ana.user)
        linked = make_income(concept='Kore - Inicio', client=ana, project=project)
        make_income(concept='Suelto', client=ana)
        for entity, object_id, repr_ in (
            ('income', linked.pk, 'Kore - Inicio'),
            ('project', project.pk, 'Kore Web'),
        ):
            AccountingChangeLog.objects.create(
                entity_type=entity, object_id=object_id,
                object_repr=repr_, action='updated',
            )
        AccountingChangeLog.objects.create(
            entity_type='income',
            object_id=IncomeRecord.objects.get(concept='Suelto').pk,
            object_repr='Suelto', action='updated',
        )

        response = super_client.get(f'{CHANGES}?project={project.pk}')

        assert response.status_code == 200
        assert {row['object_repr'] for row in response.data['results']} == {
            'Kore - Inicio', 'Kore Web',
        }
