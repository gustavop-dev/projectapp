"""The proposal history identifies the exact immutable version delivered to a client."""

from unittest.mock import patch
from decimal import Decimal

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from content.models import BusinessProposal, EntityHistory
from content.services.proposal_snapshot_service import (
    finalize_proposal_snapshots,
    prepare_proposal_snapshots,
)


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def proposal():
    user = User.objects.create_user(username='proposal-history@example.test')
    profile = UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_CLIENT, company_name='Nube SAS',
    )
    return BusinessProposal.objects.create(
        title='Portal de clientes', client=profile, client_name='Nube SAS',
        client_email='proposal-history@example.test',
        email_intro='Esta propuesta conserva la versión enviada.', total_investment=Decimal('100.00'),
    )


def _delivery(ok):
    return {'ok': ok, 'reason': 'sent' if ok else 'send_failed', 'detail': ''}


def test_successful_delivery_marks_the_exact_prepared_snapshot_as_sent(proposal, settings, tmp_path):
    """Fails if a later proposal edit can replace the version marked as sent."""
    settings.MEDIA_ROOT = tmp_path
    with patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=b'%PDF sent'):
        prepared = prepare_proposal_snapshots([proposal])
    prepared_version = EntityHistory.objects.get(
        entity_type='proposal', object_id=proposal.pk,
    ).entries.get(action='prepared_version')
    proposal.total_investment = Decimal('250.00')
    proposal.save(update_fields=['total_investment'])
    finalize_proposal_snapshots(prepared, _delivery(True))

    entries = EntityHistory.objects.get(entity_type='proposal', object_id=proposal.pk).entries
    sent = entries.get(action='sent_version')
    staff = User.objects.create_user(username='history-staff', is_staff=True)
    client = APIClient()
    client.force_authenticate(staff)
    listing = client.get(f'/api/entity-history/proposal/{proposal.pk}/')

    assert sent.snapshot == prepared_version.snapshot
    assert sent.snapshot['total_investment'] == '100.00'
    assert sent.source_key.startswith('proposal_pdf:')
    assert listing.data['last_sent_version']['id'] == sent.pk


def test_failed_delivery_does_not_mark_a_prepared_snapshot_as_sent(proposal, settings, tmp_path):
    """Fails if an unsent PDF is presented as a version received by the client."""
    settings.MEDIA_ROOT = tmp_path
    with patch('content.services.proposal_pdf_service.ProposalPdfService.generate', return_value=b'%PDF failed'):
        prepared = prepare_proposal_snapshots([proposal])
    finalize_proposal_snapshots(prepared, _delivery(False))

    entries = EntityHistory.objects.get(entity_type='proposal', object_id=proposal.pk).entries
    assert entries.filter(action='prepared_version').count() == 1
    assert entries.filter(action='sent_version').count() == 0
