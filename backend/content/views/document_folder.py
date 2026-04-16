from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import DocumentFolder
from content.serializers.document_folder import DocumentFolderSerializer


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_document_folders(request):
    folders = DocumentFolder.objects.annotate(document_count=Count('documents'))
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
    folder = get_object_or_404(DocumentFolder, pk=folder_id)
    folder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reorder_document_folders(request):
    ids = request.data.get('ids', [])
    if not isinstance(ids, list):
        return Response({'ids': 'Must be a list.'}, status=status.HTTP_400_BAD_REQUEST)
    folders_by_id = {f.id: f for f in DocumentFolder.objects.filter(pk__in=ids)}
    for order, folder_id in enumerate(ids):
        if folder_id in folders_by_id:
            folders_by_id[folder_id].order = order
    DocumentFolder.objects.bulk_update(folders_by_id.values(), ['order'])
    return Response({'status': 'ok'})
