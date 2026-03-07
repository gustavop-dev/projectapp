import copy as _copy
import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from content.models import BlogPost
from content.serializers.blog import (
    BlogPostAdminDetailSerializer,
    BlogPostAdminListSerializer,
    BlogPostCreateUpdateSerializer,
    BlogPostDetailSerializer,
    BlogPostFromJSONSerializer,
    BlogPostListSerializer,
    AVAILABLE_CATEGORIES,
    BLOG_JSON_TEMPLATE,
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
    Accepts ?lang=es|en query param (default 'es').
    """
    qs = BlogPost.objects.filter(is_published=True)
    serializer = BlogPostListSerializer(
        qs, many=True, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_blog_post(request, slug):
    """
    Retrieve a single published blog post by slug.
    Accepts ?lang=es|en query param (default 'es').
    Returns 404 if not found or not published.
    """
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    serializer = BlogPostDetailSerializer(
        post, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_blog_posts(request):
    """
    List all blog posts (including drafts) for admin management.
    Returns all bilingual fields.
    """
    qs = BlogPost.objects.all()
    serializer = BlogPostAdminListSerializer(qs, many=True)
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
    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_blog_post(request, post_id):
    """
    Retrieve full blog post detail for admin editing.
    Returns all bilingual fields.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    serializer = BlogPostAdminDetailSerializer(post)
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
    detail = BlogPostAdminDetailSerializer(post)
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


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_blog_post_from_json(request):
    """
    Create a blog post from a complete JSON payload.

    Mirrors the proposal create-from-json pattern: accepts metadata
    and structured content_json in a single request.
    """
    serializer = BlogPostFromJSONSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    post = BlogPost.objects.create(
        title_es=data['title_es'],
        title_en=data['title_en'],
        excerpt_es=data['excerpt_es'],
        excerpt_en=data['excerpt_en'],
        content_json_es=data['content_json_es'],
        content_json_en=data.get('content_json_en') or {},
        cover_image_url=data.get('cover_image_url', ''),
        sources=data.get('sources', []),
        category=data.get('category', ''),
        read_time_minutes=data.get('read_time_minutes', 0),
        is_featured=data.get('is_featured', False),
        is_published=data.get('is_published', False),
        meta_title_es=data.get('meta_title_es', ''),
        meta_title_en=data.get('meta_title_en', ''),
        meta_description_es=data.get('meta_description_es', ''),
        meta_description_en=data.get('meta_description_en', ''),
    )

    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_blog_json_template(request):
    """
    Return a downloadable JSON template for blog post creation.
    Includes all section types with placeholder content.
    """
    template = {
        'title_es': 'Título del artículo en español',
        'title_en': 'Article title in English',
        'excerpt_es': 'Resumen corto en español (1-2 oraciones).',
        'excerpt_en': 'Short summary in English (1-2 sentences).',
        'content_json_es': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'content_json_en': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'sources': [
            {'name': 'Source Name', 'url': 'https://example.com'},
        ],
        'category': 'technology',
        'read_time_minutes': 8,
        'is_featured': False,
        'is_published': False,
        'meta_title_es': '',
        'meta_title_en': '',
        'meta_description_es': '',
        'meta_description_en': '',
        '_available_categories': AVAILABLE_CATEGORIES,
    }
    return Response(template, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_blog_post(request, post_id):
    """
    Duplicate a blog post: creates a deep copy reset to draft status.
    """
    post = get_object_or_404(BlogPost, pk=post_id)

    new_post = BlogPost.objects.create(
        title_es=f'{post.title_es} (copia)',
        title_en=f'{post.title_en} (copy)',
        slug='',
        excerpt_es=post.excerpt_es,
        excerpt_en=post.excerpt_en,
        content_es=post.content_es,
        content_en=post.content_en,
        content_json_es=_copy.deepcopy(post.content_json_es),
        content_json_en=_copy.deepcopy(post.content_json_en),
        cover_image_url=post.cover_image_url,
        sources=_copy.deepcopy(post.sources),
        category=post.category,
        read_time_minutes=post.read_time_minutes,
        is_featured=False,
        meta_title_es=post.meta_title_es,
        meta_title_en=post.meta_title_en,
        meta_description_es=post.meta_description_es,
        meta_description_en=post.meta_description_en,
        is_published=False,
        published_at=None,
    )

    detail = BlogPostAdminDetailSerializer(new_post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def upload_blog_cover_image(request, post_id):
    """
    Upload a cover image file for a blog post.
    Expects multipart/form-data with a 'cover_image' file field.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    cover = request.FILES.get('cover_image')
    if not cover:
        return Response(
            {'cover_image': 'No file provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    post.cover_image = cover
    post.save(update_fields=['cover_image', 'updated_at'])

    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_200_OK)
