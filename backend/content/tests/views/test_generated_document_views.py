from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from content.models import (
    AccountingChangeLog,
    BusinessProposal,
    Document,
    DocumentFolder,
    EmailLog,
    EmailLogTarget,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
    get_commercial_proposal_document_type,
    get_markdown_document_type,
)

pytestmark = pytest.mark.django_db


def make_account(status_value):
    return Document.objects.create(
        title='Cuenta de cobro',
        document_type=get_collection_account_document_type(),
        commercial_status=status_value,
    )


def list_row(admin_client, document, **params):
    response = admin_client.get(reverse('list-documents'), params)
    assert response.status_code == 200
    return next(row for row in response.json() if row['id'] == document.pk)


@pytest.mark.parametrize(
    ('status_value', 'expected_key'),
    (
        (Document.CommercialStatus.DRAFT, 'draft'),
        (Document.CommercialStatus.ISSUED, 'issued'),
        (Document.CommercialStatus.PAID, 'paid'),
        (Document.CommercialStatus.CANCELLED, 'cancelled'),
    ),
)
def test_list_maps_commercial_status(admin_client, status_value, expected_key):
    document = make_account(status_value)

    row = list_row(admin_client, document)

    assert row['display_state']['key'] == expected_key
    assert row['active_states'] == []


def test_list_marks_delivered_account_as_sent(admin_client):
    document = make_account(Document.CommercialStatus.ISSUED)
    log = EmailLog.objects.create(
        template_key='collection_account_sent',
        recipient='client@example.com',
        status=EmailLog.Status.SENT,
    )
    EmailLogTarget.objects.create(
        email_log=log,
        entity_type=AccountingChangeLog.EntityType.COLLECTION_ACCOUNT,
        object_id=document.pk,
    )

    row = list_row(admin_client, document)

    assert row['display_state'] == {
        'key': 'sent', 'label': 'Enviada', 'variant': 'success',
    }


def test_list_marks_failed_account_delivery(admin_client):
    document = make_account(Document.CommercialStatus.ISSUED)
    log = EmailLog.objects.create(
        template_key='collection_account_sent',
        recipient='client@example.com',
        status=EmailLog.Status.FAILED,
    )
    EmailLogTarget.objects.create(
        email_log=log,
        entity_type=AccountingChangeLog.EntityType.COLLECTION_ACCOUNT,
        object_id=document.pk,
    )

    row = list_row(admin_client, document)

    assert row['display_state']['key'] == 'send_failed'


def test_unclassified_preset_excludes_collection_accounts(admin_client):
    account = make_account(Document.CommercialStatus.ISSUED)
    markdown = Document.objects.create(
        title='Documento manual',
        document_type=get_markdown_document_type(),
    )
    markdown.state_episodes.all().delete()

    response = admin_client.get(
        reverse('list-documents'),
        {'preset': 'unclassified'},
    )

    assert {row['id'] for row in response.json()} == {markdown.pk}


def test_system_folder_rejects_rename(admin_client):
    folder = DocumentFolder.objects.create(
        name='Cuentas de cobro',
        system_key='generated:test:collection-account',
    )

    response = admin_client.patch(
        reverse('update-document-folder', kwargs={'folder_id': folder.pk}),
        {'name': 'Otro nombre'},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'system_managed_folder'


def test_system_folder_rejects_manual_child(admin_client):
    folder = DocumentFolder.objects.create(
        name='Proyectos',
        system_key='generated:test:projects',
    )

    response = admin_client.post(
        reverse('create-document-folder'),
        {'name': 'Manual', 'parent': folder.pk},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'system_managed_folder'


def make_snapshot(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    proposal = BusinessProposal.objects.create(
        title='Portal', client_name='Acme', client_email='acme@example.com',
    )
    document = Document.objects.create(
        title='2026-08-14 · Propuesta comercial · Portal · v01',
        document_type=get_commercial_proposal_document_type(),
        source_proposal=proposal,
        source_version=1,
    )
    document.generated_file.save(
        'proposal-v01.pdf', ContentFile(b'%PDF stored-version'), save=True,
    )
    return document


def test_generated_snapshot_rejects_update(admin_client, settings, tmp_path):
    document = make_snapshot(settings, tmp_path)

    response = admin_client.patch(
        reverse('update-document', kwargs={'document_id': document.pk}),
        {'title': 'Rewritten'},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'generated_snapshot_read_only'


def test_generated_snapshot_stays_read_only_after_source_deletion(
    admin_client, settings, tmp_path,
):
    document = make_snapshot(settings, tmp_path)
    document.source_proposal.delete()
    document.refresh_from_db()

    response = admin_client.patch(
        reverse('update-document', kwargs={'document_id': document.pk}),
        {'title': 'Rewritten'},
        format='json',
    )

    assert document.source_proposal_id is None
    assert response.status_code == 409
    assert response.json()['code'] == 'generated_snapshot_read_only'


def test_generated_snapshot_downloads_stored_bytes(
    admin_client, settings, tmp_path,
):
    document = make_snapshot(settings, tmp_path)

    response = admin_client.get(
        reverse('download-document-pdf', kwargs={'document_id': document.pk}),
    )

    assert response.status_code == 200
    assert response.content == b'%PDF stored-version'


def test_collection_account_download_uses_account_pdf(admin_client):
    document = make_account(Document.CommercialStatus.ISSUED)

    with patch(
        'content.services.collection_account_pdf_service.CollectionAccountPdfService.generate',
        return_value=b'%PDF collection-account',
    ) as generate:
        response = admin_client.get(
            reverse('download-document-pdf', kwargs={'document_id': document.pk}),
        )

    assert response.status_code == 200
    assert response.content == b'%PDF collection-account'
    generate.assert_called_once_with(document)


def test_managed_folder_lists_newest_documents_first(admin_client):
    folder = DocumentFolder.objects.create(
        name='08 - Agosto',
        system_key='generated:test:2026:08',
    )
    document_type = get_markdown_document_type()
    older = Document.objects.create(
        title='Zulu', document_type=document_type, folder=folder,
    )
    newer = Document.objects.create(
        title='Alpha', document_type=document_type, folder=folder,
    )

    response = admin_client.get(
        reverse('list-documents'),
        {'folder': folder.pk},
    )

    assert [row['id'] for row in response.json()] == [newer.id, older.id]


def test_markdown_creation_rejects_managed_folder(admin_client):
    folder = DocumentFolder.objects.create(
        name='Propuestas comerciales',
        system_key='generated:test:manual-create',
    )

    response = admin_client.post(
        reverse('create-document-from-markdown'),
        {'title': 'Manual', 'markdown': '# Manual', 'folder_id': folder.pk},
        format='json',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'system_managed_folder'


def test_markdown_upload_rejects_managed_folder(admin_client):
    folder = DocumentFolder.objects.create(
        name='Cuentas de cobro',
        system_key='generated:test:manual-upload',
    )
    uploaded = BytesIO(b'# Manual')
    uploaded.name = 'manual.md'

    response = admin_client.post(
        reverse('upload-document-markdown'),
        {'file': uploaded, 'folder_id': folder.pk},
        format='multipart',
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'system_managed_folder'
