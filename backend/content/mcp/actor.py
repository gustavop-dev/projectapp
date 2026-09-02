"""
Actor resolution for MCP tool handlers.

The MCP endpoint (`mcp_endpoint`) authenticates by capability-URL token and
runs with `@authentication_classes([])`, so there is no `request.user`. Most
tools (blog, documents) don't care — they never stamp authorship. But some
modules do: accounting writes set `created_by` and are audited to an actor,
and task comments set `author`. Those handlers resolve an actor here.

The endpoint normally injects a non-interactive, connector-specific service
principal in the execution context. The setting/first-superuser lookup below
is retained only for direct handler use outside the HTTP transport.
"""
from django.conf import settings
from django.contrib.auth import get_user_model

from content.mcp.protocol import ToolError
from content.mcp.context import current_mcp_context


def mcp_actor():
    """Return the actor that MCP writes are attributed to.

    HTTP requests resolve to the connector service principal. Direct handler
    calls retain the legacy configured-superuser fallback and raise ToolError
    when it cannot be resolved.
    """
    context = current_mcp_context()
    if context is not None and context.actor is not None:
        return context.actor

    User = get_user_model()
    username = getattr(settings, 'MCP_ACTOR_USERNAME', '') or ''

    if username:
        actor = User.objects.filter(
            username=username, is_superuser=True, is_active=True,
        ).first()
        if actor is None:
            raise ToolError(
                f'MCP_ACTOR_USERNAME="{username}" no corresponde a un superuser '
                'activo. Corrige el setting o crea ese usuario.'
            )
        return actor

    actor = User.objects.filter(is_superuser=True, is_active=True).order_by('pk').first()
    if actor is None:
        raise ToolError(
            'No hay ningún superuser activo para atribuir la acción. '
            'Crea uno o define settings.MCP_ACTOR_USERNAME.'
        )
    return actor
