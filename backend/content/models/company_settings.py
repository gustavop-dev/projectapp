from django.db import models


class CompanySettings(models.Model):
    """
    Singleton model storing seller company defaults for contract generation.

    Usage:
        settings = CompanySettings.load()
        settings.contractor_full_name  # → 'CARLOS MARIO BLANCO PÉREZ'
    """

    contractor_full_name = models.CharField(
        max_length=255,
        default='',
        blank=True,
        help_text='Legal name of the contractor (EL CONTRATISTA).',
    )
    contractor_cedula = models.CharField(
        max_length=30,
        default='',
        blank=True,
        help_text='Cédula number of the contractor.',
    )
    contractor_email = models.EmailField(
        default='',
        blank=True,
        help_text='Notification email for the contractor (Cláusula 14).',
    )
    bank_name = models.CharField(
        max_length=100,
        default='',
        blank=True,
        help_text='Bank name for payment (e.g. Bancolombia).',
    )
    bank_account_type = models.CharField(
        max_length=50,
        default='Ahorros',
        blank=True,
        help_text='Account type: Ahorros or Corriente.',
    )
    bank_account_number = models.CharField(
        max_length=50,
        default='',
        blank=True,
        help_text='Bank account number for payment.',
    )
    contract_city = models.CharField(
        max_length=100,
        default='Medellín',
        blank=True,
        help_text='City for dispute resolution (Cláusula 17).',
    )
    contractor_signature = models.ImageField(
        upload_to='signatures/',
        null=True,
        blank=True,
        help_text='Signature image for the contractor (displayed on contract PDFs). PNG with transparent background recommended.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company settings'
        verbose_name_plural = 'Company settings'

    def __str__(self):
        return f'CompanySettings — {self.contractor_full_name or "(not configured)"}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def to_dict(self):
        """Return settings as a plain dict for contract param defaults."""
        return {
            'contractor_full_name': self.contractor_full_name,
            'contractor_cedula': self.contractor_cedula,
            'contractor_email': self.contractor_email,
            'bank_name': self.bank_name,
            'bank_account_type': self.bank_account_type,
            'bank_account_number': self.bank_account_number,
            'contract_city': self.contract_city,
        }
