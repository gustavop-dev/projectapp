from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import CommunicationFolder
from content.serializers.communication_folder import CommunicationFolderSerializer
from content.services import communication_folder_service as service
from content.services.communication_query_service import CommunicationFilterError, _positive_id
from content.services.communication_service import CommunicationError
from content.views.communication import _business_error


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def communication_folders(request):
    if request.method == 'GET':
        folders = CommunicationFolder.objects.all()
        try:
            for field in ('client', 'project'):
                value = _positive_id(request.query_params, field)
                if value:
                    folders = folders.filter(**{f'{field}_id': value})
        except CommunicationFilterError as exc:
            return Response(exc.errors, status=400)
        return Response(CommunicationFolderSerializer(folders, many=True).data)
    serializer = CommunicationFolderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        folder = service.save_folder(data=serializer.validated_data)
    except CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationFolderSerializer(folder).data, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def communication_folder_detail(request, folder_id):
    folder = get_object_or_404(CommunicationFolder, pk=folder_id)
    try:
        if request.method == 'DELETE':
            service.delete_folder(folder)
            return Response(status=204)
        serializer = CommunicationFolderSerializer(folder, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        folder = service.save_folder(folder=folder, data=serializer.validated_data)
    except CommunicationError as exc:
        return _business_error(exc)
    return Response(CommunicationFolderSerializer(folder).data)
