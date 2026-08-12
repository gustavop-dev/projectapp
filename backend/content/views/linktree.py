from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from content.models import Linktree
from content.serializers.linktree import (
    LinktreeCreateUpdateSerializer,
    LinktreeDetailSerializer,
    LinktreeListSerializer,
    PublicLinktreeSerializer,
    normalize_handle,
)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_linktrees(request):
    """List all linktrees for admin management."""
    qs = Linktree.objects.all()
    serializer = LinktreeListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_linktree(request, linktree_id):
    """Full detail (with buttons) for the panel editor."""
    linktree = get_object_or_404(
        Linktree.objects.prefetch_related('buttons'), pk=linktree_id
    )
    serializer = LinktreeDetailSerializer(linktree)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_linktree(request):
    """Create a linktree, optionally with its full buttons array."""
    serializer = LinktreeCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    linktree = serializer.save()
    detail = LinktreeDetailSerializer(linktree)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_linktree(request, linktree_id):
    """Update a linktree; a `buttons` array replaces the existing buttons."""
    linktree = get_object_or_404(Linktree, pk=linktree_id)
    serializer = LinktreeCreateUpdateSerializer(linktree, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    linktree.refresh_from_db()
    detail = LinktreeDetailSerializer(linktree)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_linktree(request, linktree_id):
    """Delete a linktree (QR cards pointing to it fall back to SET_NULL)."""
    linktree = get_object_or_404(Linktree, pk=linktree_id)
    linktree.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Public endpoint
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def linktree_short_redirect(request, handle):
    """
    Root-level clean URL: /lk/<handle> (with or without '@', no locale
    prefix) 302-redirects to the locale-prefixed SPA page. Registered in
    projectapp/urls.py before the serve_nuxt catch-all.
    """
    linktree = get_object_or_404(
        Linktree, handle=normalize_handle(handle), is_active=True
    )
    return HttpResponseRedirect(f'/es-co{linktree.public_path}')


@api_view(['GET'])
@permission_classes([AllowAny])
def public_linktree(request, handle):
    """Resolve a public linktree by handle (with or without the '@')."""
    linktree = get_object_or_404(
        Linktree.objects.prefetch_related('buttons'),
        handle=normalize_handle(handle),
        is_active=True,
    )
    serializer = PublicLinktreeSerializer(linktree)
    return Response(serializer.data, status=status.HTTP_200_OK)
