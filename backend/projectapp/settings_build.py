"""Settings for the build-time blog prerender server.

Used only by the throwaway local Django server that
``frontend/update-django-template.js`` starts on loopback to prerender blog
posts (see that file for why). It extends production — same MySQL database and
real content — but disables HTTPS enforcement so the dev server can be reached
over plain HTTP on 127.0.0.1 (production forces SECURE_SSL_REDIRECT, which would
301 the prerender fetches to https and break them).

Never used to serve real traffic.
"""

from .settings_prod import *  # noqa: F401,F403

# Loopback HTTP build server — no TLS in front of it.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
