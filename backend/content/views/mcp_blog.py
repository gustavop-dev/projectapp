"""
Blog Publisher MCP: public JSON-RPC endpoint (token-authenticated) and
the panel management endpoints backing /panel/mcps.
"""
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from content.mcp.protocol import handle_message
from content.mcp.tools import BLOG_TOOLS
from content.models import McpConnector
from content.permissions import IsSuperUser

logger = logging.getLogger(__name__)

LAST_USED_TOUCH_SECONDS = 60

# One entry per exposed MCP connector: slug -> tool registry.
TOOLS_BY_SLUG = {
    'blog': BLOG_TOOLS,
}


class McpEndpointThrottle(AnonRateThrottle):
    scope = 'mcp'


class McpContentNegotiation(DefaultContentNegotiation):
    """
    MCP clients probe with Accept: text/event-stream (SSE detection). DRF's
    default negotiation raises 406 before the view runs, but the Streamable
    HTTP spec requires a plain 405 for that probe. Fall back to the first
    renderer (JSON) instead of erroring so the view controls the response.
    """

    def select_renderer(self, request, renderers, format_suffix=None):
        try:
            return super().select_renderer(request, renderers, format_suffix)
        except exceptions.NotAcceptable:
            return (renderers[0], renderers[0].media_type)


def _origin_is_foreign(request):
    """
    Streamable HTTP spec: servers MUST validate the Origin header (DNS
    rebinding defense). claude.ai's MCP client DOES send
    Origin: https://claude.ai, so known MCP client origins are allowed
    alongside our own host; anything else is rejected.
    """
    origin = request.headers.get('Origin')
    if not origin:
        return False
    if origin in getattr(settings, 'MCP_ALLOWED_ORIGINS', []):
        return False
    return urlparse(origin).netloc != request.get_host()


def _touch_last_used(connector):
    now = tz.now()
    if connector.last_used_at and (now - connector.last_used_at).total_seconds() < LAST_USED_TOUCH_SECONDS:
        return
    McpConnector.objects.filter(pk=connector.pk).update(last_used_at=now)


@api_view(['POST'])
@authentication_classes([])  # token in URL is the credential; no session ⇒ no CSRF
@permission_classes([AllowAny])
@throttle_classes([McpEndpointThrottle])
def mcp_endpoint(request, slug, token):
    """
    MCP Streamable HTTP endpoint for a connector (e.g. blog).
    Plain-JSON responses only (no SSE) — WSGI-compatible by design. DRF
    answers GET (SSE probe) and DELETE (session termination) with the
    spec-mandated 405; McpContentNegotiation keeps an SSE-only Accept
    header from short-circuiting into a 406.
    """
    if _origin_is_foreign(request):
        return HttpResponse(status=403)

    tools = TOOLS_BY_SLUG.get(slug)
    connector = McpConnector.objects.filter(slug=slug, is_active=True).first()
    if tools is None or connector is None or not connector.check_token(token):
        raise Http404

    message = request.data
    http_status, payload = handle_message(message, tools)

    if isinstance(message, dict) and message.get('method') == 'tools/call':
        _touch_last_used(connector)

    if payload is None:
        return Response(status=http_status)
    return Response(payload, status=http_status)


# api_view exposes the wrapped APIView class as .cls; override negotiation so
# an SSE-only Accept header reaches the view instead of 406ing in initial().
mcp_endpoint.cls.content_negotiation_class = McpContentNegotiation


# ---------------------------------------------------------------------------
# Panel management endpoints (/panel/mcps) — session + CSRF, superuser only
# ---------------------------------------------------------------------------

def _connector_payload(connector):
    tools = TOOLS_BY_SLUG.get(connector.slug, [])
    return {
        'slug': connector.slug,
        'name': connector.name,
        'description': connector.description,
        'is_active': connector.is_active,
        'has_token': bool(connector.token_hash),
        'token_prefix': connector.token_prefix,
        'last_used_at': connector.last_used_at.isoformat() if connector.last_used_at else None,
        'tools': [{'name': t['name'], 'description': t['description']} for t in tools],
    }


@api_view(['GET'])
@permission_classes([IsSuperUser])
def list_mcp_connectors(request):
    """List MCP connectors for /panel/mcps."""
    connectors = McpConnector.objects.all().order_by('slug')
    return Response([_connector_payload(c) for c in connectors], status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def generate_mcp_connector_token(request, slug):
    """Create/rotate the connector token. The full URL is returned ONCE."""
    connector = get_object_or_404(McpConnector, slug=slug)
    token = connector.generate_token()
    logger.info('[MCP] token rotated for connector %s by %s', slug, request.user.username)
    # Build from the request host so staging/local instances hand out URLs
    # that actually point at themselves (the token only exists in their DB).
    connector_url = request.build_absolute_uri(f'/api/mcp/{connector.slug}/{token}/')
    return Response({
        'connector_url': connector_url,
        'token_prefix': connector.token_prefix,
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsSuperUser])
def update_mcp_connector(request, slug):
    """Toggle is_active."""
    connector = get_object_or_404(McpConnector, slug=slug)
    if 'is_active' in request.data:
        try:
            is_active = serializers.BooleanField().to_internal_value(request.data['is_active'])
        except serializers.ValidationError:
            return Response(
                {'is_active': 'Valor booleano inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        connector.is_active = is_active
        connector.save(update_fields=['is_active', 'updated_at'])
        logger.info(
            '[MCP] connector %s %s by %s',
            slug, 'activated' if connector.is_active else 'deactivated',
            request.user.username,
        )
    return Response(_connector_payload(connector), status=status.HTTP_200_OK)
