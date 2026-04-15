import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Document(models.Model):
    """Generic branded document: markdown content and/or commercial collection account."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PUBLISHED = 'published', 'Publicado'
        ARCHIVED = 'archived', 'Archivado'

    class CommercialStatus(models.TextChoices):
        """Lifecycle for collection_account document type only (null for markdown types)."""

        DRAFT = 'draft', 'Draft'
        ISSUED = 'issued', 'Issued'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

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
    document_type = models.ForeignKey(
        'content.DocumentType',
        on_delete=models.PROTECT,
        related_name='documents',
        null=True,
        blank=True,
    )
    folder = models.ForeignKey(
        'content.DocumentFolder',
        on_delete=models.SET_NULL,
        related_name='documents',
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        'content.DocumentTag',
        related_name='documents',
        blank=True,
    )
    project = models.ForeignKey(
        'accounts.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
    )
    deliverable = models.ForeignKey(
        'accounts.Deliverable',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text='Optional scope: show this document under a specific deliverable.',
    )
    client_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_documents',
    )
    issuer = models.ForeignKey(
        'content.IssuerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
    )

    public_number = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        help_text='Human-visible consecutive number, e.g. PA-2026-004.',
    )
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=120, blank=True, default='')
    currency = models.CharField(max_length=3, default='COP')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default='')
    terms_and_conditions = models.TextField(blank=True, default='')
    template_version = models.CharField(max_length=32, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    commercial_status = models.CharField(
        max_length=20,
        choices=CommercialStatus.choices,
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_updated',
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
