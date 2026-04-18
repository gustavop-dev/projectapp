from django.core.exceptions import ValidationError
from django.db import models


class DiagnosticDefaultConfig(models.Model):
    """Admin-editable defaults for new ``WebAppDiagnostic`` rows.

    Singleton per language. When an admin creates a new diagnostic,
    ``content.services.diagnostic_service.create_diagnostic`` first checks
    this table for the requested language and inherits payment terms,
    currency, investment, duration and the section seed from it. When no
    row exists, the hardcoded seed in ``content.seeds.diagnostic_template``
    is used.
    """

    class Language(models.TextChoices):
        ES = 'es', 'Español'
        EN = 'en', 'English'

    class Currency(models.TextChoices):
        COP = 'COP', 'COP'
        USD = 'USD', 'USD'

    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        unique=True,
        help_text='Language for this default configuration.',
    )
    sections_json = models.JSONField(
        default=list,
        help_text='Full array of default section dicts (same shape as the seed).',
    )

    payment_initial_pct = models.PositiveSmallIntegerField(default=60)
    payment_final_pct = models.PositiveSmallIntegerField(default=40)
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.COP,
    )
    default_investment_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    default_duration_label = models.CharField(
        max_length=80, blank=True, default='',
    )
    expiration_days = models.PositiveIntegerField(default=21)
    reminder_days = models.PositiveIntegerField(default=7)
    urgency_reminder_days = models.PositiveIntegerField(default=14)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diagnostic Default Config'
        verbose_name_plural = 'Diagnostic Default Configs'

    def __str__(self):
        return f'DiagnosticDefaultConfig ({self.get_language_display()})'

    def clean(self):
        super().clean()
        total = (self.payment_initial_pct or 0) + (self.payment_final_pct or 0)
        if total != 100:
            raise ValidationError({
                'payment_initial_pct': (
                    'payment_initial_pct + payment_final_pct must equal 100 '
                    f'(got {total}).'
                ),
            })
