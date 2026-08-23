from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.exceptions import ValidationError

from content.email_copy_families import COLLECTIONS, PROPOSALS
from content.models import ClientEmailCopyRecipient, EmailBody, EmailLog
from content.services import email_log_service
from content.services.email_delivery_service import (
    DeliveryClassification,
    EmailDeliveryGateway,
    EmailMultiAlternatives,
)
from content.serializers.accounting import EmailLogSerializer


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def locmem_email_backend(settings):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    mail.outbox = []


def build_message(recipient='client@example.com'):
    message = EmailMultiAlternatives(
        subject='Propuesta ProjectApp',
        body='Versión de texto',
        from_email='team@projectapp.co',
        to=[recipient],
    )
    message.attach_alternative('<p>Versión HTML</p>', 'text/html')
    message.attach('alcance.txt', b'contenido', 'text/plain')
    return message


def record_primary(recipient='client@example.com'):
    return email_log_service.record_send(
        template_key='proposal_sent_client',
        recipients=[recipient],
        subject='Propuesta ProjectApp',
        status=EmailLog.Status.SENT,
        html_body='<p>Versión HTML</p>',
        text_body='Versión de texto',
        audience=EmailLog.Audience.CLIENT,
    )[0]


def test_client_delivery_uses_hidden_copy_envelope():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    result = EmailDeliveryGateway.send(
        message, template_key='proposal_sent_client',
    )

    assert result == 1
    assert len(mail.outbox) == 2
    assert mail.outbox[0].to == ['client@example.com']
    assert mail.outbox[0].bcc == []
    assert mail.outbox[1].to == []
    assert mail.outbox[1].bcc == ['audit@example.com']


def test_client_copy_preserves_rendered_content():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')

    primary, copy_message = mail.outbox
    assert copy_message.subject == primary.subject
    assert copy_message.body == primary.body
    assert copy_message.alternatives == primary.alternatives
    assert copy_message.attachments == primary.attachments


def test_primary_failure_skips_internal_copy():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    with patch(
        'content.services.email_delivery_service.EmailMessage.send',
        side_effect=SMTPException('primary unavailable'),
    ) as smtp_send:
        with pytest.raises(SMTPException, match='primary unavailable'):
            EmailDeliveryGateway.send(
                message, template_key='proposal_sent_client',
            )

    assert smtp_send.call_count == 1
    assert EmailLog.objects.count() == 0


def test_copy_failure_preserves_primary_status():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    with patch(
        'content.services.email_delivery_service.EmailMessage.send',
        side_effect=[1, SMTPException('copy unavailable')],
    ):
        result = EmailDeliveryGateway.send(
            message, template_key='proposal_sent_client',
        )
    primary = record_primary()

    copy_log = EmailLog.objects.get(delivery_role=EmailLog.DeliveryRole.COPY)
    assert result == 1
    assert primary.status == EmailLog.Status.SENT
    assert copy_log.status == EmailLog.Status.FAILED
    assert copy_log.error_message == 'copy unavailable'


def test_copy_history_shares_delivery_body():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')
    primary = record_primary()
    copy_log = EmailLog.objects.get(delivery_role=EmailLog.DeliveryRole.COPY)

    assert primary.delivery_id == copy_log.delivery_id
    assert primary.body_id == copy_log.body_id
    assert EmailBody.objects.count() == 1


def test_primary_serializer_exposes_copy_attempt():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')
    primary = record_primary()

    assert EmailLogSerializer(primary).data['copies'][0]['recipient'] == (
        'audit@example.com'
    )


def test_nonmatching_family_skips_copy():
    ClientEmailCopyRecipient.objects.create(
        email='billing@example.com', families=[COLLECTIONS],
    )
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')

    assert len(mail.outbox) == 1


def test_security_delivery_skips_copy():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    EmailDeliveryGateway.send(
        message,
        template_key='verification_code_onboarding',
        classification=DeliveryClassification.SECURITY,
    )

    assert len(mail.outbox) == 1


def test_unregistered_delivery_requires_explicit_policy():
    message = build_message()

    with pytest.raises(ValueError, match='Email policy required'):
        EmailDeliveryGateway.send(message, template_key='future_email')


def test_unregistered_client_policy_is_rejected():
    message = build_message()

    with pytest.raises(ValueError, match='missing from the inventory'):
        EmailDeliveryGateway.send(
            message,
            template_key='future_email',
            classification=DeliveryClassification.CLIENT,
        )


def test_copy_recipient_lookup_failure_preserves_primary():
    message = build_message()

    with patch(
        'content.services.email_delivery_service._active_copy_recipients',
        side_effect=RuntimeError('configuration unavailable'),
    ):
        result = EmailDeliveryGateway.send(
            message, template_key='proposal_sent_client',
        )

    assert result == 1
    assert len(mail.outbox) == 1


def test_inactive_recipient_is_not_copied():
    ClientEmailCopyRecipient.objects.create(
        email='paused@example.com', is_active=False,
    )
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')

    assert len(mail.outbox) == 1


def test_primary_recipient_is_not_copied_twice():
    ClientEmailCopyRecipient.objects.create(email='CLIENT@example.com')
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')

    assert len(mail.outbox) == 1


def test_multiple_copy_recipients_create_independent_attempts():
    ClientEmailCopyRecipient.objects.create(email='audit-a@example.com')
    ClientEmailCopyRecipient.objects.create(email='audit-b@example.com')
    message = build_message()

    EmailDeliveryGateway.send(message, template_key='proposal_sent_client')
    record_primary()

    assert len(mail.outbox) == 3
    assert EmailLog.objects.filter(
        delivery_role=EmailLog.DeliveryRole.COPY,
    ).count() == 2


def test_multi_log_delivery_records_single_copy():
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')
    message = build_message()

    EmailDeliveryGateway.send(
        message,
        template_key='proposal_multi_sent_client',
        primary_log_writes=2,
    )
    first = email_log_service.record_send(
        template_key='proposal_multi_sent_client',
        recipients=['client@example.com'],
        subject='Propuesta ProjectApp',
        status=EmailLog.Status.SENT,
        html_body='<p>Versión HTML</p>',
        text_body='Versión de texto',
        audience=EmailLog.Audience.CLIENT,
    )[0]
    second = email_log_service.record_send(
        template_key='proposal_multi_sent_client',
        recipients=['client@example.com'],
        subject='Propuesta ProjectApp',
        status=EmailLog.Status.SENT,
        audience=EmailLog.Audience.CLIENT,
    )[0]

    assert first.delivery_id == second.delivery_id
    assert EmailLog.objects.filter(
        delivery_role=EmailLog.DeliveryRole.COPY,
    ).count() == 1


def test_active_recipient_requires_selected_family():
    recipient = ClientEmailCopyRecipient(
        email='audit@example.com', is_active=True, families=[],
    )

    with pytest.raises(ValidationError, match='al menos una familia'):
        recipient.full_clean()


def test_model_normalizes_email_case():
    recipient = ClientEmailCopyRecipient.objects.create(
        email=' Audit@Example.COM ', families=[PROPOSALS],
    )

    assert recipient.email == 'audit@example.com'
