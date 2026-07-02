"""
Blog Publisher MCP: public JSON-RPC endpoint (token-authenticated) and
the panel management endpoints backing /panel/mcps.
"""
import logging

from django.http import Http404
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from content.mcp.protocol import handle_message
from content.mcp.tools import BLOG_TOOLS
from content.models import McpConnector

logger = logging.getLogger(__name__)

LAST_USED_TOUCH_SECONDS = 60


class McpEndpointThrottle(AnonRateThrottle):
    scope = 'mcp'


def _touch_last_used(connector):
    now = tz.now()
    if connector.last_used_at and (now - connector.last_used_at).total_seconds() < LAST_USED_TOUCH_SECONDS:
        return
    McpConnector.objects.filter(pk=connector.pk).update(last_used_at=now)


@api_view(['POST'])
@authentication_classes([])  # token in URL is the credential; no session ⇒ no CSRF
@permission_classes([AllowAny])
@throttle_classes([McpEndpointThrottle])
def mcp_blog_endpoint(request, token):
    """
    MCP Streamable HTTP endpoint for the Blog Publisher connector.
    Plain-JSON responses only (no SSE) — WSGI-compatible by design.
    """
    connector = McpConnector.objects.filter(slug='blog', is_active=True).first()
    if connector is None or not connector.check_token(token):
        raise Http404

    message = request.data
    http_status, payload = handle_message(message, BLOG_TOOLS)

    if isinstance(message, dict) and message.get('method') == 'tools/call':
        _touch_last_used(connector)

    if payload is None:
        return Response(status=http_status)
    return Response(payload, status=http_status)
