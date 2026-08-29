import hashlib
import uuid

import pytest
from django.db import IntegrityError, transaction

from content.models import EmailBody, EmailDeliverySnapshot, EmailLinkSnapshot


pytestmark = pytest.mark.django_db


@pytest.fixture
def delivery_snapshot():
    body = EmailBody.objects.create(text='Snapshot body')
    return EmailDeliverySnapshot.objects.create(
        delivery_id=uuid.uuid4(),
        template_key='migration_regression',
        classification=EmailDeliverySnapshot.Classification.INTERNAL,
        body=body,
    )


def test_link_snapshot_hashes_a_max_length_url(delivery_snapshot):
    prefix = 'https://example.com/'
    url = prefix + ('a' * (2048 - len(prefix)))

    link = EmailLinkSnapshot.objects.create(
        snapshot=delivery_snapshot,
        url=url,
    )

    assert link.url == url
    assert link.url_sha256 == hashlib.sha256(url.encode('utf-8')).hexdigest()


def test_link_snapshot_rejects_a_repeated_url(delivery_snapshot):
    url = 'https://example.com/evidence'
    EmailLinkSnapshot.objects.create(snapshot=delivery_snapshot, url=url)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EmailLinkSnapshot.objects.create(snapshot=delivery_snapshot, url=url)


def test_link_snapshot_rehashes_an_updated_url(delivery_snapshot):
    link = EmailLinkSnapshot.objects.create(
        snapshot=delivery_snapshot,
        url='https://example.com/original',
    )

    link.url = 'https://example.com/revised'
    link.save(update_fields={'url'})
    link.refresh_from_db()

    expected = hashlib.sha256(link.url.encode('utf-8')).hexdigest()
    assert link.url_sha256 == expected


def test_link_snapshot_unique_key_fits_mysql_utf8mb4(delivery_snapshot):
    constraint = next(
        item
        for item in EmailLinkSnapshot._meta.constraints
        if item.name == 'uniq_email_snapshot_link_hash'
    )
    digest_field = EmailLinkSnapshot._meta.get_field('url_sha256')
    bigint_bytes = 8
    utf8mb4_bytes = digest_field.max_length * 4

    assert constraint.fields == ('snapshot', 'url_sha256')
    assert bigint_bytes + utf8mb4_bytes <= 3072
