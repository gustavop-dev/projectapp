"""Short-lived server-side handle for the preview PDF of a cuenta de cobro.

The preview modal used to hand the PDF to the viewer as a ``blob:`` URL built
from base64. A blob URL carries no name, so Chrome's PDF viewer falls back to
the URL's own UUID: its download button and its "Save to Drive" both proposed
``81a20288-b85a-41bd-aec4-693ebf6c02ae.pdf`` instead of the consecutivo. Serving
the same bytes from a real URL — with a filename in Content-Disposition and the
consecutivo as the last path segment — is what fixes every download path at once.

The preview persists nothing (its transaction is rolled back), so the bytes live
in the cache behind an opaque token. Unlike the impersonation exchange code this
mirrors, the token is NOT single-use: the viewer re-fetches on reload and print.
"""
import secrets

from django.core.cache import cache

CACHE_PREFIX = 'collection-account-preview-pdf:'
# Long enough to review the email side by side and come back to the document,
# short enough that a document never sent stops being fetchable the same hour.
TTL_SECONDS = 30 * 60


def store_preview_pdf(pdf_bytes, filename):
    """Cache *pdf_bytes* under a fresh opaque token and return the token."""
    token = secrets.token_urlsafe(32)
    cache.set(
        f'{CACHE_PREFIX}{token}',
        {'pdf': pdf_bytes, 'filename': filename},
        timeout=TTL_SECONDS,
    )
    return token


def load_preview_pdf(token):
    """Return ``{'pdf': bytes, 'filename': str}`` or ``None`` when expired."""
    if not token:
        return None
    return cache.get(f'{CACHE_PREFIX}{token}')
