from django.db import models


class ProposalDefaultConfig(models.Model):
    """
    Stores admin-editable default section configurations for new proposals.

    One row per language (singleton pattern). When a new proposal is created,
    ProposalService.get_default_sections() checks this table first; if no
    row exists for the requested language, the hardcoded defaults are used.
    """

    class Language(models.TextChoices):
        ES = 'es', 'Español'
        EN = 'en', 'English'

    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        unique=True,
        help_text='Language for this default configuration.',
    )
    sections_json = models.JSONField(
        default=list,
        help_text='Full array of default section dicts (same structure as DEFAULT_SECTIONS).',
    )
    expiration_days = models.PositiveIntegerField(
        default=21,
        help_text='Default proposal expiration period in days.',
    )
    default_slug_pattern = models.CharField(
        max_length=200,
        default='{client_name}',
        blank=True,
        help_text=(
            'Template used to auto-generate the public slug when a seller does not '
            'provide one at creation time. Placeholders: {client_name}, {project_type}, '
            '{year}. The rendered value is slugified and deduplicated with numeric suffixes.'
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proposal Default Config'
        verbose_name_plural = 'Proposal Default Configs'

    def __str__(self):
        return f'ProposalDefaultConfig ({self.get_language_display()})'
