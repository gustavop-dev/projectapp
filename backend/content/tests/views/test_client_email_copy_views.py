import pytest
from django.urls import reverse

from content.email_copy_families import CLIENT_EMAIL_FAMILY_VALUES, PROPOSALS
from content.models import ClientEmailCopyRecipient


pytestmark = pytest.mark.django_db


def test_staff_lists_copy_configuration(admin_client):
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')

    response = admin_client.get(reverse('client-email-copy-recipients'))

    assert response.status_code == 200
    assert response.data['results'][0]['email'] == 'audit@example.com'
    assert len(response.data['families']) == 5
    assert response.data['copy_mode'] == 'bcc'


def test_anonymous_user_cannot_list_copy_configuration(api_client):
    response = api_client.get(reverse('client-email-copy-recipients'))

    assert response.status_code in (401, 403)


def test_create_recipient_defaults_to_every_family(admin_client):
    response = admin_client.post(
        reverse('client-email-copy-recipients'),
        {'email': 'Audit@Example.com'},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['email'] == 'audit@example.com'
    assert response.data['families'] == list(CLIENT_EMAIL_FAMILY_VALUES)


def test_duplicate_recipient_is_rejected_case_insensitively(admin_client):
    ClientEmailCopyRecipient.objects.create(email='audit@example.com')

    response = admin_client.post(
        reverse('client-email-copy-recipients'),
        {'email': 'AUDIT@example.com'},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['email'] == ['Ese correo ya está en la lista.']


def test_active_recipient_rejects_empty_family_list(admin_client):
    response = admin_client.post(
        reverse('client-email-copy-recipients'),
        {'email': 'audit@example.com', 'is_active': True, 'families': []},
        format='json',
    )

    assert response.status_code == 400
    assert 'al menos una familia' in response.data['families'][0]


def test_patch_recipient_updates_family_selection(admin_client):
    recipient = ClientEmailCopyRecipient.objects.create(email='audit@example.com')

    response = admin_client.patch(
        reverse(
            'client-email-copy-recipient-detail',
            kwargs={'recipient_id': recipient.pk},
        ),
        {'families': [PROPOSALS]},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['families'] == [PROPOSALS]


def test_delete_recipient_removes_configuration(admin_client):
    recipient = ClientEmailCopyRecipient.objects.create(email='audit@example.com')

    response = admin_client.delete(reverse(
        'client-email-copy-recipient-detail',
        kwargs={'recipient_id': recipient.pk},
    ))

    assert response.status_code == 204
    assert ClientEmailCopyRecipient.objects.count() == 0

