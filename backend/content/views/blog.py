import copy as _copy
import logging
from xml.sax.saxutils import escape as xml_escape

from django.http import HttpResponse
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


BASE_URL = 'https://projectapp.co'

STATIC_SITEMAP_PAGES = [
    ('/en-us', '/es-co', 'weekly', '1.0'),
    ('/es-co', '/en-us', 'weekly', '1.0'),
    ('/en-us/landing-web-design', '/es-co/landing-web-design', 'weekly', '0.9'),
    ('/es-co/landing-web-design', '/en-us/landing-web-design', 'weekly', '0.9'),
    ('/en-us/about-us', '/es-co/about-us', 'monthly', '0.9'),
    ('/es-co/about-us', '/en-us/about-us', 'monthly', '0.9'),
    ('/en-us/web-designs', '/es-co/web-designs', 'weekly', '0.9'),
    ('/es-co/web-designs', '/en-us/web-designs', 'weekly', '0.9'),
    ('/en-us/portfolio-works', '/es-co/portfolio-works', 'weekly', '0.9'),
    ('/es-co/portfolio-works', '/en-us/portfolio-works', 'weekly', '0.9'),
    ('/en-us/custom-software', '/es-co/custom-software', 'monthly', '0.9'),
    ('/es-co/custom-software', '/en-us/custom-software', 'monthly', '0.9'),
    ('/en-us/3d-animations', '/es-co/3d-animations', 'weekly', '0.8'),
    ('/es-co/3d-animations', '/en-us/3d-animations', 'weekly', '0.8'),
    ('/en-us/e-commerce-prices', '/es-co/e-commerce-prices', 'monthly', '0.7'),
    ('/es-co/e-commerce-prices', '/en-us/e-commerce-prices', 'monthly', '0.7'),
    ('/en-us/hosting', '/es-co/hosting', 'monthly', '0.7'),
    ('/es-co/hosting', '/en-us/hosting', 'monthly', '0.7'),
    ('/en-us/contact', '/es-co/contact', 'monthly', '0.6'),
    ('/es-co/contact', '/en-us/contact', 'monthly', '0.6'),
]


def serve_sitemap_xml(request):
    """Serve a dynamic sitemap.xml combining static pages and published blog posts."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        '',
    ]

    for path, alt, changefreq, priority in STATIC_SITEMAP_PAGES:
        hl_self = 'en-us' if path.startswith('/en-us') else 'es-co'
        hl_alt = 'es-co' if hl_self == 'en-us' else 'en-us'
        lines.append('  <url>')
        lines.append(f'    <loc>{BASE_URL}{xml_escape(path)}</loc>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{hl_self}" href="{BASE_URL}{xml_escape(path)}" />')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{hl_alt}" href="{BASE_URL}{xml_escape(alt)}" />')
        lines.append(f'    <changefreq>{changefreq}</changefreq>')
        lines.append(f'    <priority>{priority}</priority>')
        lines.append('  </url>')

    lines.append('')
    lines.append('  <!-- Blog -->')
    lines.append('  <url>')
    lines.append(f'    <loc>{BASE_URL}/blog</loc>')
    lines.append('    <changefreq>daily</changefreq>')
    lines.append('    <priority>0.8</priority>')
    lines.append('  </url>')

    posts = BlogPost.objects.filter(is_published=True).values('slug', 'updated_at')
    for post in posts:
        lastmod = post['updated_at'].strftime('%Y-%m-%d') if post['updated_at'] else ''
        lines.append('  <url>')
        lines.append(f'    <loc>{BASE_URL}/blog/{xml_escape(post["slug"])}</loc>')
        if lastmod:
            lines.append(f'    <lastmod>{lastmod}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.7</priority>')
        lines.append('  </url>')

    lines.append('')
    lines.append('</urlset>')
    lines.append('')

    xml = '\n'.join(lines)
    response = HttpResponse(xml, content_type='application/xml; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=3600, s-maxage=3600'
    return response


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def list_blog_posts(request):
    """
    List published blog posts with pagination.
    Accepts ?lang=es|en, ?page=1, ?page_size=6 query params.
    Returns {results, count, page, page_size, total_pages}.
    """
    qs = BlogPost.objects.filter(is_published=True)

    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(50, max(1, int(request.query_params.get('page_size', 6))))
    except (ValueError, TypeError):
        page_size = 6

    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size
    page_qs = qs[start:end]

    serializer = BlogPostListSerializer(
        page_qs, many=True, context={'request': request}
    )
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }, status=status.HTTP_200_OK)


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
        author=data.get('author', 'projectapp-team'),
        meta_title_es=data.get('meta_title_es', ''),
        meta_title_en=data.get('meta_title_en', ''),
        meta_description_es=data.get('meta_description_es', ''),
        meta_description_en=data.get('meta_description_en', ''),
        meta_keywords_es=data.get('meta_keywords_es', ''),
        meta_keywords_en=data.get('meta_keywords_en', ''),
        cover_image_credit=data.get('cover_image_credit', ''),
        cover_image_credit_url=data.get('cover_image_credit_url', ''),
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
        'author': 'projectapp-team',
        'content_json_es': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'content_json_en': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'cover_image_url': '',
        'cover_image_credit': '',
        'cover_image_credit_url': '',
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
        'meta_keywords_es': '',
        'meta_keywords_en': '',
        '_available_categories': AVAILABLE_CATEGORIES,
        '_available_authors': [
            {'slug': slug, 'label': label}
            for slug, label in BlogPost.AUTHOR_CHOICES
        ],
        '_block_instructions': {
            'content': 'Texto de párrafo para la sección. String simple.',
            'list': 'Array de strings. Se renderiza como lista con íconos de check.',
            'subsections': 'Array de {title, description}. Se renderiza como tarjetas.',
            'timeline': 'Array de {step, description}. Se renderiza como pasos numerados verticales.',
            'examples': 'Array de strings. Se renderiza como grid de tarjetas de ejemplo.',
            'image': '{url, alt, credit, credit_url}. Imagen inline con crédito del autor (ej. Unsplash).',
            'quote': '{text, author}. Cita destacada con borde lemon.',
            'callout': '{type, title, text}. Caja resaltada. type: tip | warning | info | note.',
            'video': '{url, title}. Embed de YouTube o Vimeo. Pegar URL normal del video.',
            'key_takeaways': 'Array de strings. Caja de resumen numerada con ícono 💡. Los motores de IA extraen esto.',
            'faq': 'Array de {question, answer}. Preguntas frecuentes con acordeón. Genera FAQ Schema para Google.',
        },
    }
    return Response(template, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def blog_sitemap_data(request):
    """
    Return a lightweight list of published blog posts for dynamic sitemap generation.
    Each entry contains slug and updated_at.
    """
    qs = BlogPost.objects.filter(is_published=True).values('slug', 'updated_at')
    return Response(list(qs), status=status.HTTP_200_OK)


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
