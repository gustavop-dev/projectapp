"""
ASGI config for projectapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from projectapp.environment import default_settings_module

os.environ.setdefault('DJANGO_SETTINGS_MODULE', default_settings_module())

application = get_asgi_application()
