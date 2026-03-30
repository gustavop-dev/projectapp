import uuid

from django.db import models
from django.utils.text import slugify


class Document(models.Model):
    """Generic branded document that can be rendered as a PDF."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PUBLISHED = 'published', 'Publicado'
        ARCHIVED = 'archived', 'Archivado'

    class Language(models.TextChoices):
        ES = 'es', 'Espa\u00f1ol'
        EN = 'en', 'English'

    class CoverType(models.TextChoices):
        GENERIC = 'generic', 'Gen\u00e9rica'
        NONE = 'none', 'Sin portada'
        PROPOSAL = 'proposal', 'Propuesta'

    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT,
    )
    content_markdown = models.TextField(blank=True, default='')
    content_json = models.JSONField(default=dict, blank=True)
    client_name = models.CharField(max_length=255, blank=True, default='')
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.ES,
    )
    cover_type = models.CharField(
        max_length=20, choices=CoverType.choices, default=CoverType.GENERIC,
    )

    include_portada = models.BooleanField(default=True)
    include_subportada = models.BooleanField(default=True)
    include_contraportada = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or 'document'
        super().save(*args, **kwargs)
