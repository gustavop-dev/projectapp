from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone

from content.models import Document, DocumentThread, DocumentThreadItem


BOGOTA = ZoneInfo('America/Bogota')


class DocumentThreadError(ValueError):
    """A document-thread rule violation safe to expose through the panel API."""

    def __init__(self, message, *, code, hint=None, status_code=400):
        super().__init__(message)
        self.code = code
        self.hint = hint
        self.status_code = status_code


def default_occurred_on(document):
    """Use the document date, falling back to its Bogotá creation date."""
    if document.issue_date:
        return document.issue_date
    created_at = document.created_at or timezone.now()
    return timezone.localtime(created_at, BOGOTA).date()


def _validated_title(title, *, fallback=None):
    value = str(title or '').strip()
    if not value and fallback is not None:
        value = str(fallback).strip()
    if not value:
        raise DocumentThreadError(
            'El hilo debe tener un nombre.',
            code='document_thread_title_required',
        )
    if len(value) > 255:
        raise DocumentThreadError(
            'El nombre del hilo no puede superar 255 caracteres.',
            code='document_thread_title_too_long',
        )
    return value


def _lock_documents(raw_items):
    document_ids = [item['document_id'] for item in raw_items]
    if len(document_ids) != len(set(document_ids)):
        raise DocumentThreadError(
            'Un documento no puede repetirse dentro del mismo hilo.',
            code='duplicate_document_in_thread',
        )

    documents = {
        document.pk: document
        for document in Document.objects.select_for_update().filter(pk__in=document_ids)
    }
    missing = [document_id for document_id in document_ids if document_id not in documents]
    if missing:
        raise DocumentThreadError(
            'Uno de los documentos seleccionados ya no existe.',
            code='document_not_found',
        )
    return document_ids, documents


def _ensure_documents_are_available(document_ids, *, current_thread=None):
    memberships = (
        DocumentThreadItem.objects.select_for_update()
        .select_related('document', 'thread')
        .filter(document_id__in=document_ids)
    )
    if current_thread is not None:
        memberships = memberships.exclude(thread=current_thread)
    membership = memberships.first()
    if membership:
        raise DocumentThreadError(
            f'“{membership.document.title}” ya pertenece al hilo '
            f'“{membership.thread.title}”.',
            code='document_already_threaded',
            hint='Retira el documento de su hilo actual antes de enlazarlo en otro.',
            status_code=409,
        )


def _resolved_items(raw_items, documents):
    return [
        {
            'document': documents[item['document_id']],
            'occurred_on': item.get('occurred_on')
            or default_occurred_on(documents[item['document_id']]),
            'position': position,
        }
        for position, item in enumerate(raw_items)
    ]


@transaction.atomic
def create_document_thread(*, title, items, actor):
    if len(items) < 2:
        raise DocumentThreadError(
            'Selecciona al menos dos documentos para formar un hilo.',
            code='document_thread_requires_two_documents',
        )

    document_ids, documents = _lock_documents(items)
    _ensure_documents_are_available(document_ids)
    resolved_items = _resolved_items(items, documents)
    thread = DocumentThread.objects.create(
        title=_validated_title(title, fallback=resolved_items[0]['document'].title),
        created_by=actor,
        updated_by=actor,
    )
    try:
        DocumentThreadItem.objects.bulk_create([
            DocumentThreadItem(
                thread=thread,
                document=item['document'],
                occurred_on=item['occurred_on'],
                position=item['position'],
                linked_by=actor,
                updated_by=actor,
            )
            for item in resolved_items
        ])
    except IntegrityError as exc:
        raise DocumentThreadError(
            'Uno de los documentos ya fue enlazado en otro hilo.',
            code='document_already_threaded',
            hint='Actualiza la búsqueda y vuelve a intentarlo.',
            status_code=409,
        ) from exc
    return thread


@transaction.atomic
def update_document_thread(*, thread, actor, title=None, items=None):
    thread = DocumentThread.objects.select_for_update().get(pk=thread.pk)

    if items is not None:
        if not items:
            raise DocumentThreadError(
                'El hilo debe conservar al menos un documento.',
                code='document_thread_items_required',
            )
        document_ids, documents = _lock_documents(items)
        _ensure_documents_are_available(document_ids, current_thread=thread)

        if len(items) == 1:
            thread.delete()
            return None, True

        resolved_items = _resolved_items(items, documents)
        existing = {
            item.document_id: item
            for item in DocumentThreadItem.objects.select_for_update().filter(thread=thread)
        }
        target_ids = set(document_ids)
        DocumentThreadItem.objects.filter(thread=thread).exclude(
            document_id__in=target_ids,
        ).delete()

        for item in resolved_items:
            document = item['document']
            membership = existing.get(document.pk)
            if membership is None:
                DocumentThreadItem.objects.create(
                    thread=thread,
                    document=document,
                    occurred_on=item['occurred_on'],
                    position=item['position'],
                    linked_by=actor,
                    updated_by=actor,
                )
                continue
            membership.occurred_on = item['occurred_on']
            membership.position = item['position']
            membership.updated_by = actor
            membership.save(update_fields=[
                'occurred_on', 'position', 'updated_by', 'updated_at',
            ])

    if title is not None:
        thread.title = _validated_title(title)
    thread.updated_by = actor
    thread.save(update_fields=['title', 'updated_by', 'updated_at'])
    return thread, False


@transaction.atomic
def dissolve_document_thread(*, thread):
    locked = DocumentThread.objects.select_for_update().get(pk=thread.pk)
    locked.delete()
