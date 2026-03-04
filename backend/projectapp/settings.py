"""
Django base settings for projectapp.

This file contains shared configuration for all environments.
Do NOT use this file directly — import it via settings_dev.py or settings_prod.py.

Environment-specific overrides:
  - settings_dev.py  : SQLite, DEBUG=True, console email
  - settings_prod.py : MySQL, DEBUG=False, SMTP email
"""

import os
from pathlib import Path

from decouple import Csv, config
from huey import RedisHuey

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


DJANGO_ENV = config('DJANGO_ENV', default='development')
IS_PRODUCTION = DJANGO_ENV == 'production'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY', default='change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'content',
    'corsheaders',
    # Third-party (operations)
    'dbbackup',
    'huey.contrib.djhuey',
]

ENABLE_SILK = config('ENABLE_SILK', default=False, cast=bool)
if ENABLE_SILK:
    INSTALLED_APPS.append('silk')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if ENABLE_SILK:
    MIDDLEWARE.insert(1, 'silk.middleware.SilkyMiddleware')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    default='http://127.0.0.1:5173,http://localhost:5173',
    cast=Csv(),
)

CSRF_TRUSTED_ORIGINS = config(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default='http://127.0.0.1:5173,http://localhost:5173',
    cast=Csv(),
)

ROOT_URLCONF = 'projectapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'content' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'projectapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DJANGO_DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DJANGO_DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
    'dbbackup': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': config('BACKUP_STORAGE_PATH', default='/var/backups/projectapp'),
        },
    },
}

# ==============================================================================
# EMAIL — override in settings_dev.py / settings_prod.py
# ==============================================================================

EMAIL_BACKEND = config('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtpout.secureserver.net')
EMAIL_PORT = config('EMAIL_PORT', default=465, cast=int)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='team@projectapp.co')
NOTIFICATION_EMAIL = config('NOTIFICATION_EMAIL', default='dev.gustavo.perezp@gmail.com')

# ==============================================================================
# WHATSAPP — CallMeBot API
# ==============================================================================

WHATSAPP_PHONE = config('WHATSAPP_PHONE', default='')
CALLMEBOT_API_KEY = config('CALLMEBOT_API_KEY', default='')

# ==============================================================================
# HUEY — task queue
# ==============================================================================

HUEY = RedisHuey(
    name='projectapp',
    url=config('REDIS_URL', default='redis://localhost:6379/5'),
    immediate=not IS_PRODUCTION,
)

# ==============================================================================
# BACKUPS — django-dbbackup
# ==============================================================================
# Storage is configured via STORAGES['dbbackup'] above (new-style API).

DBBACKUP_FILENAME_TEMPLATE = '{datetime}.sql'
DBBACKUP_MEDIA_FILENAME_TEMPLATE = '{datetime}.tar'
DBBACKUP_CLEANUP_KEEP = 4
DBBACKUP_CLEANUP_KEEP_MEDIA = 4

# ==============================================================================
# SILK — query profiling (enabled via ENABLE_SILK env flag)
# ==============================================================================

if ENABLE_SILK:
    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_META = True
    SILKY_ANALYZE_QUERIES = True

    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True

    def silk_permissions(user):
        return user.is_staff

    SILKY_PERMISSIONS = silk_permissions

    SILKY_MAX_RECORDED_REQUESTS = 10000
    SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10

    SILKY_IGNORE_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/silk/',
    ]

    SILKY_MAX_REQUEST_BODY_SIZE = 1024
    SILKY_MAX_RESPONSE_BODY_SIZE = 1024

SLOW_QUERY_THRESHOLD_MS = config('SLOW_QUERY_THRESHOLD_MS', default=500, cast=int)
N_PLUS_ONE_THRESHOLD = config('N_PLUS_ONE_THRESHOLD', default=10, cast=int)

# ==============================================================================
# LOGGING
# ==============================================================================

LOG_LEVEL = config('DJANGO_LOG_LEVEL', default='INFO')

_LOGS_DIR = BASE_DIR / 'logs'
_LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'backup_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'backups.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'backups': {
            'handlers': ['backup_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}