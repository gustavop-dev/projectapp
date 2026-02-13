from django.conf import settings
from django.urls import path, include, re_path
from content.admin import admin_site
from django.conf.urls.static import static

from .views import serve_nuxt

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/', include('content.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all: serve pre-rendered Nuxt pages and public assets.
# This must be LAST so admin, api, and media URLs take priority.
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_nuxt, name='nuxt-page'),
]