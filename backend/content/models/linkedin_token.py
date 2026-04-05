"""
Singleton model for encrypted LinkedIn OAuth token storage.

Uses Fernet symmetric encryption from the `cryptography` library.
The encryption key is loaded from settings.LINKEDIN_ENCRYPTION_KEY.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_fernet():
    """Return a Fernet instance from the configured encryption key, or None."""
    key = getattr(settings, 'LINKEDIN_ENCRYPTION_KEY', '')
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError):
        logger.error('Invalid LINKEDIN_ENCRYPTION_KEY — cannot encrypt/decrypt tokens.')
        return None


class LinkedInToken(models.Model):
    """
    Singleton model storing the LinkedIn OAuth access & refresh tokens.

    Follows the CompanySettings singleton pattern: pk is always 1,
    use ``LinkedInToken.load()`` to retrieve the instance.
    """

    access_token_encrypted = models.TextField(
        blank=True, default='',
        help_text='Fernet-encrypted LinkedIn access token.',
    )
    refresh_token_encrypted = models.TextField(
        blank=True, default='',
        help_text='Fernet-encrypted LinkedIn refresh token.',
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the access token expires.',
    )
    refresh_token_expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When the refresh token expires (typically 60 days).',
    )

    # Cached profile info (avoids extra API calls)
    member_sub = models.CharField(
        max_length=100, blank=True, default='',
        help_text='LinkedIn member "sub" claim (used to build urn:li:person:XXX).',
    )
    profile_name = models.CharField(max_length=255, blank=True, default='')
    profile_picture = models.URLField(max_length=500, blank=True, default='')
    profile_email = models.EmailField(blank=True, default='')

    obtained_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'LinkedIn Token'
        verbose_name_plural = 'LinkedIn Tokens'

    def __str__(self):
        return f'LinkedInToken (connected={bool(self.access_token_encrypted)})'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------

    def set_access_token(self, plaintext: str) -> None:
        f = _get_fernet()
        if f is None:
            raise ValueError('LINKEDIN_ENCRYPTION_KEY is not configured.')
        self.access_token_encrypted = f.encrypt(plaintext.encode()).decode()

    def get_access_token(self) -> str | None:
        if not self.access_token_encrypted:
            return None
        f = _get_fernet()
        if f is None:
            return None
        try:
            return f.decrypt(self.access_token_encrypted.encode()).decode()
        except InvalidToken:
            logger.error('Failed to decrypt access token — key may have changed.')
            return None

    def set_refresh_token(self, plaintext: str) -> None:
        f = _get_fernet()
        if f is None:
            raise ValueError('LINKEDIN_ENCRYPTION_KEY is not configured.')
        self.refresh_token_encrypted = f.encrypt(plaintext.encode()).decode()

    def get_refresh_token(self) -> str | None:
        if not self.refresh_token_encrypted:
            return None
        f = _get_fernet()
        if f is None:
            return None
        try:
            return f.decrypt(self.refresh_token_encrypted.encode()).decode()
        except InvalidToken:
            logger.error('Failed to decrypt refresh token — key may have changed.')
            return None

    # ------------------------------------------------------------------
    # Expiry checks
    # ------------------------------------------------------------------

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return timezone.now() >= self.expires_at

    @property
    def is_refresh_expired(self) -> bool:
        if not self.refresh_token_expires_at:
            return True
        return timezone.now() >= self.refresh_token_expires_at

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all stored token data."""
        self.access_token_encrypted = ''
        self.refresh_token_encrypted = ''
        self.expires_at = None
        self.refresh_token_expires_at = None
        self.member_sub = ''
        self.profile_name = ''
        self.profile_picture = ''
        self.profile_email = ''
        self.obtained_at = None
