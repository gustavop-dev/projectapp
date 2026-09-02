"""Immutable PDF storage for issued collection-account Documents.

The relational collection-account rows remain the source used while a draft is
being prepared.  Issuance crosses the accounting boundary: from that point on
every reader must use the exact stored bytes rather than rendering today's
code over yesterday's snapshots.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from django.core.files.base import ContentFile

from content.models import Document, EmailAttachmentSnapshot
from content.utils import safe_slug

logger = logging.getLogger(__name__)

ISSUE_SOURCE = 'collection_account_issue'
EMAIL_HISTORY_SOURCE = 'collection_account_email_history'
LEGACY_RECONSTRUCTION_SOURCE = 'collection_account_legacy_reconstruction'


class CollectionAccountSnapshotError(ValueError):
    """The immutable PDF could not be produced, stored, or read."""


@dataclass(frozen=True)
class StoredCollectionAccountPdf:
    """Storage reference retained so an enclosing transaction can clean up."""

    storage: object
    name: str
    pdf_bytes: bytes
    sha256: str


def _validated_pdf(pdf_bytes):
    if not isinstance(pdf_bytes, (bytes, bytearray)) or not pdf_bytes:
        raise CollectionAccountSnapshotError(
            'No se pudo generar el PDF inmutable de la cuenta de cobro.',
        )
    pdf = bytes(pdf_bytes)
    if b'%PDF-' not in pdf[:1024]:
        raise CollectionAccountSnapshotError(
            'El archivo generado para la cuenta de cobro no es un PDF válido.',
        )
    return pdf


def render_collection_account_pdf(document):
    """Render draft/current relational data without persisting a file."""
    from content.services.collection_account_pdf_service import (
        CollectionAccountPdfService,
    )

    return _validated_pdf(CollectionAccountPdfService.generate(document))


def stored_collection_account_pdf(document, *, allow_legacy=True):
    """Return canonical bytes, dynamically rendering only unsnapshotted legacy rows.

    A non-empty FileField whose object disappeared is corruption, not a legacy
    row.  It must fail visibly instead of silently replacing historical bytes.
    """
    if document.generated_file:
        try:
            with document.generated_file.open('rb') as stored_pdf:
                return _validated_pdf(stored_pdf.read())
        except (OSError, ValueError) as exc:
            logger.exception(
                'Stored collection-account PDF %s could not be read', document.pk,
            )
            raise CollectionAccountSnapshotError(
                'El PDF archivado de la cuenta de cobro no está disponible.',
            ) from exc

    if not allow_legacy:
        raise CollectionAccountSnapshotError(
            'La cuenta de cobro no tiene un PDF inmutable archivado.',
        )

    if document.commercial_status != Document.CommercialStatus.DRAFT:
        logger.warning(
            'Legacy collection account %s has no immutable PDF; rendering fallback',
            document.pk,
        )
    return render_collection_account_pdf(document)


def first_email_snapshot_pdf(document):
    """Return the earliest exact PDF captured for this account, when present."""
    attachment = (
        EmailAttachmentSnapshot.objects.filter(
            source_document=document,
            business_kind='collection_account',
            format_kind=EmailAttachmentSnapshot.FormatKind.PDF,
        )
        .select_related('snapshot')
        .order_by('snapshot__captured_at', 'position', 'pk')
        .first()
    )
    if attachment is None:
        return None
    try:
        with attachment.file.open('rb') as stored_file:
            return _validated_pdf(stored_file.read())
    except (OSError, ValueError) as exc:
        raise CollectionAccountSnapshotError(
            'El PDF histórico del correo no está disponible.',
        ) from exc


def persist_collection_account_pdf(
    document,
    *,
    pdf_bytes=None,
    source=ISSUE_SOURCE,
):
    """Store one immutable PDF and annotate its provenance/hash.

    Existing files are never overwritten.  The returned storage reference lets
    a caller that owns a wider database transaction remove the file if that
    outer transaction later rolls back.
    """
    if document.generated_file:
        raise CollectionAccountSnapshotError(
            'La cuenta de cobro ya tiene un PDF inmutable archivado.',
        )
    if document.commercial_status == Document.CommercialStatus.DRAFT:
        raise CollectionAccountSnapshotError(
            'Una cuenta de cobro en borrador no puede archivarse como definitiva.',
        )
    if not document.public_number or not document.issue_date:
        raise CollectionAccountSnapshotError(
            'La cuenta debe tener consecutivo y fecha de emisión antes de archivar el PDF.',
        )

    pdf = _validated_pdf(
        pdf_bytes if pdf_bytes is not None else render_collection_account_pdf(document),
    )
    digest = hashlib.sha256(pdf).hexdigest()
    filename = f'{safe_slug(document.public_number, "cuenta-de-cobro")}.pdf'
    storage = document.generated_file.storage
    stored_name = ''

    try:
        document.generated_file.save(filename, ContentFile(pdf), save=False)
        stored_name = document.generated_file.name
        metadata = dict(document.metadata or {})
        metadata['generated_source'] = source
        metadata['generated_pdf'] = {
            'source': source,
            'sha256': digest,
            'filename': filename,
        }
        document.metadata = metadata
        document.save(update_fields=['generated_file', 'metadata', 'updated_at'])
    except Exception as exc:
        if stored_name:
            try:
                storage.delete(stored_name)
            except Exception:
                logger.exception(
                    'Could not clean failed collection-account PDF %s', stored_name,
                )
        document.generated_file = ''
        raise CollectionAccountSnapshotError(
            'No se pudo guardar el PDF inmutable de la cuenta de cobro.',
        ) from exc

    return StoredCollectionAccountPdf(
        storage=storage,
        name=stored_name,
        pdf_bytes=pdf,
        sha256=digest,
    )


def discard_stored_collection_account_pdf(stored):
    """Best-effort compensation for a surrounding database rollback."""
    if stored is None or not stored.name:
        return
    try:
        stored.storage.delete(stored.name)
    except Exception:
        logger.exception(
            'Could not clean rolled-back collection-account PDF %s', stored.name,
        )
