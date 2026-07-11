"""
LinkedIn integration views.

Handles OAuth callback (with CSRF state validation), connection status,
and rate-limited blog-to-LinkedIn publishing.
"""

import logging
import math
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import BlogPost, LinkedInPost
from content.serializers.linkedin_post import LinkedInPostSerializer
from content.services.linkedin_post_service import (
    apply_schedule_transition,
    publish_linkedin_post_now,
)
from content.services.linkedin_service import (
    exchange_code_for_token,
    get_authorization_url,
    get_connection_status,
    publish_blog_to_linkedin,
)

logger = logging.getLogger(__name__)

BLOG_PUBLIC_BASE = 'https://projectapp.co/blog'

# OAuth state cache prefix and TTL
_STATE_PREFIX = 'linkedin_oauth_state:'
_STATE_TTL = 600  # 10 minutes

# Rate limit: minimum interval between LinkedIn publishes per post
_PUBLISH_COOLDOWN = timedelta(minutes=10)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def linkedin_auth_url(request):
    """
    Return the LinkedIn OAuth authorization URL with a CSRF state token.

    The state is stored in Redis cache for 10 minutes. The frontend must
    pass it back on callback for validation.
    """
    state = secrets.token_urlsafe(32)
    cache.set(f'{_STATE_PREFIX}{state}', True, timeout=_STATE_TTL)
    url = get_authorization_url(state=state)
    return Response({'authorization_url': url, 'state': state})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def linkedin_callback(request):
    """
    Exchange the LinkedIn authorization code for an access token.

    Expects JSON body: { "code": "<auth_code>", "state": "<csrf_state>" }
    Validates the state parameter against the cache before proceeding.
    """
    # --- Validate CSRF state ---
    state = request.data.get('state')
    if not state:
        return Response(
            {'error': 'Missing OAuth state parameter.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cache_key = f'{_STATE_PREFIX}{state}'
    if not cache.get(cache_key):
        return Response(
            {'error': 'Invalid or expired OAuth state. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    cache.delete(cache_key)

    # --- Check for errors from LinkedIn ---
    error = request.data.get('error')
    if error:
        return Response(
            {'error': f'LinkedIn authorization error: {error}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- Exchange code ---
    code = request.data.get('code')
    if not code:
        return Response(
            {'error': 'Authorization code is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        exchange_code_for_token(code)
        connection = get_connection_status()
        return Response({
            'success': True,
            'message': 'LinkedIn connected successfully.',
            'connection': connection,
        })
    except ValueError as exc:
        logger.error('LinkedIn callback failed: %s', exc)
        return Response(
            {'error': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def linkedin_status(request):
    """Check LinkedIn connection status."""
    connection = get_connection_status()
    return Response(connection)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def publish_to_linkedin(request, post_id):
    """
    Publish a blog post summary to LinkedIn.

    Rate-limited to one publish per post every 10 minutes to prevent
    accidental duplicate posts.
    """
    post = BlogPost.objects.filter(pk=post_id).first()
    if not post:
        return Response(
            {'error': 'Blog post not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # --- Rate limit check ---
    if post.linkedin_published_at:
        threshold = tz.now() - _PUBLISH_COOLDOWN
        if post.linkedin_published_at >= threshold:
            remaining_seconds = (post.linkedin_published_at - threshold).total_seconds()
            remaining_minutes = math.ceil(remaining_seconds / 60)
            return Response(
                {'error': f'This post was published to LinkedIn recently. Wait {remaining_minutes} min.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    # English is the default: LinkedIn content targets the US market.
    lang = request.data.get('lang', 'en')
    summary = post.linkedin_summary_es if lang == 'es' else post.linkedin_summary_en
    title = post.title_es if lang == 'es' else post.title_en

    if not summary:
        return Response(
            {'error': f'LinkedIn summary ({lang}) is empty. Please add a summary first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Build blog URL
    blog_url = f'{BLOG_PUBLIC_BASE}/{post.slug}'

    # Get cover image URL
    cover_image_url = ''
    if post.cover_image_url:
        cover_image_url = post.cover_image_url
    elif post.cover_image:
        cover_image_url = f'https://projectapp.co{post.cover_image.url}'

    description = post.excerpt_es if lang == 'es' else post.excerpt_en

    try:
        result = publish_blog_to_linkedin(
            summary=summary,
            blog_url=blog_url,
            title=title,
            cover_image_url=cover_image_url,
            description=description,
        )
    except ValueError as exc:
        return Response(
            {'error': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if result['success']:
        post.linkedin_post_id = result['post_id']
        post.linkedin_published_at = tz.now()
        post.save(update_fields=['linkedin_post_id', 'linkedin_published_at'])

    return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_502_BAD_GATEWAY)


# ---------------------------------------------------------------------------
# Freeform LinkedIn posts (panel module)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_linkedin_posts(request):
    """List freeform LinkedIn posts, newest first."""
    posts = LinkedInPost.objects.all()
    return Response(LinkedInPostSerializer(posts, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_linkedin_post(request):
    """Create a freeform LinkedIn post (draft, or scheduled when scheduled_at set)."""
    serializer = LinkedInPostSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    post = serializer.save()
    apply_schedule_transition(post)
    return Response(
        LinkedInPostSerializer(post).data, status=status.HTTP_201_CREATED,
    )


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_linkedin_post(request, post_id):
    """Update a draft/scheduled/failed post. Published posts are immutable."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if post.status == LinkedInPost.STATUS_PUBLISHED:
        return Response(
            {'error': 'Un post ya publicado no se puede editar.'},
            status=status.HTTP_409_CONFLICT,
        )
    data = request.data.copy()
    if data.get('scheduled_at') == '':
        data['scheduled_at'] = None
    serializer = LinkedInPostSerializer(post, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    post = serializer.save()
    apply_schedule_transition(post)
    return Response(LinkedInPostSerializer(post).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def publish_linkedin_post(request, post_id):
    """Publish a freeform LinkedIn post immediately."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    result = publish_linkedin_post_now(post)

    if result.get('already'):
        return Response({'error': result['message']}, status=status.HTTP_409_CONFLICT)
    if result.get('not_connected'):
        return Response({'error': result['message']}, status=status.HTTP_400_BAD_REQUEST)

    post.refresh_from_db()
    payload = LinkedInPostSerializer(post).data
    payload['message'] = result['message']
    return Response(
        payload,
        status=status.HTTP_200_OK if result['success'] else status.HTTP_502_BAD_GATEWAY,
    )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_linkedin_post(request, post_id):
    """Delete a freeform LinkedIn post (local record only)."""
    post = LinkedInPost.objects.filter(pk=post_id).first()
    if not post:
        return Response({'error': 'Post no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
