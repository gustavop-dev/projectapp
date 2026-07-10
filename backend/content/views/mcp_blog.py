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
from content.mcp.accounting_tools import ACCOUNTING_TOOLS
from content.mcp.client_tools import CLIENT_TOOLS
from content.mcp.diagnostic_tools import DIAGNOSTIC_TOOLS
from content.mcp.document_tools import DOCUMENT_TOOLS
from content.mcp.linkedin_tools import LINKEDIN_TOOLS
from content.mcp.proposal_tools import PROPOSAL_TOOLS
from content.mcp.task_tools import TASK_TOOLS
from content.mcp.tools import BLOG_TOOLS
from content.models import McpConnector, McpRequestLog
from content.permissions import IsSuperUser

logger = logging.getLogger(__name__)

LAST_USED_TOUCH_SECONDS = 60

# One entry per exposed MCP connector: slug -> tool registry.
TOOLS_BY_SLUG = {
    'blog': BLOG_TOOLS,
    'documents': DOCUMENT_TOOLS,
    'clients': CLIENT_TOOLS,
    'tasks': TASK_TOOLS,
    'accounting': ACCOUNTING_TOOLS,
    'diagnostics': DIAGNOSTIC_TOOLS,
    'proposals': PROPOSAL_TOOLS,
    'linkedin-personal': LINKEDIN_TOOLS,
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
    if urlparse(origin).netloc != request.get_host():
        # Record the exact rejected value: MCP clients' headers are not
        # documented anywhere, so this log is how we learn what they send.
        logger.warning('[MCP] rejected foreign Origin: %s', origin)
        return True
    return False


def _touch_last_used(connector):
    now = tz.now()
    if connector.last_used_at and (now - connector.last_used_at).total_seconds() < LAST_USED_TOUCH_SECONDS:
        return
    McpConnector.objects.filter(pk=connector.pk).update(last_used_at=now)


def _record_event(connector, event, ok=True, detail=''):
    """Best-effort activity logging — must never break the MCP response."""
    if connector is None:
        return
    try:
        McpRequestLog.record(connector, event, ok=ok, detail=detail)
    except Exception:
        logger.exception('[MCP] failed to record %s event for %s', event, connector.slug)


def _record_tools_call(connector, message, payload):
    params = message.get('params') or {}
    tool_name = params.get('name', '?') if isinstance(params, dict) else '?'
    result = (payload or {}).get('result') or {}
    error = (payload or {}).get('error')
    if error:
        _record_event(connector, 'tool_call', ok=False, detail=f'{tool_name}: {error.get("message", "")}')
    elif result.get('isError'):
        text = (result.get('content') or [{}])[0].get('text', '')
        _record_event(connector, 'tool_call', ok=False, detail=f'{tool_name}: {text[:150]}')
    else:
        _record_event(connector, 'tool_call', detail=tool_name)


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
    connector_for_log = McpConnector.objects.filter(slug=slug).first()

    if _origin_is_foreign(request):
        _record_event(
            connector_for_log, 'origin_rejected', ok=False,
            detail=request.headers.get('Origin', ''),
        )
        return HttpResponse(status=403)

    tools = TOOLS_BY_SLUG.get(slug)
    connector = connector_for_log if (connector_for_log and connector_for_log.is_active) else None
    if tools is None or connector is None or not connector.check_token(token):
        if connector_for_log and not connector_for_log.is_active:
            detail = 'Conector inactivo — actívalo en el panel'
        else:
            detail = 'Token inválido (¿fue regenerado?)'
        _record_event(connector_for_log, 'auth_error', ok=False, detail=detail)
        raise Http404

    message = request.data
    http_status, payload = handle_message(
        message, tools, server_name=f'projectapp-{slug}-mcp',
    )

    if isinstance(message, dict):
        method = message.get('method')
        if method == 'initialize':
            _record_event(connector, 'handshake', detail='initialize OK')
        elif method == 'tools/call':
            _touch_last_used(connector)
            _record_tools_call(connector, message, payload)

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
    recent = [
        {
            'event': e.event,
            'ok': e.ok,
            'detail': e.detail,
            'created_at': e.created_at.isoformat(),
        }
        for e in connector.request_logs.all()[:10]
    ]
    if not recent:
        connection_status = 'none'
    elif recent[0]['ok']:
        connection_status = 'connected'
    else:
        connection_status = 'error'
    return {
        'slug': connector.slug,
        'name': connector.name,
        'description': connector.description,
        'is_active': connector.is_active,
        'has_token': bool(connector.token_hash),
        'token_prefix': connector.token_prefix,
        'last_used_at': connector.last_used_at.isoformat() if connector.last_used_at else None,
        'connection_status': connection_status,
        'recent_events': recent,
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
