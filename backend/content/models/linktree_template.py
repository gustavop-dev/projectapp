"""Immutable template packages and validated publication snapshots."""
import uuid

from django.conf import settings
from django.db import models


class LinktreeTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('content.Linktree', null=True, on_delete=models.SET_NULL,
                              related_name='owned_templates')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='+')
    name = models.CharField(max_length=160)
    manifest = models.JSONField(default=dict)
    html = models.TextField()
    css = models.TextField(blank=True)
    assets = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class LinktreeTemplateVersion(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Validando'
        VALID = 'valid', 'Lista para publicar'
        INVALID = 'invalid', 'Requiere correcciones'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    linktree = models.ForeignKey('content.Linktree', on_delete=models.CASCADE,
                                 related_name='template_versions')
    template = models.ForeignKey(LinktreeTemplate, on_delete=models.PROTECT, related_name='versions')
    assets = models.JSONField(default=dict)
    overrides = models.JSONField(default=list)
    profile = models.JSONField(default=dict)
    profile_digest = models.CharField(max_length=64)
    document = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    report = models.JSONField(default=dict)
    screenshots = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class LinktreeTemplateClick(models.Model):
    """Daily aggregate, deliberately without visitor identifiers or IP addresses."""
    version = models.ForeignKey(LinktreeTemplateVersion, on_delete=models.CASCADE, related_name='clicks')
    link_key = models.CharField(max_length=40)
    day = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'link_key', 'day'], name='unique_linktree_template_click_day')]
