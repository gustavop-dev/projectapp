"""Historical collection-account PDF backfill behavior."""
import hashlib
import uuid
from datetime import date
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from content.models import (
    Document,
    DocumentCollectionAccount,
    EmailAttachmentSnapshot,
    EmailBody,
    EmailDeliverySnapshot,
)
from content.services.collection_account_snapshot_service import (
    EMAIL_HISTORY_SOURCE,
    LEGACY_RECONSTRUCTION_SOURCE,
    stored_collection_account_pdf,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def generated_document_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def make_legacy_account(number='PA-LEGACY-001'):
    document = Document.objects.create(
        title=f'Cuenta de cobro {number}',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        public_number=number,
        issue_date=date(2026, 8, 1),
    )
    DocumentCollectionAccount.objects.create(document=document)
    return document


def attach_email_snapshot(document, pdf_bytes):
    body = EmailBody.objects.create(text='Correo histórico')
    snapshot = EmailDeliverySnapshot.objects.create(
        delivery_id=uuid.uuid4(),
        template_key='collection_account_sent',
        classification=EmailDeliverySnapshot.Classification.CLIENT,
        body=body,
        attachment_size_bytes=len(pdf_bytes),
        attachment_count=1,
    )
    attachment = EmailAttachmentSnapshot(
        snapshot=snapshot,
        filename=f'{document.public_number}.pdf',
        mime_type='application/pdf',
        size_bytes=len(pdf_bytes),
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        position=0,
        format_kind=EmailAttachmentSnapshot.FormatKind.PDF,
        business_kind='collection_account',
        business_kind_label='Cuenta de cobro',
        source_document=document,
        source_document_type_code='collection_account',
        source_document_type_name='Cuenta de cobro',
    )
    attachment.file.save(attachment.filename, ContentFile(pdf_bytes), save=False)
    attachment.save()


def test_apply_prefers_the_exact_email_attachment():
    document = make_legacy_account()
    historical_pdf = b'%PDF-1.4 email attachment exact bytes'
    attach_email_snapshot(document, historical_pdf)

    with patch(
        'content.management.commands.backfill_collection_account_pdf_snapshots'
        '.render_collection_account_pdf',
        side_effect=AssertionError('email evidence must win'),
    ):
        call_command(
            'backfill_collection_account_pdf_snapshots', apply=True,
            stdout=StringIO(),
        )

    document.refresh_from_db()
    assert stored_collection_account_pdf(document) == historical_pdf
    assert document.metadata['generated_pdf']['source'] == EMAIL_HISTORY_SOURCE


def test_apply_reconstructs_only_when_email_evidence_is_absent():
    document = make_legacy_account()
    reconstructed_pdf = b'%PDF-1.4 reconstructed legacy account'

    with patch(
        'content.management.commands.backfill_collection_account_pdf_snapshots'
        '.render_collection_account_pdf',
        return_value=reconstructed_pdf,
    ):
        call_command(
            'backfill_collection_account_pdf_snapshots', apply=True,
            stdout=StringIO(),
        )

    document.refresh_from_db()
    assert stored_collection_account_pdf(document) == reconstructed_pdf
    assert (
        document.metadata['generated_pdf']['source']
        == LEGACY_RECONSTRUCTION_SOURCE
    )


def test_default_dry_run_leaves_the_legacy_document_unchanged():
    document = make_legacy_account()
    output = StringIO()

    with patch(
        'content.management.commands.backfill_collection_account_pdf_snapshots'
        '.render_collection_account_pdf',
        return_value=b'%PDF-1.4 dry run',
    ):
        call_command(
            'backfill_collection_account_pdf_snapshots', stdout=output,
        )

    document.refresh_from_db()
    assert not document.generated_file
    assert 'dry-run: eligible=1' in output.getvalue()
