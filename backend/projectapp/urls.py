from django.conf import settings
from django.http import JsonResponse
from django.urls import path, include, re_path
from content.admin import admin_site
from django.conf.urls.static import static

from .views import serve_nuxt
from content.views.blog import serve_sitemap_xml


def health_check(request):
    return JsonResponse({"status": "ok", "project": "projectapp"})


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

# Catch-all: serve pre-rendered Nuxt pages and public assets.
# This must be LAST so admin, api, and media URLs take priority.
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_nuxt, name='nuxt-page'),
]