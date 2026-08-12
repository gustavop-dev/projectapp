from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import DocumentFolder
from content.serializers.document_folder import DocumentFolderSerializer
from content.services import document_archive_service
from content.views.document import (
    apply_archive_scope, archive_scope, archived_order_field, search_term,
)


def _annotated_folders(scope):
    """Carpetas del scope pedido, con los contadores activos y archivados.

    Se anotan los cuatro y el serializer elige: `document_count` sigue siendo
    relativo al estado de la carpeta (activa cuenta activos, archivada cuenta
    archivados), y `archived_document_count` es absoluto — es el que deja ver la
    carpeta ACTIVA que todavía guarda archivados, el estado mixto que produce
    una restauración por cadena.

    Compartido por la lista y por las respuestas de archive/unarchive para que
    el payload sea idéntico en ambos casos: el fallback `.count()` del
    serializer sólo entra cuando no hay annotation.
    """
    # distinct=True evita que el JOIN cruzado de las dos relaciones inversas
    # (documents + children) multiplique los conteos entre sí; el `filter=`
    # acota el estado pero no elimina ese cruce. Los cuatro agregados reusan los
    # mismos dos JOINs, así que el riesgo no crece con ellos.
    return apply_archive_scope(DocumentFolder.objects.all(), scope).annotate(
        active_document_count=Count(
            'documents', filter=Q(documents__is_archived=False), distinct=True,
        ),
        archived_document_count=Count(
            'documents', filter=Q(documents__is_archived=True), distinct=True,
        ),
        active_children_count=Count(
            'children', filter=Q(children__is_archived=False), distinct=True,
        ),
        archived_children_count=Count(
            'children', filter=Q(children__is_archived=True), distinct=True,
        ),
    )


def _folder_payload(folder, scope):
    """Serializa una carpeta con los contadores anotados de su scope."""
    annotated = _annotated_folders(scope).filter(pk=folder.pk).first() or folder
    return DocumentFolderSerializer(annotated).data


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_document_folders(request):
    """Lista carpetas por estado, opcionalmente filtradas por nombre.

    La búsqueda devuelve coincidencias planas, sin rellenar con los ancestros:
    la página ya pinta un listado plano mientras hay consulta activa.
    """
    scope = archive_scope(request)
    if scope is None:
        return Response(
            {'scope': 'El estado solicitado no es válido. Usa active, archived o all.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    folders = _annotated_folders(scope)

    search = search_term(request)
    if search:
        folders = folders.filter(name__icontains=search)

    if scope == 'archived':
        folders = folders.order_by(archived_order_field(request), 'order', 'name')
    serializer = DocumentFolderSerializer(folders, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document_folder(request):
    serializer = DocumentFolderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document_folder(request, folder_id):
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    serializer = DocumentFolderSerializer(folder, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_document_folder(request, folder_id):
    """Elimina una carpeta vacía.

    Los conteos NO excluyen lo archivado a propósito: contenido es contenido.
    Si excluyéramos los archivados, borrar una carpeta archivada dejaría a sus
    documentos archivados en la raíz (folder es SET_NULL) sin avisar. Para
    sacar de la vista una carpeta con contenido está archivar, no borrar.
    """
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    document_count = folder.documents.count()
    if document_count:
        return Response(
            {
                'detail': (
                    f'La carpeta tiene {document_count} documento(s). '
                    'Muévelos o elimínalos antes de borrarla.'
                ),
                'document_count': document_count,
            },
            status=status.HTTP_409_CONFLICT,
        )
    children_count = folder.children.count()
    if children_count:
        return Response(
            {
                'detail': (
                    f'La carpeta tiene {children_count} subcarpeta(s). '
                    'Muévelas o elimínalas antes de borrarla.'
                ),
                'children_count': children_count,
            },
            status=status.HTTP_409_CONFLICT,
        )
    folder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def archive_document_folder(request, folder_id):
    """Archiva la carpeta y, en cascada, su contenido.

    A diferencia de eliminar, esto SÍ está permitido con contenido: no destruye
    nada. Devuelve cuánto arrastró para que la UI lo pueda reportar.
    """
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    counts = document_archive_service.archive_folder(folder)
    return Response({
        'folder': _folder_payload(folder, scope='archived'),
        'archived_folders': counts['folders'],
        'archived_documents': counts['documents'],
    })


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def unarchive_document_folder(request, folder_id):
    """Restaura la carpeta, lo que su archivado arrastró, y su cadena de ancestros.

    Antes esto respondía 409 cuando el padre seguía archivado, y con eso una
    subcarpeta arrastrada por la cascada no tenía forma de volver. Ahora la
    cadena se reabre sola y viaja en `restored_chain` para que la UI la nombre;
    `restored_folders`/`restored_documents` siguen contando sólo la cascada
    propia.
    """
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    counts = document_archive_service.unarchive_folder(folder)
    return Response({
        'folder': _folder_payload(folder, scope='active'),
        'restored_folders': counts['folders'],
        'restored_documents': counts['documents'],
        'restored_chain': [
            {'id': ancestor.id, 'name': ancestor.name}
            for ancestor in counts['restored_chain']
        ],
        'moved_to_root': counts['moved_to_root'],
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reorder_document_folders(request):
    ids = request.data.get('ids', [])
    if not isinstance(ids, list):
        return Response({'ids': 'Debe ser una lista.'}, status=status.HTTP_400_BAD_REQUEST)
    folders_by_id = {f.id: f for f in DocumentFolder.objects.filter(pk__in=ids)}
    for order, folder_id in enumerate(ids):
        if folder_id in folders_by_id:
            folders_by_id[folder_id].order = order
    DocumentFolder.objects.bulk_update(folders_by_id.values(), ['order'])
    return Response({'status': 'ok'})
