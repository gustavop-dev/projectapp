from collections import defaultdict

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import Document, DocumentFolder
from content.models.document_folder import MAX_FOLDER_DEPTH
from content.serializers.document_folder import DocumentFolderSerializer


def _build_tree_context(folders=None):
    """Pre-compute tree maps so the serializer resolves path/depth/count in O(1).

    Returns dict suitable for `context=` of DocumentFolderSerializer.
    """
    folders = list(
        folders if folders is not None
        else DocumentFolder.objects.annotate(_direct_count=Count('documents'))
    )
    folder_by_id = {f.pk: f for f in folders}
    children_map = defaultdict(list)
    direct_counts = {}
    for f in folders:
        children_map[f.parent_id].append(f)
        direct_counts[f.pk] = getattr(f, '_direct_count', None)
        if direct_counts[f.pk] is None:
            direct_counts[f.pk] = f.documents.count()
    # Compute recursive_counts bottom-up via post-order DFS from each root.
    recursive_counts = {}

    def _accumulate(node):
        total = direct_counts.get(node.pk, 0)
        for child in children_map.get(node.pk, []):
            total += _accumulate(child)
        recursive_counts[node.pk] = total
        return total

    for root in children_map.get(None, []):
        _accumulate(root)
    return {
        'folder_by_id': folder_by_id,
        'children_map': children_map,
        'direct_counts': direct_counts,
        'recursive_counts': recursive_counts,
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_document_folders(request):
    folders = list(
        DocumentFolder.objects.annotate(_direct_count=Count('documents')).order_by('order', 'name')
    )
    context = _build_tree_context(folders)
    serializer = DocumentFolderSerializer(folders, many=True, context=context)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document_folder(request):
    serializer = DocumentFolderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    out = DocumentFolderSerializer(serializer.instance, context=_build_tree_context())
    return Response(out.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document_folder(request, folder_id):
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    serializer = DocumentFolderSerializer(folder, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    out = DocumentFolderSerializer(serializer.instance, context=_build_tree_context())
    return Response(out.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_document_folder(request, folder_id):
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    has_children = folder.children.exists()
    descendant_ids = folder.get_descendant_ids(include_self=True)
    document_count = Document.objects.filter(folder_id__in=descendant_ids).count()
    if has_children or document_count:
        reasons = []
        if has_children:
            reasons.append('has_children')
        if document_count:
            reasons.append('has_documents')
        return Response(
            {
                'detail': (
                    'La carpeta no se puede eliminar: '
                    + (
                        'contiene subcarpetas. ' if has_children else ''
                    )
                    + (
                        f'Hay {document_count} documento(s) en la carpeta o sus subcarpetas.'
                        if document_count else ''
                    )
                ).strip(),
                'document_count': document_count,
                'has_children': has_children,
                'reasons': reasons,
            },
            status=status.HTTP_409_CONFLICT,
        )
    folder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reorder_document_folders(request):
    ids = request.data.get('ids', [])
    parent_id = request.data.get('parent_id', None)
    if not isinstance(ids, list):
        return Response({'ids': 'Must be a list.'}, status=status.HTTP_400_BAD_REQUEST)
    if not ids:
        return Response({'status': 'ok'})
    folders_by_id = {f.id: f for f in DocumentFolder.objects.filter(pk__in=ids)}
    # Reject if any folder doesn't belong to the declared parent scope.
    for fid in ids:
        f = folders_by_id.get(fid)
        if f is None:
            return Response(
                {'ids': f'Folder {fid} not found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (f.parent_id or None) != (parent_id or None):
            return Response(
                {'ids': 'All folders must share the same parent.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    for order, folder_id in enumerate(ids):
        folders_by_id[folder_id].order = order
    DocumentFolder.objects.bulk_update(folders_by_id.values(), ['order'])
    return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def move_document_folder(request, folder_id):
    """Reparent a folder and optionally place it at a position among new siblings."""
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    raw_parent = request.data.get('parent_id', None)
    position = request.data.get('position', None)

    if raw_parent in (None, '', 'null'):
        new_parent = None
    else:
        try:
            new_parent = DocumentFolder.objects.get(pk=int(raw_parent))
        except (ValueError, TypeError, DocumentFolder.DoesNotExist):
            return Response(
                {'parent_id': 'Carpeta padre inválida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Validate cycle + depth using the serializer's logic.
    serializer = DocumentFolderSerializer(
        folder, data={'parent': new_parent.pk if new_parent else None}, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        folder.parent = new_parent
        folder.save(update_fields=['parent', 'updated_at'])

        siblings = list(
            DocumentFolder.objects.filter(parent=new_parent)
            .exclude(pk=folder.pk)
            .order_by('order', 'name')
        )
        if isinstance(position, int) and 0 <= position <= len(siblings):
            siblings.insert(position, folder)
        else:
            siblings.append(folder)
        for idx, sib in enumerate(siblings):
            sib.order = idx
        DocumentFolder.objects.bulk_update(siblings, ['order'])

    folder.refresh_from_db()
    out = DocumentFolderSerializer(folder, context=_build_tree_context())
    return Response(out.data)
