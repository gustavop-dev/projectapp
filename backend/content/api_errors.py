"""Helpers for consistent, user-facing API error payloads.

The panel frontend renders errors as title + optional detail/action. To make
that possible every 4xx should return a predictable shape:

    {"error": "<mensaje en español>", "code": "<machine_code>", "hint": "<qué hacer>"}

`error` is always present and user-facing (Spanish). `code` is an optional stable
machine identifier the frontend can branch on. `hint` is an optional actionable
suggestion shown as the detail line.
"""

from rest_framework import status as http_status
from rest_framework.response import Response


class ProposalActionError(ValueError):
    """A user-facing validation error raised from the service layer.

    Subclasses ValueError so existing ``except ValueError`` handlers keep
    catching it, while carrying an optional machine ``code`` and actionable
    ``hint`` that views can forward via :func:`error_response`.
    """

    def __init__(self, message, *, code=None, hint=None):
        super().__init__(message)
        self.code = code
        self.hint = hint


def error_response_from_exc(exc, *, status=http_status.HTTP_400_BAD_REQUEST):
    """Build an error Response from a ValueError/ProposalActionError."""
    return error_response(
        str(exc),
        code=getattr(exc, 'code', None),
        hint=getattr(exc, 'hint', None),
        status=status,
    )


def error_response(message, *, code=None, hint=None, status=http_status.HTTP_400_BAD_REQUEST):
    """Build a DRF Response with the standard error payload.

    Args:
        message: User-facing error message in Spanish.
        code: Optional stable machine code (e.g. 'missing_client_email').
        hint: Optional actionable suggestion (shown as the detail line).
        status: HTTP status code (defaults to 400).
    """
    payload = {'error': message}
    if code:
        payload['code'] = code
    if hint:
        payload['hint'] = hint
    return Response(payload, status=status)
