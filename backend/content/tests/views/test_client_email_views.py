"""The per-client email history behind the Emails module of /panel/clients.

Three endpoints nested under the client, where the nesting is what
authorizes the row: list (paginated, split by audience), body, and retry.
"""

import pytest
from django.urls import reverse

from content.models import EmailBody, EmailLog

pytestmark = pytest.mark.django_db


def make_log(profile, **kwargs):
    defaults = {
        'template_key': 'collection_account_sent',
        'recipient': 'ana@example.com',
        'subject': 'Cuenta de cobro',
        'status': EmailLog.Status.SENT,
        'audience': EmailLog.Audience.CLIENT,
        'client': profile,
    }
    defaults.update(kwargs)
    return EmailLog.objects.create(**defaults)


def list_url(profile):
    return reverse('list-client-emails', args=[profile.pk])


class TestListClientEmails:

    def test_it_lists_what_is_filed_under_this_client(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        make_log(profile)

        response = admin_client.get(list_url(profile))

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['subject'] == 'Cuenta de cobro'

    def test_another_clients_email_is_not_listed(
        self, admin_client, make_client_profile,
    ):
        owner = make_client_profile(company='Dueno SAS')
        stranger = make_client_profile(company='Ajeno SAS')
        make_log(owner)

        response = admin_client.get(list_url(stranger))

        assert response.data['count'] == 0

    def test_the_audience_param_splits_the_two_groups(
        self, admin_client, make_client_profile,
    ):
        """What the modal's segmented control asks for. Server-side because
        the list paginates: counting one loaded page would lie."""
        profile = make_client_profile()
        make_log(profile)
        make_log(
            profile, template_key='accounting_change',
            audience=EmailLog.Audience.INTERNAL, subject='Cambio contable',
        )

        both = admin_client.get(list_url(profile))
        to_client = admin_client.get(list_url(profile), {'audience': 'client'})
        internal = admin_client.get(list_url(profile), {'audience': 'internal'})

        assert both.data['count'] == 2
        assert to_client.data['count'] == 1
        assert internal.data['count'] == 1
        assert internal.data['results'][0]['subject'] == 'Cambio contable'

    def test_an_unknown_audience_is_ignored_rather_than_rejected(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        make_log(profile)

        response = admin_client.get(list_url(profile), {'audience': 'ruido'})

        assert response.data['count'] == 1

    def test_rows_sent_in_the_same_instant_keep_a_stable_order(
        self, admin_client, make_client_profile,
    ):
        """sent_at is auto_now_add, so one multi-recipient send writes several
        rows at the same timestamp; without the -id tiebreaker pagination
        could repeat or skip one."""
        profile = make_client_profile()
        first = make_log(profile)
        second = make_log(profile)

        response = admin_client.get(list_url(profile))

        ids = [row['id'] for row in response.data['results']]
        assert ids == [second.id, first.id]

    def test_it_names_the_notice_of_a_proposal_send(
        self, admin_client, make_client_profile,
    ):
        """EMAIL_TEMPLATE_LABELS only knows the six accounting notices, so
        without the fallback this column would show raw snake_case."""
        profile = make_client_profile()
        make_log(profile, template_key='magic_link', subject='Acceso')

        response = admin_client.get(list_url(profile))

        assert response.data['results'][0]['template_label'] == 'Acceso directo'

    def test_an_unknown_client_is_a_404(self, admin_client):
        response = admin_client.get(reverse('list-client-emails', args=[999999]))

        assert response.status_code == 404

    def test_it_requires_an_admin(self, client, make_client_profile):
        profile = make_client_profile()

        response = client.get(list_url(profile))

        assert response.status_code in (401, 403)


class TestClientEmailBody:

    def test_it_returns_the_message_as_delivered(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        body = EmailBody.objects.create(html='<p>Hola</p>', text='Hola')
        log = make_log(profile, body=body)

        response = admin_client.get(
            reverse('client-email-body', args=[profile.pk, log.pk]),
        )

        assert response.status_code == 200
        assert response.data['html'] == '<p>Hola</p>'

    def test_a_send_from_before_bodies_were_stored_says_so(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        log = make_log(profile)

        response = admin_client.get(
            reverse('client-email-body', args=[profile.pk, log.pk]),
        )

        assert response.status_code == 404
        assert response.data['code'] == 'body_not_stored'

    def test_another_clients_body_is_not_readable(
        self, admin_client, make_client_profile,
    ):
        """The nesting is the authorization: no separate check to forget."""
        owner = make_client_profile(company='Dueno SAS')
        stranger = make_client_profile(company='Ajeno SAS')
        body = EmailBody.objects.create(html='<p>Privado</p>', text='Privado')
        log = make_log(owner, body=body)

        response = admin_client.get(
            reverse('client-email-body', args=[stranger.pk, log.pk]),
        )

        assert response.status_code == 404


class TestRetryClientEmail:

    def test_a_send_that_worked_is_not_retried(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        log = make_log(profile)

        response = admin_client.post(
            reverse('retry-client-email', args=[profile.pk, log.pk]),
        )

        assert response.status_code == 400
        assert 'fallaron' in response.data['error']

    def test_a_failed_proposal_send_explains_where_to_resend_it(
        self, admin_client, make_client_profile,
    ):
        """It must not be told it 'resume varios registros del día' — that is
        the digests' reason, and this is a proposal."""
        profile = make_client_profile()
        log = make_log(
            profile, template_key='proposal_sent_client',
            status=EmailLog.Status.FAILED,
        )

        response = admin_client.post(
            reverse('retry-client-email', args=[profile.pk, log.pk]),
        )

        assert response.status_code == 400
        assert 'propuesta' in response.data['error']

    def test_a_failed_digest_keeps_the_digest_reason(
        self, admin_client, make_client_profile,
    ):
        profile = make_client_profile()
        log = make_log(
            profile, template_key='accounting_payment_calendar',
            audience=EmailLog.Audience.INTERNAL,
            status=EmailLog.Status.FAILED,
        )

        response = admin_client.post(
            reverse('retry-client-email', args=[profile.pk, log.pk]),
        )

        assert response.status_code == 400
        assert 'resume varios registros' in response.data['error']

    def test_another_clients_send_cannot_be_retried_from_here(
        self, admin_client, make_client_profile,
    ):
        owner = make_client_profile(company='Dueno SAS')
        stranger = make_client_profile(company='Ajeno SAS')
        log = make_log(owner, status=EmailLog.Status.FAILED)

        response = admin_client.post(
            reverse('retry-client-email', args=[stranger.pk, log.pk]),
        )

        assert response.status_code == 404
