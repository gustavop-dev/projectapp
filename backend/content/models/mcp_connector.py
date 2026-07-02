import hashlib
import hmac
import secrets

from django.db import models


class McpConnector(models.Model):
    """
    A remote MCP connector exposed by this backend (e.g. the Blog Publisher).

    The token embedded in the connector URL is the credential (capability
    URL, webhook-secret style). Only its SHA-256 hash is stored; the
    plaintext is shown once at generation time in /panel/mcps.
    """

    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    token_hash = models.CharField(
        max_length=64, blank=True, default='',
        help_text='SHA-256 hex digest of the connector token. Plaintext is never stored.',
    )
    token_prefix = models.CharField(
        max_length=8, blank=True, default='',
        help_text='First 8 chars of the token, for masked display in the panel.',
    )
    is_active = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'MCP Connector'
        verbose_name_plural = 'MCP Connectors'

    def __str__(self):
        return self.name

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def generate_token(self):
        """Create a new token, persist only its hash, return the plaintext once."""
        token = secrets.token_urlsafe(36)
        self.token_hash = self.hash_token(token)
        self.token_prefix = token[:8]
        self.save(update_fields=['token_hash', 'token_prefix', 'updated_at'])
        return token

    def check_token(self, token):
        if not self.token_hash or not token:
            return False
        return hmac.compare_digest(self.token_hash, self.hash_token(token))
