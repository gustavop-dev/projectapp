"""
Actor resolution for MCP tool handlers.

The MCP endpoint (`mcp_endpoint`) authenticates by capability-URL token and
runs with `@authentication_classes([])`, so there is no `request.user`. Most
tools (blog, documents) don't care — they never stamp authorship. But some
modules do: accounting writes set `created_by` and are audited to an actor,
and task comments set `author`. Those handlers resolve an actor here.

Policy (decided with the operator): use an existing superuser as the actor.
Configurable via `settings.MCP_ACTOR_USERNAME`; falls back to the first active
superuser. The audit trail then shows that superuser as if the change came
from the panel.
"""
from django.conf import settings
from django.contrib.auth import get_user_model

from content.mcp.protocol import ToolError


def mcp_actor():
    """Return the superuser that MCP writes are attributed to.

    Raises ToolError (surfaced to the model, not a 500) when no suitable
    superuser exists, so the operator gets an actionable message instead of a
    crash.
    """
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
