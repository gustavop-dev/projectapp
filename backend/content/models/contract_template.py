from django.db import models


class ContractTemplate(models.Model):
    """
    Stores a contract template as markdown with optional {placeholders}.

    The default template (is_default=True) is used when generating contracts
    from the ContractParamsModal. Placeholders like {client_full_name} are
    substituted with values from proposal.contract_params at PDF generation time.

    Admin can edit the default template via Django admin.
    """

    name = models.CharField(max_length=255)
    content_markdown = models.TextField(
        help_text='Markdown text. Use {client_full_name}, {contractor_cedula}, etc. for placeholders.',
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']
        verbose_name = 'Contract template'
        verbose_name_plural = 'Contract templates'

    def __str__(self):
        default_label = ' (default)' if self.is_default else ''
        return f'{self.name}{default_label}'

    def save(self, *args, **kwargs):
        if self.is_default:
            ContractTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        """Return the default template, or None if not configured."""
        return cls.objects.filter(is_default=True).first()
