"""Historical PDF downloads survive replacement, detachment, and live-row deletion."""

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import date
import pytest
from rest_framework.test import APIClient

from content.models import BusinessProposal, CreditCardStatement, Document, EntityHistory, EntityRevision
from content.services import accounting_statement_service


pytestmark = pytest.mark.django_db


def _admin_client(*, superuser=False):
    user = get_user_model().objects.create_user(
        username=f'staff-{superuser}', is_staff=True, is_superuser=superuser,
    )
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_document_history_downloads_retained_pdf_after_live_file_is_detached(settings, tmp_path):
    """Fails if replacing or clearing a document file makes its prior version unreadable."""
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(title='Contrato PDF')
    document.generated_file.save('contract-history.pdf', ContentFile(b'%PDF historical-document'), save=True)
    version = next(
        row for row in EntityHistory.objects.get(
            entity_type='document', object_id=document.pk,
        ).entries.all()
        if row.snapshot.get('generated_file')
    )
    document.generated_file = ''
    document.save(update_fields=['generated_file'])

    response = _admin_client().get(
        f'/api/entity-history/document/{document.pk}/versions/{version.pk}/file/',
    )

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'%PDF historical-document'
    assert response['Cache-Control'] == 'no-store'


def test_proposal_history_downloads_archived_pdf_after_proposal_deletion(settings, tmp_path):
    """Fails if deleting a proposal removes the exact PDF version marked as sent."""
    settings.MEDIA_ROOT = tmp_path
    proposal = BusinessProposal.objects.create(
        title='Propuesta PDF', client_name='Cliente', client_email='client@example.test',
    )
    name = default_storage.save('documents/proposal-history.pdf', ContentFile(b'%PDF historical-proposal'))
    history = EntityHistory.objects.get(entity_type='proposal', object_id=proposal.pk)
    proposal_id = proposal.pk
    history.revision += 1
    history.save(update_fields=['revision'])
    version = EntityRevision.objects.create(
        history=history, number=history.revision, action='sent_version',
        snapshot={'archived_pdf': name}, source='proposal_email',
    )
    proposal.delete()

    response = _admin_client().get(
        f'/api/entity-history/proposal/{proposal_id}/versions/{version.pk}/file/',
    )

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'%PDF historical-proposal'


def test_statement_history_preserves_original_pdf(settings, tmp_path):
    """Fails if replacing or removing an extract PDF destroys the bytes held by its version."""
    settings.MEDIA_ROOT = tmp_path
    statement = CreditCardStatement.objects.create(
        card_name='Tarjeta histórica', period_date=date(2026, 9, 1), purchases_total='100.00',
    )
    accounting_statement_service.attach_statement_pdf(
        statement, ContentFile(b'%PDF original-statement', name='original.pdf'), None,
    )
    version = next(
        row for row in EntityHistory.objects.get(
            entity_type='statement', object_id=statement.pk,
        ).entries.all()
        if row.snapshot.get('pdf_file')
    )
    accounting_statement_service.attach_statement_pdf(
        statement, ContentFile(b'%PDF replacement-statement', name='replacement.pdf'), None,
    )
    accounting_statement_service.remove_statement_pdf(statement, None)

    response = _admin_client(superuser=True).get(
        f'/api/entity-history/statement/{statement.pk}/versions/{version.pk}/file/',
    )

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == b'%PDF original-statement'
