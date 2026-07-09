from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from content.models import HourPackage, Nationality
from content.serializers.hour_packages import (
    HourPackageAdminListSerializer,
    HourPackageAdminDetailSerializer,
    HourPackageCreateUpdateSerializer,
)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only) — hour-package catalog per nationality
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_hour_packages(request):
    """List hour packages, optionally filtered by ?nationality=COL|MEX|USA."""
    qs = HourPackage.objects.all()
    nationality = request.query_params.get('nationality')
    if nationality:
        if nationality not in Nationality.values:
            return Response(
                {'nationality': ['Nacionalidad inválida. Usa COL, MEX o USA.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = qs.filter(nationality=nationality)
    serializer = HourPackageAdminListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_hour_package(request):
    """Create a new hour package."""
    serializer = HourPackageCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    package = serializer.save()
    detail = HourPackageAdminDetailSerializer(package)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_hour_package(request, package_id):
    """Retrieve full hour package detail for admin editing."""
    package = get_object_or_404(HourPackage, pk=package_id)
    serializer = HourPackageAdminDetailSerializer(package)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_hour_package(request, package_id):
    """Update an hour package's fields."""
    package = get_object_or_404(HourPackage, pk=package_id)
    serializer = HourPackageCreateUpdateSerializer(
        package, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    detail = HourPackageAdminDetailSerializer(package)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_hour_package(request, package_id):
    """Delete an hour package."""
    package = get_object_or_404(HourPackage, pk=package_id)
    package.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
