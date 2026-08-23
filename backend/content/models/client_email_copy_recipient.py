from django.core.exceptions import ValidationError
from django.db import models

from content.email_copy_families import CLIENT_EMAIL_FAMILY_VALUES


def default_client_email_families():
    """New recipients copy every client-email family by default."""
    return list(CLIENT_EMAIL_FAMILY_VALUES)


class ClientEmailCopyRecipient(models.Model):
    """Administrable BCC destination for outbound client email.

    This list is intentionally separate from ``NotificationRecipient``:
    operational/accounting alerts and copies of customer communication have
    different audiences and volume.
    """

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    families = models.JSONField(default=default_client_email_families)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['email']
        verbose_name = 'Client Email Copy Recipient'
        verbose_name_plural = 'Client Email Copy Recipients'

    def clean(self):
        super().clean()
        if not isinstance(self.families, list):
            raise ValidationError({'families': 'Debe ser una lista.'})
        unknown = set(self.families) - set(CLIENT_EMAIL_FAMILY_VALUES)
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
                family for family in CLIENT_EMAIL_FAMILY_VALUES
                if family in selected
            ]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
