"""A client's email history: what we sent them, and what it looked like.

The accounting Historial answers "why did that notice not arrive?" entering
through the email. This is the inverse question — "what have we sent this
client?" — which is the one you actually have while looking at their row.

Its own module rather than a corner of ``accounting.py``: every endpoint
there is superuser-only and scoped to the module's own template keys, and an
``IsAdminUser`` view living among them would invite widening the wrong guard.
The scope here is orthogonal — the client the row is filed under — and it
doubles as the authorization: a log belonging to somebody else 404s.

Note the deliberate consequence of ``IsAdminUser``: a staff user who is not a
superuser can read the body of an accounting notice here, which
``/api/accounting/email-log/<id>/body/`` denies them. That is the operator's
call, made knowingly, so the clients page keeps one access level throughout.
"""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import UserProfile
from content.api_errors import error_response
from content.models import EmailLog
from content.serializers.client_emails import ClientEmailLogSerializer
from content.services import accounting_email_retry_service
from content.views.history_pagination import (
    email_body_response,
    paginated_history_response,
)

logger = logging.getLogger(__name__)


def _client_or_404(client_id):
    return get_object_or_404(UserProfile.objects.clients(), pk=client_id)


def _log_or_404(client_id, log_id, queryset=None):
    """A log row of this client, or 404.

    Nesting the lookup under the client is the authorization: there is no
    second check to forget, and another client's row is simply not found.
    """
    return get_object_or_404(
        (
            queryset if queryset is not None else EmailLog.objects.all()
        ).filter(delivery_role=EmailLog.DeliveryRole.PRIMARY),
        id=log_id,
        client_id=client_id,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_client_emails(request, client_id):
    """One page of everything filed under this client, newest first.

    ``?audience=client|internal`` splits the two groups the modal shows: what
    reached the client's own address, and the internal notices about their
    records. Filtered server-side rather than in the browser because the list
    paginates — a count over one loaded page would lie.
    """
    _client_or_404(client_id)
    logs = (
        EmailLog.objects
        .filter(
            client_id=client_id,
            delivery_role=EmailLog.DeliveryRole.PRIMARY,
        )
        .select_related('body')
        .prefetch_related('targets')
        # The -id tiebreaker is not decoration: sent_at is auto_now_add, so a
        # multi-recipient send writes several rows in the same instant and
        # offset pagination would repeat or skip one between pages.
        .order_by('-sent_at', '-id')
    )
    audience = (request.query_params.get('audience') or '').strip()
    if audience in EmailLog.Audience.values:
        logs = logs.filter(audience=audience)

    return paginated_history_response(
        logs, request.query_params, ClientEmailLogSerializer,
    )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def client_email_body(request, client_id, log_id):
    """The message as delivered, for the preview modal."""
    log = _log_or_404(
        client_id, log_id, EmailLog.objects.select_related('body'),
    )
    return email_body_response(log)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def retry_client_email(request, client_id, log_id):
    """Re-send a failed notice to the address on the row, and only to it.

    Reuses the accounting retry service unchanged, which means the proposal
    and diagnostic rows listed here are not retryable: they come back with
    their own reason rather than the digest's. Adding handlers for them is
    deliberately out of scope — they are resent from the proposal itself.
    """
    log = _log_or_404(client_id, log_id)
    try:
        attempt = accounting_email_retry_service.retry_send(log)
    except accounting_email_retry_service.RetryError as exc:
        return error_response(str(exc))
    return Response(
        ClientEmailLogSerializer(attempt).data,
        status=status.HTTP_201_CREATED,
    )
