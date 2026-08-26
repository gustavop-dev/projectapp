from django.conf import settings
from django.db import models


class DocumentNote(models.Model):
    """Private, actionable note that may explain a state episode."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Pendiente'
        RESOLVED = 'resolved', 'Resuelta'
        DISCARDED = 'discarded', 'Descartada'

    document = models.ForeignKey(
        'content.Document',
        on_delete=models.CASCADE,
        related_name='document_notes',
    )
    episode = models.ForeignKey(
        'content.DocumentStateEpisode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes',
    )
    title = models.CharField(max_length=120, blank=True, default='')
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_note = models.CharField(max_length=500, blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_at_known = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('order', 'created_at', 'id')
        indexes = [
            models.Index(fields=('document', 'status')),
            models.Index(fields=('episode', 'status')),
        ]

    def __str__(self):
        return self.title or self.content[:60]
