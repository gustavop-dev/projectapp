import uuid
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import EmailBody, EmailLog


pytestmark = pytest.mark.django_db


def make_log(
    template_key,
    *,
    recipient='recipient@example.com',
    status=EmailLog.Status.SENT,
    audience=EmailLog.Audience.INTERNAL,
    body=None,
    delivery_id=None,
    delivery_role=EmailLog.DeliveryRole.PRIMARY,
):
    return EmailLog.objects.create(
        template_key=template_key,
        recipient=recipient,
        subject=f'Asunto {template_key}',
        status=status,
        audience=audience,
        body=body,
        delivery_id=delivery_id,
        delivery_role=delivery_role,
    )


def global_history(admin_client, params=None):
    return admin_client.get(
        reverse('list-standalone-emails'),
        {'scope': 'all', **(params or {})},
    )


def test_global_scope_includes_every_audience(admin_client):
    make_log('proposal_sent_client', audience=EmailLog.Audience.CLIENT)
    make_log('accounting_change', audience=EmailLog.Audience.INTERNAL)
    make_log('verification_code_onboarding', audience=EmailLog.Audience.SECURITY)

    response = global_history(admin_client)

    assert response.status_code == 200
    assert {row['audience'] for row in response.data['results']} == {
        'client', 'internal', 'security',
    }


def test_default_scope_preserves_standalone_history(admin_client):
    make_log('branded_email')
    make_log('accounting_change')

    response = admin_client.get(reverse('list-standalone-emails'))

    assert [row['template_key'] for row in response.data['results']] == [
        'branded_email',
    ]


def test_global_scope_nests_copy_attempt(admin_client):
    delivery_id = uuid.uuid4()
    primary = make_log('accounting_change', delivery_id=delivery_id)
    make_log(
        'accounting_change',
        recipient='audit@example.com',
        delivery_id=delivery_id,
        delivery_role=EmailLog.DeliveryRole.COPY,
    )

    response = global_history(admin_client)

    assert response.data['total'] == 1
    assert response.data['results'][0]['id'] == primary.pk
    assert response.data['results'][0]['copies'][0]['recipient'] == (
        'audit@example.com'
    )


def test_family_filter_returns_matching_channel(admin_client):
    make_log('proposal_sent_client')
    make_log('accounting_change')

    response = global_history(admin_client, {'family': 'accounting'})

    assert [row['template_key'] for row in response.data['results']] == [
        'accounting_change',
    ]


def test_recipient_filter_is_case_insensitive(admin_client):
    make_log('accounting_change', recipient='Carlos@example.com')
    make_log('accounting_change', recipient='other@example.com')

    response = global_history(admin_client, {'recipient': 'CARLOS'})

    assert [row['recipient'] for row in response.data['results']] == [
        'Carlos@example.com',
    ]


def test_status_filter_returns_failed_send(admin_client):
    make_log('accounting_change', status=EmailLog.Status.SENT)
    failed = make_log(
        'accounting_change',
        recipient='failed@example.com',
        status=EmailLog.Status.FAILED,
    )

    response = global_history(admin_client, {'status': 'failed'})

    assert [row['id'] for row in response.data['results']] == [failed.pk]


@freeze_time('2026-08-20 12:00:00')
def test_date_window_excludes_older_send(admin_client):
    """Falla si el filtro diario incluye un envío de una fecha anterior."""
    old = make_log('accounting_change', recipient='old@example.com')
    EmailLog.objects.filter(pk=old.pk).update(
        sent_at=timezone.now() - timedelta(days=10),
    )
    current = make_log('accounting_change', recipient='today@example.com')

    response = global_history(
        admin_client,
        {'date_from': '2026-08-20', 'date_to': '2026-08-20'},
    )

    assert [row['id'] for row in response.data['results']] == [current.pk]


def test_admin_can_read_security_email_body(admin_client):
    body = EmailBody.objects.create(
        text='Tu código es 123456',
        html='<p>Tu código es <strong>123456</strong></p>',
    )
    log = make_log(
        'verification_code_onboarding',
        audience=EmailLog.Audience.SECURITY,
        body=body,
    )

    response = admin_client.get(reverse(
        'standalone-email-body',
        kwargs={'log_id': log.pk},
    ))

    assert response.status_code == 200
    assert response.data['text'] == 'Tu código es 123456'
    assert '123456' in response.data['html']


def test_anonymous_user_cannot_read_email_body(api_client):
    log = make_log('verification_code_onboarding')

    response = api_client.get(reverse(
        'standalone-email-body',
        kwargs={'log_id': log.pk},
    ))

    assert response.status_code in (401, 403)
