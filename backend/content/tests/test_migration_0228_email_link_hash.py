import hashlib
import uuid
from importlib import import_module

import pytest
from django.apps import apps

from content.models import EmailBody, EmailDeliverySnapshot, EmailLinkSnapshot


migration = import_module('content.migrations.0228_emaillinksnapshot_url_sha256')


@pytest.mark.django_db
def test_url_hash_migration_populates_an_existing_link():
    body = EmailBody.objects.create(text='Existing snapshot body')
    snapshot = EmailDeliverySnapshot.objects.create(
        delivery_id=uuid.uuid4(),
        template_key='migration_backfill',
        classification=EmailDeliverySnapshot.Classification.INTERNAL,
        body=body,
    )
    link = EmailLinkSnapshot.objects.create(
        snapshot=snapshot,
        url='https://example.com/existing',
    )
    EmailLinkSnapshot.objects.filter(pk=link.pk).update(url_sha256='')

    migration.populate_url_sha256(apps, None)
    link.refresh_from_db()

    expected = hashlib.sha256(link.url.encode('utf-8')).hexdigest()
    assert link.url_sha256 == expected
