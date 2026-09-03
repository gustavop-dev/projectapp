"""Storage backends for content that must never be served from ``MEDIA_URL``."""

from django.core.files.storage import storages


def get_private_storage():
    """Resolve the private storage alias lazily for model ``FileField`` use."""

    return storages['private']
