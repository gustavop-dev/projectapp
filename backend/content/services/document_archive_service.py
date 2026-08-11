"""Archivado y desarchivado del gestor de documentos (panel admin).

Archivar saca algo de circulación sin destruirlo. A diferencia de eliminar,
archivar una carpeta CON contenido está permitido: la operación cae en cascada
sobre cada subcarpeta y cada documento del subárbol.

Cada fila arrastrada guarda en `archived_via_folder` la carpeta que la archivó;
las filas archivadas por su cuenta dejan ese campo en NULL y no se tocan. Así,
desarchivar una carpeta restaura exactamente lo que ella arrastró — sin recorrer
el árbol, y sin resucitar lo que el usuario había archivado a propósito.

Ese FK (en vez de un enum 'manual'/'folder') es lo que mantiene correcto el
caso anidado: si una subcarpeta se archivó a mano y después se archiva su padre,
el subárbol de la subcarpeta sigue apuntando a ella, así que desarchivar el
padre lo deja intacto. También sobrevive a mover un documento de carpeta
mientras está archivado, porque el vínculo no depende de dónde vive hoy.

El archivado es una herramienta del panel: el portal del cliente (`accounts/`)
no filtra por estos campos.
"""
from django.db import transaction
from django.utils import timezone

from content.models import Document, DocumentFolder

_ARCHIVE_FIELDS = ['is_archived', 'archived_at', 'archived_via_folder']


class DocumentArchiveError(ValueError):
    """Operación de archivado rechazada por una regla de negocio."""


def archive_document(document):
    """Archiva un documento suelto. Devuelve True si cambió algo."""
    if document.is_archived:
        return False
    document.is_archived = True
    document.archived_at = timezone.now()
    document.archived_via_folder = None
    document.save(update_fields=_ARCHIVE_FIELDS)
    return True


def unarchive_document(document):
    """Restaura un documento archivado. Devuelve True si cambió algo.

    Si su carpeta fue eliminada mientras estaba archivado, el FK ya quedó en
    NULL (on_delete=SET_NULL) y el documento reaparece en «Sin carpeta».
    """
    if not document.is_archived:
        return False
    document.is_archived = False
    document.archived_at = None
    document.archived_via_folder = None
    document.save(update_fields=_ARCHIVE_FIELDS)
    return True


@transaction.atomic
def archive_folder(folder):
    """Archiva la carpeta, sus subcarpetas y todos sus documentos.

    Devuelve ``{'folders': n, 'documents': m}`` con lo que arrastró esta
    llamada. El filtro `is_archived=False` es la memoria de la cascada: lo que
    ya estaba archivado conserva su marca y su `archived_at` original, de modo
    que re-archivar no rejuvenece nada en la vista ordenada por antigüedad.
    """
    now = timezone.now()
    descendant_ids = folder.get_descendant_ids()
    scope_ids = {folder.pk} | descendant_ids

    folders_count = DocumentFolder.objects.filter(
        pk__in=descendant_ids, is_archived=False,
    ).update(is_archived=True, archived_at=now, archived_via_folder=folder)

    documents_count = Document.objects.filter(
        folder_id__in=scope_ids, is_archived=False,
    ).update(is_archived=True, archived_at=now, archived_via_folder=folder)

    # La carpeta sobre la que se actuó siempre queda como archivada a mano.
    DocumentFolder.objects.filter(pk=folder.pk, is_archived=False).update(
        is_archived=True, archived_at=now, archived_via_folder=None,
    )
    folder.refresh_from_db()

    return {'folders': folders_count, 'documents': documents_count}


@transaction.atomic
def unarchive_folder(folder):
    """Restaura la carpeta y exactamente lo que su archivado arrastró.

    Devuelve ``{'folders': n, 'documents': m}``. Lanza `DocumentArchiveError`
    si el padre sigue archivado: la carpeta restaurada no sería raíz ni hija de
    algo visible, así que desaparecería de ambas vistas.
    """
    if folder.parent_id and DocumentFolder.objects.filter(
        pk=folder.parent_id, is_archived=True,
    ).exists():
        raise DocumentArchiveError(
            'Su carpeta contenedora sigue archivada. '
            'Restaura primero la carpeta padre.'
        )

    folders_count = DocumentFolder.objects.filter(
        archived_via_folder=folder, is_archived=True,
    ).update(is_archived=False, archived_at=None, archived_via_folder=None)

    documents_count = Document.objects.filter(
        archived_via_folder=folder, is_archived=True,
    ).update(is_archived=False, archived_at=None, archived_via_folder=None)

    DocumentFolder.objects.filter(pk=folder.pk).update(
        is_archived=False, archived_at=None, archived_via_folder=None,
    )
    folder.refresh_from_db()

    return {'folders': folders_count, 'documents': documents_count}
