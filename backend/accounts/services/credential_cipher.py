"""
Symmetric cipher for project access credentials (Django admin passwords).

Stored ciphertext is a Fernet token (base64-encoded, URL-safe). The key must be a
valid Fernet key and live in the ``PROJECT_ACCESS_CIPHER_KEY`` env var.

If the key is missing, ``encrypt_password`` / ``decrypt_password`` raise
``ImproperlyConfigured``. Empty inputs are returned as empty strings so callers
can treat "no credential saved" uniformly.

Generate a key once with::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from decouple import config
from django.core.exceptions import ImproperlyConfigured


@lru_cache(maxsize=1)
def _get_cipher() -> Fernet:
    key = config('PROJECT_ACCESS_CIPHER_KEY', default='')
    if not key:
        raise ImproperlyConfigured(
            'PROJECT_ACCESS_CIPHER_KEY is not set. Generate one with '
            'Fernet.generate_key() and add it to the environment.',
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            f'PROJECT_ACCESS_CIPHER_KEY is not a valid Fernet key: {exc}',
        ) from exc


def encrypt_password(plain: str) -> str:
    """Encrypt a plaintext password. Empty input returns ''."""
    if not plain:
        return ''
    token = _get_cipher().encrypt(plain.encode('utf-8'))
    return token.decode('ascii')


def decrypt_password(token: str) -> str:
    """Decrypt a stored token. Empty or invalid input returns ''."""
    if not token:
        return ''
    try:
        return _get_cipher().decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError):
        return ''
