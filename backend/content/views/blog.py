import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from content.models import BlogPost
from content.serializers.blog import (
    BlogPostCreateUpdateSerializer,
    BlogPostDetailSerializer,
    BlogPostListSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def list_blog_posts(request):
    """
    List all published blog posts, ordered by published_at descending.
    """
    qs = BlogPost.objects.filter(is_published=True)
    serializer = BlogPostListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_blog_post(request, slug):
    """
    Retrieve a single published blog post by slug.
    Returns 404 if not found or not published.
    """
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    serializer = BlogPostDetailSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_blog_posts(request):
    """
    List all blog posts (including drafts) for admin management.
    """
    qs = BlogPost.objects.all()
    serializer = BlogPostListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_blog_post(request):
    """
    Create a new blog post.
    """
    serializer = BlogPostCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    post = serializer.save()
    detail = BlogPostDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_blog_post(request, post_id):
    """
    Retrieve full blog post detail for admin editing.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    serializer = BlogPostDetailSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_blog_post(request, post_id):
    """
    Update a blog post's fields.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    serializer = BlogPostCreateUpdateSerializer(
        post, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    detail = BlogPostDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_blog_post(request, post_id):
    """
    Delete a blog post.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
