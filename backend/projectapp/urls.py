import os

from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.urls import path, include, re_path
from content.admin import admin_site
from django.conf.urls.static import static

from .views import serve_nuxt
from content.views.blog import serve_sitemap_xml


def health_check(request):
    # 'project'/'environment' let external probes verify WHO answered: a shared
    # codebase means the project name alone cannot tell prod from staging
    # (measured: /qa pilot #3). DJANGO_ENV is read through settings because
    # python-decouple resolves it from backend/.env, which os.getenv cannot see.
    return JsonResponse({
        "status": "ok",
        "project": "projectapp",
        "environment": getattr(settings, "DJANGO_ENV", os.getenv("DJANGO_ENV", "development")),
    })


def oauth_discovery_not_found(request, *args, **kwargs):
    """
    MCP clients (claude.ai custom connectors) probe these OAuth discovery
    endpoints; the SPA catch-all used to answer 200 HTML, which reads as
    "OAuth-protected server" and derails the connector setup. A real 404
    signals a no-auth (capability URL) server.
    """
    return HttpResponseNotFound()


urlpatterns = [
    path('api/health/', health_check, name='health-check'),
    path('admin/', admin_site.urls),
    path('api/', include('content.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('sitemap.xml', serve_sitemap_xml, name='sitemap-xml'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'ENABLE_SILK', False):
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

# OAuth/OpenID discovery probes must 404 (no-auth MCP server), not fall
# through to the SPA catch-all which answers 200 HTML.
urlpatterns += [
    re_path(
        r'^\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)(/.*)?$',
        oauth_discovery_not_found,
        name='oauth-discovery-not-found',
    ),
]

# Catch-all: serve pre-rendered Nuxt pages and public assets.
# This must be LAST so admin, api, and media URLs take priority.
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_nuxt, name='nuxt-page'),
]