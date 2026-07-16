from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import ViewMapSettings
from content.serializers.view_map import ViewMapSettingsSerializer


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_view_map_settings(request):
    """Return the view-map panel settings singleton."""
    serializer = ViewMapSettingsSerializer(ViewMapSettings.load())
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_view_map_settings(request):
    """Update the view-map panel settings singleton."""
    serializer = ViewMapSettingsSerializer(
        ViewMapSettings.load(), data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)
