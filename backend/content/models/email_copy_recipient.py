from django.core.exceptions import ValidationError
from django.db import models

from content.email_copy_families import EMAIL_COPY_FAMILY_VALUES


def default_email_copy_families():
    """New recipients copy every outbound-email family by default."""
    return list(EMAIL_COPY_FAMILY_VALUES)


class EmailCopyRecipient(models.Model):
    """Administrable BCC destination for every outbound platform email."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    families = models.JSONField(default=default_email_copy_families)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['email']
        verbose_name = 'Email Copy Recipient'
        verbose_name_plural = 'Email Copy Recipients'

    def clean(self):
        super().clean()
        if not isinstance(self.families, list):
            raise ValidationError({'families': 'Debe ser una lista.'})
        unknown = set(self.families) - set(EMAIL_COPY_FAMILY_VALUES)
        if unknown:
            raise ValidationError({
                'families': f'Familias no válidas: {", ".join(sorted(unknown))}.',
            })
        if self.is_active and not self.families:
            raise ValidationError({
                'families': 'Un destinatario activo debe cubrir al menos una familia.',
            })

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower()
        if isinstance(self.families, list):
            selected = set(self.families)
            self.families = [
                family for family in EMAIL_COPY_FAMILY_VALUES
                if family in selected
            ]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
