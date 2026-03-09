import copy as _copy

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from content.models import PortfolioWork
from content.serializers.portfolio_works import (
    PortfolioWorkListSerializer,
    PortfolioWorkDetailSerializer,
    PortfolioWorkAdminListSerializer,
    PortfolioWorkAdminDetailSerializer,
    PortfolioWorkCreateUpdateSerializer,
    PortfolioWorkFromJSONSerializer,
    PORTFOLIO_JSON_TEMPLATE,
)


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def portfolio_works_list(request):
    """
    Legacy endpoint — list all portfolio works (backwards compat).
    """
    qs = PortfolioWork.objects.all()
    serializer = PortfolioWorkListSerializer(
        qs, many=True, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_portfolio_works(request):
    """
    List published portfolio works.
    Accepts ?lang=es|en query param.
    """
    qs = PortfolioWork.objects.filter(is_published=True)
    serializer = PortfolioWorkListSerializer(
        qs, many=True, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_portfolio_work(request, slug):
    """
    Retrieve a single published portfolio work by slug.
    Accepts ?lang=es|en query param (default 'es').
    """
    work = get_object_or_404(PortfolioWork, slug=slug, is_published=True)
    serializer = PortfolioWorkDetailSerializer(
        work, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def portfolio_sitemap_data(request):
    """
    Return a lightweight list of published portfolio works for dynamic sitemap generation.
    Each entry contains slug and updated_at.
    """
    qs = PortfolioWork.objects.filter(is_published=True).values('slug', 'updated_at')
    return Response(list(qs), status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_portfolio_works(request):
    """List all portfolio works (including drafts) for admin management."""
    qs = PortfolioWork.objects.all()
    serializer = PortfolioWorkAdminListSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_portfolio_work(request):
    """Create a new portfolio work."""
    serializer = PortfolioWorkCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    work = serializer.save()
    detail = PortfolioWorkAdminDetailSerializer(work)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_portfolio_work(request, work_id):
    """Retrieve full portfolio work detail for admin editing."""
    work = get_object_or_404(PortfolioWork, pk=work_id)
    serializer = PortfolioWorkAdminDetailSerializer(work)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_portfolio_work(request, work_id):
    """Update a portfolio work's fields."""
    work = get_object_or_404(PortfolioWork, pk=work_id)
    serializer = PortfolioWorkCreateUpdateSerializer(
        work, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    detail = PortfolioWorkAdminDetailSerializer(work)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_portfolio_work(request, work_id):
    """Delete a portfolio work."""
    work = get_object_or_404(PortfolioWork, pk=work_id)
    work.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_portfolio_work(request, work_id):
    """Duplicate a portfolio work as a new draft."""
    work = get_object_or_404(PortfolioWork, pk=work_id)
    new_work = PortfolioWork.objects.create(
        title_es=f'{work.title_es} (copia)',
        title_en=f'{work.title_en} (copy)',
        slug='',
        excerpt_es=work.excerpt_es,
        excerpt_en=work.excerpt_en,
        content_json_es=_copy.deepcopy(work.content_json_es),
        content_json_en=_copy.deepcopy(work.content_json_en),
        project_url=work.project_url,
        cover_image_url=work.cover_image_url,
        category_title_es=work.category_title_es,
        category_title_en=work.category_title_en,
        meta_title_es=work.meta_title_es,
        meta_title_en=work.meta_title_en,
        meta_description_es=work.meta_description_es,
        meta_description_en=work.meta_description_en,
        meta_keywords_es=work.meta_keywords_es,
        meta_keywords_en=work.meta_keywords_en,
        order=work.order,
        is_published=False,
        published_at=None,
    )
    detail = PortfolioWorkAdminDetailSerializer(new_work)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def upload_portfolio_cover_image(request, work_id):
    """Upload a cover image file for a portfolio work."""
    work = get_object_or_404(PortfolioWork, pk=work_id)
    cover = request.FILES.get('cover_image')
    if not cover:
        return Response(
            {'cover_image': 'No file provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    work.cover_image = cover
    work.save(update_fields=['cover_image', 'updated_at'])
    detail = PortfolioWorkAdminDetailSerializer(work)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_portfolio_work_from_json(request):
    """Create a portfolio work from a complete JSON payload."""
    serializer = PortfolioWorkFromJSONSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    work = PortfolioWork.objects.create(
        title_es=data['title_es'],
        title_en=data['title_en'],
        excerpt_es=data.get('excerpt_es', ''),
        excerpt_en=data.get('excerpt_en', ''),
        content_json_es=data['content_json_es'],
        content_json_en=data.get('content_json_en') or {},
        project_url=data['project_url'],
        cover_image_url=data.get('cover_image_url', ''),
        is_published=data.get('is_published', False),
        order=data.get('order', 0),
        meta_title_es=data.get('meta_title_es', ''),
        meta_title_en=data.get('meta_title_en', ''),
        meta_description_es=data.get('meta_description_es', ''),
        meta_description_en=data.get('meta_description_en', ''),
        meta_keywords_es=data.get('meta_keywords_es', ''),
        meta_keywords_en=data.get('meta_keywords_en', ''),
    )
    detail = PortfolioWorkAdminDetailSerializer(work)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_portfolio_json_template(request):
    """Return a downloadable JSON template for portfolio work creation."""
    template = {
        'title_es': 'Título del proyecto en español',
        'title_en': 'Project title in English',
        'excerpt_es': 'Tagline corto en español.',
        'excerpt_en': 'Short tagline in English.',
        'project_url': 'https://example.com',
        'content_json_es': _copy.deepcopy(PORTFOLIO_JSON_TEMPLATE),
        'content_json_en': _copy.deepcopy(PORTFOLIO_JSON_TEMPLATE),
        'cover_image_url': '',
        'is_published': False,
        'order': 0,
        'meta_title_es': '',
        'meta_title_en': '',
        'meta_description_es': '',
        'meta_description_en': '',
        'meta_keywords_es': '',
        'meta_keywords_en': '',
    }
    return Response(template, status=status.HTTP_200_OK)