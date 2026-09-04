import json

import pytest
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from content.models import EmailLog
from content.services.email_recipient_service import (
    EmailRecipientValidationError,
    parse_email_recipients,
    recipient_log_contexts,
)


User = get_user_model()


def test_parser_accepts_legacy_recipient_field():
    to_recipients, cc_recipients = parse_email_recipients({
        'recipient_email': ' Client@Example.com ',
    })

    assert to_recipients == ['client@example.com']
    assert cc_recipients == []


def test_parser_preserves_header_groups():
    to_recipients, cc_recipients = parse_email_recipients({
        'recipient_emails': json.dumps(['uno@example.com', 'dos@example.com']),
        'cc_emails': json.dumps(['copia@example.com']),
    })

    assert to_recipients == ['uno@example.com', 'dos@example.com']
    assert cc_recipients == ['copia@example.com']


@pytest.mark.parametrize(
    'payload',
    [
        {
            'recipient_emails': ['repetido@example.com', 'repetido@example.com'],
        },
        {
            'recipient_emails': ['repetido@example.com'],
            'cc_emails': ['REPETIDO@example.com'],
        },
    ],
    ids=['same-header', 'cross-header'],
)
def test_parser_rejects_duplicate_addresses(payload):
    with pytest.raises(
        EmailRecipientValidationError,
        match='repetido@example.com',
    ) as error:
        parse_email_recipients(payload)

    assert error.value.code == 'duplicate_recipient_email'


@pytest.mark.parametrize(
    'email',
    ['no-es-correo', 'cliente_10@temp.example.com'],
    ids=['malformed', 'placeholder'],
)
def test_parser_rejects_unusable_address(email):
    with pytest.raises(EmailRecipientValidationError):
        parse_email_recipients({'recipient_emails': [email]})


def test_parser_requires_to_recipient():
    with pytest.raises(EmailRecipientValidationError) as error:
        parse_email_recipients({'cc_emails': ['copia@example.com']})

    assert error.value.code == 'recipient_required'


def test_parser_enforces_combined_limit():
    with pytest.raises(EmailRecipientValidationError) as error:
        parse_email_recipients({
            'recipient_emails': [f'persona-{index}@example.com' for index in range(9)],
            'cc_emails': ['copia-a@example.com', 'copia-b@example.com'],
        })

    assert error.value.code == 'recipient_limit_exceeded'


@pytest.mark.django_db
def test_log_contexts_attribute_registered_client():
    user = User.objects.create_user(
        username='registered-recipient',
        email='registered@example.com',
    )
    profile = UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
    )

    contexts = recipient_log_contexts(
        ['manual@example.com'],
        ['registered@example.com'],
    )

    assert contexts == [
        {
            'email': 'manual@example.com',
            'recipient_kind': EmailLog.RecipientKind.TO,
            'client_id': None,
            'audience': EmailLog.Audience.INTERNAL,
        },
        {
            'email': 'registered@example.com',
            'recipient_kind': EmailLog.RecipientKind.CC,
            'client_id': profile.pk,
            'audience': EmailLog.Audience.CLIENT,
        },
    ]
