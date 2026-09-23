"""Per-card image library referenced by HTML templates through a stable key."""
import uuid

from django.core.validators import RegexValidator
from django.db import models

ASSET_KEY_VALIDATOR = RegexValidator(
    r'^[a-z][a-z0-9_-]{0,39}$',
    'Usa una clave en minúsculas con números, guion o guion bajo (hasta 40 caracteres).',
)


class LinktreeAsset(models.Model):
    """
    A decorative image uploaded once for a Linktree and reusable by any of its
    HTML templates as ``<img data-asset="key">`` or CSS ``asset(key)``.
    Published versions keep their own snapshot of the normalized files, so
    replacing or deleting a library image never alters what is already live.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    linktree = models.ForeignKey('content.Linktree', on_delete=models.CASCADE, related_name='assets')
    key = models.CharField(max_length=40, validators=[ASSET_KEY_VALIDATOR])
    alt = models.CharField(max_length=500, blank=True, default='')
    # Same shape as template package assets: format, mime, width, height,
    # size and private-storage paths per density.
    image = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        constraints = [
            models.UniqueConstraint(fields=['linktree', 'key'], name='unique_linktree_asset_key'),
        ]
        verbose_name = 'Linktree Asset'
        verbose_name_plural = 'Linktree Assets'

    def __str__(self):
        return f'{self.key} → {self.linktree_id}'

    @property
    def url(self):
        """Admin preview URL; templates may reference it verbatim and it is normalized to the key."""
        return f'/api/linktrees/admin/{self.linktree_id}/assets/{self.key}/'
