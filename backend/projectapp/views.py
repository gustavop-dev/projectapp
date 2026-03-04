import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponseRedirect

FRONTEND_DIR = os.path.join(settings.BASE_DIR, 'static', 'frontend')
DEFAULT_LOCALE = 'en-us'


def serve_nuxt(request, path=''):
    """
    Serve pre-rendered Nuxt pages and public assets from backend/static/frontend/.
    
    Handles:
    - HTML pages: /en-us/about-us → static/frontend/en-us/about-us/index.html
    - Payload JSON: /en-us/about-us/_payload.json → static/frontend/en-us/about-us/_payload.json
    - Public assets: /img/icons/icon.png → static/frontend/img/icons/icon.png
    - SPA fallback: routes not pre-rendered get 200.html (Nuxt handles client-side)
    """
    clean_path = path.strip('/')

    # Redirect bare root to default locale
    if not clean_path:
        return HttpResponseRedirect(f'/{DEFAULT_LOCALE}/')

    # Security: prevent path traversal
    resolved = os.path.realpath(os.path.join(FRONTEND_DIR, clean_path))
    if not resolved.startswith(os.path.realpath(FRONTEND_DIR)):
        raise Http404()

    # 1. Exact file match (e.g. _payload.json, .png, .mp4, .splinecode)
    if os.path.isfile(resolved):
        content_type, _ = mimetypes.guess_type(resolved)
        return FileResponse(open(resolved, 'rb'), content_type=content_type)

    # 2. Directory with index.html (e.g. /en-us/about-us/ → index.html)
    index_file = os.path.join(resolved, 'index.html')
    if os.path.isfile(index_file):
        return FileResponse(open(index_file, 'rb'), content_type='text/html')

    # 3. SPA fallback for client-side routes not pre-rendered
    fallback = os.path.join(FRONTEND_DIR, '200.html')
    if os.path.isfile(fallback):
        return FileResponse(open(fallback, 'rb'), content_type='text/html')

    # 4. Root index.html as last resort
    root_index = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.isfile(root_index):
        return FileResponse(open(root_index, 'rb'), content_type='text/html')

    raise Http404('Page not found')
