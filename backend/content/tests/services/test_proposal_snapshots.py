from unittest.mock import patch

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from freezegun import freeze_time

from content.models import BusinessProposal, Document
from content.services.generated_document_filing_service import (
    move_proposal_snapshots_to_project,
)
from content.services.proposal_service import ProposalService
from content.services.proposal_snapshot_service import ProposalSnapshotError

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def client_profile():
    user = User.objects.create_user(
        username='proposal-snapshot@example.com',
        email='proposal-snapshot@example.com',
        first_name='Lina',
        last_name='Gómez',
    )
    return UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name='Nube SAS',
        nit='901234567',
    )


@pytest.fixture
def proposal(client_profile):
    return BusinessProposal.objects.create(
        title='Portal de clientes',
        client=client_profile,
        client_name='Nube SAS',
        client_email=client_profile.user.email,
    )


def delivery(ok=True):
    return {
        'ok': ok,
        'reason': 'sent' if ok else 'send_failed',
        'detail': '' if ok else 'SMTP timeout',
    }


def active_state_keys(document):
    return set(
        document.state_episodes.filter(closed_at__isnull=True)
        .values_list('state__system_key', flat=True)
    )


def folder_path(document):
    return [
        *(folder.name for folder in document.folder.get_ancestors()),
        document.folder.name,
    ]


def test_send_persists_attached_pdf_version(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    captured = {}

    def fake_send(sent_proposal, snapshot=None):
        captured['snapshot'] = snapshot
        return delivery()

    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            return_value=b'%PDF exact-version',
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            side_effect=fake_send,
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)

    snapshot = Document.objects.get(source_proposal=proposal, source_version=1)
    with snapshot.generated_file.open('rb') as stored_pdf:
        stored_bytes = stored_pdf.read()

    assert stored_bytes == b'%PDF exact-version'
    assert captured['snapshot'].pdf_bytes == stored_bytes
    assert active_state_keys(snapshot) == {'sent'}


@freeze_time('2026-08-14 15:00:00')
def test_send_files_proposal_under_client_month(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            return_value=b'%PDF hierarchy',
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            return_value=delivery(),
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)

    snapshot = Document.objects.get(source_proposal=proposal)
    assert folder_path(snapshot) == [
        'Clientes',
        'Lina Gómez',
        'Sin proyecto',
        'Propuestas comerciales',
        '2026',
        '08 - Agosto',
    ]


@freeze_time('2026-08-14 15:00:00')
def test_send_applies_proposal_version_title(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            return_value=b'%PDF title',
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            return_value=delivery(),
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)

    snapshot = Document.objects.get(source_proposal=proposal)
    assert snapshot.title == (
        '2026-08-14 · Propuesta comercial · Portal de clientes · v01'
    )


def test_resend_creates_next_version(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            side_effect=(b'%PDF version-one', b'%PDF version-two'),
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            return_value=delivery(),
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)
        ProposalService.resend_proposal(proposal)

    assert list(
        Document.objects.filter(source_proposal=proposal)
        .order_by('source_version')
        .values_list('source_version', flat=True)
    ) == [1, 2]


def test_pdf_failure_preserves_draft_status(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            side_effect=RuntimeError('render failed'),
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
        ) as mock_send,
        pytest.raises(ProposalSnapshotError, match='No se pudo generar'),
    ):
        ProposalService.send_proposal(proposal)

    proposal.refresh_from_db()
    assert proposal.status == BusinessProposal.Status.DRAFT
    assert not Document.objects.filter(source_proposal=proposal).exists()
    mock_send.assert_not_called()


def test_empty_pdf_aborts_send(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            return_value=b'',
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
        ) as mock_send,
        pytest.raises(ProposalSnapshotError, match='quedó vacío'),
    ):
        ProposalService.send_proposal(proposal)

    proposal.refresh_from_db()
    assert proposal.status == BusinessProposal.Status.DRAFT
    assert not Document.objects.filter(source_proposal=proposal).exists()
    mock_send.assert_not_called()


def test_email_failure_marks_snapshot_needs_fix(proposal, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            return_value=b'%PDF failed-delivery',
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            return_value=delivery(ok=False),
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)

    snapshot = Document.objects.get(source_proposal=proposal)
    assert active_state_keys(snapshot) == {'draft', 'needs_fix'}
    assert snapshot.metadata['delivery']['reason'] == 'send_failed'


def test_multi_generation_failure_saves_no_versions(
    proposal, client_profile, settings, tmp_path,
):
    settings.MEDIA_ROOT = tmp_path
    second = BusinessProposal.objects.create(
        title='Aplicación móvil',
        client=client_profile,
        client_name='Nube SAS',
        client_email=client_profile.user.email,
    )
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            side_effect=(b'%PDF first', RuntimeError('second failed')),
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_multi_proposal_to_client',
        ) as mock_send,
        pytest.raises(ProposalSnapshotError, match='Aplicación móvil'),
    ):
        ProposalService.send_multi_proposals([proposal, second])

    proposal.refresh_from_db()
    second.refresh_from_db()
    assert proposal.status == BusinessProposal.Status.DRAFT
    assert second.status == BusinessProposal.Status.DRAFT
    assert not Document.objects.filter(source_proposal__in=[proposal, second]).exists()
    mock_send.assert_not_called()


@freeze_time('2026-08-14 15:00:00')
def test_onboarding_moves_versions_to_project_branch(
    proposal, client_profile, settings, tmp_path,
):
    settings.MEDIA_ROOT = tmp_path
    with (
        patch(
            'content.services.proposal_pdf_service.ProposalPdfService.generate',
            side_effect=(b'%PDF one', b'%PDF two'),
        ),
        patch(
            'content.services.proposal_email_service.ProposalEmailService.send_proposal_to_client',
            return_value=delivery(),
        ),
        patch.object(ProposalService, '_schedule_email_tasks'),
    ):
        ProposalService.send_proposal(proposal)
        ProposalService.resend_proposal(proposal)
    project = Project.objects.create(
        name='Proyecto Nube', client=client_profile.user,
    )

    move_proposal_snapshots_to_project(proposal, project)

    snapshots = list(
        Document.objects.filter(source_proposal=proposal).order_by('source_version')
    )
    assert {snapshot.project_id for snapshot in snapshots} == {project.pk}
    assert folder_path(snapshots[0]) == [
        'Proyectos',
        'Proyecto Nube',
        'Propuestas comerciales',
        snapshots[0].issue_date.strftime('%Y'),
        f'{snapshots[0].issue_date.month:02d} - Agosto',
    ]
