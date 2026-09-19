"""Access boundaries for short-lived formalization reviews."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import ProposalFormalization, ProposalFormalizationFile

pytestmark = pytest.mark.django_db


def _preparation(proposal, user, expires_at):
    return ProposalFormalization.objects.create(
        proposal=proposal,
        created_by=user,
        payload={
            'subject': 'Formalización',
            'recipient_emails': ['contact@acme.com'],
            'cc_emails': [],
        },
        source_hash='a' * 64,
        html_body='<p>preview</p>',
        text_body='preview',
        expires_at=expires_at,
    )


@freeze_time('2026-09-19 12:00:00')
def test_detail_returns_gone_for_an_expired_preparation(admin_client, admin_user, proposal):
    """Fails if a formalization preview remains available after its review window expires."""
    preparation = _preparation(proposal, admin_user, timezone.now())
    url = reverse('formalization-detail', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 410
    assert response.json()['code'] == 'expired_preparation'


@freeze_time('2026-09-19 12:00:00')
def test_detail_hides_a_preparation_created_by_another_administrator(admin_client, admin_user, proposal):
    """Fails if one administrator can read another administrator's formalization review."""
    other_user = get_user_model().objects.create_user(
        username='other_formalization_admin', email='other-formalization@example.com',
        password='testpass123', is_staff=True,
    )
    preparation = _preparation(proposal, other_user, timezone.now() + timedelta(hours=1))
    url = reverse('formalization-detail', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 404


def test_options_returns_private_formalization_availability(admin_client, proposal):
    """Fails if the Documents modal cannot initialize formalization defaults from a private response."""
    response = admin_client.get(reverse('formalization-options', kwargs={'proposal_id': proposal.pk}))

    assert response.status_code == 200
    assert set(response.json()['defaults']) == {'subject', 'greeting', 'body', 'footer'}
    assert response.json()['documents'][0]['key'] == 'contract'
    assert response['Cache-Control'] == 'private, no-store'


def test_pdf_returns_a_controlled_error_for_an_unknown_document_kind(admin_client, proposal):
    """Fails if an unsupported formalization PDF URL becomes an unhandled server error."""
    response = admin_client.get(reverse('formalization-pdf', kwargs={
        'proposal_id': proposal.pk,
        'kind': 'unsupported',
    }))

    assert response.status_code == 400
    assert response.json()['code'] == 'invalid_document'


@freeze_time('2026-09-19 12:00:00')
def test_attachment_returns_gone_for_an_expired_preparation(admin_client, admin_user, proposal):
    """Fails if a private formalization attachment remains downloadable after expiry."""
    preparation = _preparation(proposal, admin_user, timezone.now())
    attachment = ProposalFormalizationFile.objects.create(
        preparation=preparation,
        key='commercial',
        filename='formal.pdf',
        description='Formal PDF',
        mime_type='application/pdf',
        sha256='a' * 64,
        size=18,
    )
    attachment.file.save('formal.pdf', ContentFile(b'curated formal bytes'), save=True)
    url = reverse('formalization-file', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation.pk,
        'file_id': attachment.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 410


@freeze_time('2026-09-19 12:00:00')
def test_attachment_serves_saved_bytes_with_download_hardening(admin_client, admin_user, proposal):
    """Fails if a current formalization attachment loses its reviewed bytes or download protections."""
    preparation = _preparation(proposal, admin_user, timezone.now() + timedelta(hours=1))
    attachment = ProposalFormalizationFile.objects.create(
        preparation=preparation,
        key='commercial',
        filename='formal.pdf',
        description='Formal PDF',
        mime_type='application/pdf',
        sha256='b' * 64,
        size=19,
    )
    attachment.file.save('formal.pdf', ContentFile(b'curated formal bytes'), save=True)
    url = reverse('formalization-file', kwargs={
        'proposal_id': proposal.pk,
        'preparation_id': preparation.pk,
        'file_id': attachment.pk,
    })

    response = admin_client.get(url)

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'curated formal bytes'
    assert response['Content-Disposition'] == 'attachment; filename="formal.pdf"'
    assert response['Cache-Control'] == 'private, no-store'
    assert response['X-Content-Type-Options'] == 'nosniff'
