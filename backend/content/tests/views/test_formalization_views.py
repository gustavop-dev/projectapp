"""Access boundaries for short-lived formalization reviews."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from content.models import ProposalFormalization

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
