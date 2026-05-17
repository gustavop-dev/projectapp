"""
Development settings for projectapp.

Overrides: DEBUG=True, SQLite database, console email backend.
Usage: DJANGO_SETTINGS_MODULE=projectapp.settings_dev

Optional override file: `backend/.env_development`
    If present, layered on top of the standard `.env` for these keys:
      - DJANGO_ALLOWED_HOSTS
      - DJANGO_CSRF_TRUSTED_ORIGINS
      - DJANGO_CORS_ALLOWED_ORIGINS
      - FRONTEND_BASE_URL
    Used for host-only network access (e.g. VirtualBox 192.168.56.x).
    Never read by settings_prod.py — production is unaffected.
"""

from decouple import Config, Csv, RepositoryEnv

from .settings import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': config('DJANGO_DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

_LOCALHOST_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:3002',
    'http://localhost:3003',
    'http://localhost:3004',
    'http://localhost:3005',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
    'http://127.0.0.1:3002',
    'http://127.0.0.1:3003',
    'http://127.0.0.1:3004',
    'http://127.0.0.1:3005',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

CSRF_TRUSTED_ORIGINS = list(_LOCALHOST_ORIGINS)
CORS_ALLOWED_ORIGINS = list(_LOCALHOST_ORIGINS)

_DEV_ENV_PATH = BASE_DIR / '.env_development'
if _DEV_ENV_PATH.exists():
    _dev = Config(RepositoryEnv(str(_DEV_ENV_PATH)))
    ALLOWED_HOSTS = _dev('DJANGO_ALLOWED_HOSTS', default=','.join(ALLOWED_HOSTS), cast=Csv())
    _dev_csrf = _dev('DJANGO_CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
    _dev_cors = _dev('DJANGO_CORS_ALLOWED_ORIGINS', default='', cast=Csv())
    if _dev_csrf:
        CSRF_TRUSTED_ORIGINS = sorted(set(_LOCALHOST_ORIGINS) | set(_dev_csrf))
    if _dev_cors:
        CORS_ALLOWED_ORIGINS = sorted(set(_LOCALHOST_ORIGINS) | set(_dev_cors))
    FRONTEND_BASE_URL = _dev('FRONTEND_BASE_URL', default=FRONTEND_BASE_URL)
