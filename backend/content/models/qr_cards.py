import uuid

from django.db import models


class QRCard(models.Model):
    """
    A QR-code + short-link card. The UUID is the permanent identifier
    printed/embedded in the QR; the destination it redirects to can be
    changed at any time without invalidating the printed code.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    destination_url = models.URLField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QR Card'
        verbose_name_plural = 'QR Cards'

    def __str__(self):
        return f'{self.name} ({self.id})'
