from importlib import import_module

import pytest
from django.apps import apps

from content.email_copy_families import EMAIL_COPY_FAMILY_VALUES
from content.models import EmailCopyRecipient


pytestmark = pytest.mark.django_db
migration = import_module(
    'content.migrations.0225_seed_carlos_email_copy_recipient'
)


def test_forward_enables_carlos_for_every_email_family():
    EmailCopyRecipient.objects.update_or_create(
        email=migration.CARLOS_EMAIL,
        defaults={
            'is_active': False,
            'families': ['proposals'],
        },
    )

    migration.enable_carlos_email_copy(apps, None)

    recipient = EmailCopyRecipient.objects.get(email=migration.CARLOS_EMAIL)
    assert recipient.is_active is True
    assert recipient.families == list(EMAIL_COPY_FAMILY_VALUES)
