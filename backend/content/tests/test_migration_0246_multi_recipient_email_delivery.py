import uuid
from importlib import import_module

import pytest
from django.apps import apps

from content.models import EmailBody, EmailDeliverySnapshot, EmailLog


pytestmark = pytest.mark.django_db
migration = import_module('content.migrations.0246_multi_recipient_email_delivery')


def test_backfill_recovers_existing_delivery_headers():
    delivery_id = uuid.uuid4()
    body = EmailBody.objects.create(text='Texto', html='<p>Texto</p>')
    snapshot = EmailDeliverySnapshot.objects.create(
        delivery_id=delivery_id,
        template_key='branded_email',
        classification='client',
        family='proposals',
        body=body,
    )
    EmailLog.objects.create(
        template_key='branded_email',
        recipient='cliente@example.com',
        delivery_id=delivery_id,
        delivery_role=EmailLog.DeliveryRole.PRIMARY,
    )
    copy_log = EmailLog.objects.create(
        template_key='branded_email',
        recipient='auditoria@example.com',
        delivery_id=delivery_id,
        delivery_role=EmailLog.DeliveryRole.COPY,
    )

    migration.backfill_recipient_headers(apps, None)

    snapshot.refresh_from_db()
    copy_log.refresh_from_db()
    assert snapshot.to_recipients == ['cliente@example.com']
    assert snapshot.cc_recipients == []
    assert copy_log.recipient_kind == EmailLog.RecipientKind.BCC
