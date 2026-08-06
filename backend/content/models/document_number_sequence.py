from django.db import models


class DocumentNumberSequence(models.Model):
    """Per-issuer, per-year counter for public_number allocation."""

    issuer = models.ForeignKey(
        'content.IssuerProfile',
        on_delete=models.CASCADE,
        related_name='number_sequences',
    )
    year = models.PositiveIntegerField()
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['issuer', 'year'],
                name='uniq_document_number_sequence_issuer_year',
            ),
        ]

    def __str__(self):
        return f'{self.issuer_id}/{self.year}: {self.last_value}'


class ClientDocumentNumberSequence(models.Model):
    """
    Per-client continuous counter for PA-{CODE}-{NNN} numbering. Never
    resets by year. Hosting-driven cuentas (no platform client) keep using
    the per-issuer DocumentNumberSequence above.
    """

    client_profile = models.OneToOneField(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='collection_number_sequence',
    )
    last_value = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'client {self.client_profile_id}: {self.last_value}'
