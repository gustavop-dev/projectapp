"""Public PWA files with explicit MIME and revalidation, before the SPA fallback."""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe


PWA_FILES = {
    'manifest.webmanifest': 'application/manifest+json',
    'sw.js': 'application/javascript',
}


@require_safe
def serve_pwa_file(request, filename):
    """Serve only the fixed public files; missing builds must never return SPA HTML."""
    content_type = PWA_FILES.get(filename)
    if content_type is None:
        raise Http404()
    asset = Path(settings.BASE_DIR) / 'static' / 'frontend' / filename
    try:
        response = FileResponse(asset.open('rb'), content_type=content_type)
    except FileNotFoundError:
        raise Http404('PWA asset not found') from None
    response['Cache-Control'] = 'no-cache'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
