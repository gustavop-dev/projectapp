from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import DocumentTag
from content.serializers.document_tag import DocumentTagSerializer


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_document_tags(request):
    tags = DocumentTag.objects.all()
    serializer = DocumentTagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_document_tag(request):
    serializer = DocumentTagSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_document_tag(request, tag_id):
    tag = get_object_or_404(DocumentTag, pk=tag_id)
    serializer = DocumentTagSerializer(tag, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_document_tag(request, tag_id):
    tag = get_object_or_404(DocumentTag, pk=tag_id)
    tag.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
