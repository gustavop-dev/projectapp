"""Staff-only library. Assets are always downloaded through an authenticated view."""
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from accounts.models import Project
from content.models import Linktree, ProjectBrandAsset
from content.serializers.linktree import LinktreeListSerializer
from content.serializers.project_brand import ProjectBrandAssetSerializer, ProjectBrandAssetUploadSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def project_brand(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        serializer = ProjectBrandAssetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = serializer.save(project=project)
        return Response(ProjectBrandAssetSerializer(asset).data, status=201)
    trees = Linktree.objects.filter(project=project).prefetch_related('buttons')
    return Response({
        'linktrees': LinktreeListSerializer(trees, many=True).data,
        'assets': ProjectBrandAssetSerializer(project.brand_assets.all(), many=True).data,
    })


@api_view(['GET', 'DELETE'])
@permission_classes([IsAdminUser])
def project_brand_asset(request, project_id, asset_id):
    asset = get_object_or_404(ProjectBrandAsset, pk=asset_id, project_id=project_id)
    if request.method == 'DELETE':
        asset.delete()
        return Response(status=204)
    try:
        opened = asset.file.open('rb')
    except FileNotFoundError:
        return Response({'detail': 'El archivo ya no está disponible.'}, status=404)
    response = FileResponse(opened, as_attachment=True, filename=asset.filename,
                            content_type='application/octet-stream')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
