"""Immutable collection-account PDF storage contracts."""
from datetime import date
from unittest.mock import patch

import pytest

from content.models import Document, DocumentCollectionAccount
from content.services.collection_account_snapshot_service import (
    ISSUE_SOURCE,
    CollectionAccountSnapshotError,
    persist_collection_account_pdf,
    stored_collection_account_pdf,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def generated_document_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def make_issued_account():
    document = Document.objects.create(
        title='Cuenta de cobro — soporte mensual',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        public_number='PA-ACME-001',
        issue_date=date(2026, 9, 2),
    )
    DocumentCollectionAccount.objects.create(document=document)
    return document


def test_persist_archives_exact_bytes_with_verifiable_provenance():
    document = make_issued_account()
    expected_pdf = b'%PDF-1.4 exact issued account'

    stored = persist_collection_account_pdf(document, pdf_bytes=expected_pdf)

    document.refresh_from_db()
    assert stored.pdf_bytes == expected_pdf
    assert stored_collection_account_pdf(document) == expected_pdf
    assert document.metadata['generated_source'] == ISSUE_SOURCE
    assert document.metadata['generated_pdf']['sha256'] == stored.sha256
    assert document.is_generated_snapshot is True


def test_reader_never_renders_over_an_existing_snapshot():
    document = make_issued_account()
    persist_collection_account_pdf(document, pdf_bytes=b'%PDF-1.4 archived')
    document.refresh_from_db()

    with patch(
        'content.services.collection_account_snapshot_service'
        '.render_collection_account_pdf',
        side_effect=AssertionError('must not regenerate'),
    ):
        result = stored_collection_account_pdf(document)

    assert result == b'%PDF-1.4 archived'


def test_persist_refuses_to_replace_an_existing_snapshot():
    document = make_issued_account()
    first = persist_collection_account_pdf(
        document,
        pdf_bytes=b'%PDF-1.4 original',
    )
    document.refresh_from_db()

    with pytest.raises(CollectionAccountSnapshotError, match='ya tiene'):
        persist_collection_account_pdf(
            document,
            pdf_bytes=b'%PDF-1.4 replacement',
        )

    document.refresh_from_db()
    assert document.generated_file.name == first.name
    assert stored_collection_account_pdf(document) == b'%PDF-1.4 original'


def test_missing_stored_object_is_reported_instead_of_reconstructed():
    document = make_issued_account()
    document.generated_file.name = 'documents/generated/missing-account.pdf'
    document.save(update_fields=['generated_file'])

    with patch(
        'content.services.collection_account_snapshot_service'
        '.render_collection_account_pdf',
        side_effect=AssertionError('corruption is not legacy'),
    ):
        with pytest.raises(CollectionAccountSnapshotError, match='no está disponible'):
            stored_collection_account_pdf(document)


def test_persist_rejects_non_pdf_bytes():
    document = make_issued_account()

    with pytest.raises(CollectionAccountSnapshotError, match='no es un PDF válido'):
        persist_collection_account_pdf(document, pdf_bytes=b'<html>error</html>')

    document.refresh_from_db()
    assert not document.generated_file
