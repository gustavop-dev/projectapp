"""Helpers for parsing the ``doc_refs`` field on composed-email endpoints.

``doc_refs`` is a JSON list of ``{'source': str, ...}`` objects that reference
documents already known to the system (generated PDFs, uploaded files, static
markdown templates). Views resolve these refs into email-attachment tuples
using a type-specific resolver (proposal vs. diagnostic).
"""

import json

from rest_framework import status
from rest_framework.response import Response


class DocRefError(ValueError):
    """Raised when a doc_refs entry cannot be resolved to an attachment."""


def parse_doc_refs_field(request):
    """
    Parse and validate the ``doc_refs`` FormData/JSON field on ``request``.

    Returns ``(doc_refs_list, None)`` on success or ``(None, Response)`` on
    malformed input, mirroring the other ``_parse_*`` helper convention.
    """
    raw = request.data.get('doc_refs', '[]')
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return None, Response(
            {'error': 'doc_refs debe ser JSON válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if parsed and not isinstance(parsed, list):
        return None, Response(
            {'error': 'doc_refs debe ser una lista.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return parsed or [], None
