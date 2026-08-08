from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .accounting_base import AccountingRecordBase


class RecurringPayment(AccountingRecordBase):
    """Recurring operational cost (subscriptions, ads retainers, savings)."""

    class Currency(models.TextChoices):
        COP = 'COP', 'COP'
        USD = 'USD', 'USD'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Efectivo'
        CREDIT_CARD = 'credit_card', 'T.C'

    class Frequency(models.TextChoices):
        # Declared from the shortest cycle to the longest: the form select and
        # the filter panel render them in this order, so picking the right one
        # is a matter of walking down the list.
        MONTHLY = 'monthly', 'Mensual'
        BIMONTHLY = 'bimonthly', 'Bimestral'
        QUARTERLY = 'quarterly', 'Trimestral'
        # `four_monthly` and not `triannual`: the latter reads almost exactly
        # like the `triennial` below (every 3 years) and means the opposite.
        FOUR_MONTHLY = 'four_monthly', 'Cuatrimestral'
        SEMIANNUAL = 'semiannual', 'Semestral'
        ANNUAL = 'annual', 'Anual'
        BIENNIAL = 'biennial', 'Cada 2 años'
        TRIENNIAL = 'triennial', 'Cada 3 años'
        # Escape hatch for cycles the catalog does not cover; its length lives
        # in `custom_months`, so it is deliberately absent from FREQUENCY_MONTHS.
        CUSTOM = 'custom', 'Personalizada'

    FREQUENCY_MONTHS = {
        Frequency.MONTHLY: 1,
        Frequency.BIMONTHLY: 2,
        Frequency.QUARTERLY: 3,
        Frequency.FOUR_MONTHLY: 4,
        Frequency.SEMIANNUAL: 6,
        Frequency.ANNUAL: 12,
        Frequency.BIENNIAL: 24,
        Frequency.TRIENNIAL: 36,
    }

    class CostType(models.TextChoices):
        FIXED = 'fixed', 'Fijo'
        VARIABLE = 'variable', 'Variable'

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.COP,
    )
    # Approximate COP value used for aggregation (equals price when COP).
    cop_equivalent = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
    )
    payment_method = models.CharField(
        max_length=12,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CREDIT_CARD,
    )
    frequency = models.CharField(
        max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY,
    )
    # Cycle length for CUSTOM, in months. Months and not days on purpose: real
    # billing cycles land on the same day of the month, not every N days, and
    # dividing by whole months keeps the monthly equivalent exact.
    custom_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(600)],
        help_text='Sólo para la frecuencia personalizada: cada cuántos meses se cobra.',
    )
    billing_day = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    cost_type = models.CharField(
        max_length=10, choices=CostType.choices, default=CostType.FIXED,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    category = models.ForeignKey(
        'content.RecurringCategory',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True,
    )
    order = models.PositiveIntegerField(
        default=0, help_text='Manual sort order within its category (lower first).',
    )

    class Meta:
        # The DB is the single owner of the order the operator dragged into
        # place: category first, then the manual slot inside it.
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return f'{self.name} ({self.frequency_display})'

    def normalize_frequency(self):
        """Collapse a custom cycle onto the catalog when they mean the same.

        Picking "Personalizada" and typing 3 is the trimestral option written
        the long way. Left alone the two would be stored differently, show up
        as separate rows in the totals-by-frequency breakdown and split the
        frequency filter in half, so the custom form is rewritten to the
        catalog one. Outside CUSTOM, `custom_months` is simply not a thing.
        """
        if self.frequency != self.Frequency.CUSTOM:
            self.custom_months = None
            return
        for frequency, months in self.FREQUENCY_MONTHS.items():
            if months == self.custom_months:
                self.frequency = frequency
                self.custom_months = None
                return

    def clean(self):
        self.normalize_frequency()
        super().clean()
        if self.frequency == self.Frequency.CUSTOM and not self.custom_months:
            raise ValidationError(
                {
                    'custom_months': (
                        'Indica cada cuántos meses se cobra la frecuencia '
                        'personalizada.'
                    )
                }
            )

    def save(self, *args, **kwargs):
        # Normalizing here and not only in the serializer keeps every write
        # path consistent: panel, MCP tools, admin, imports and fixtures.
        self.normalize_frequency()
        return super().save(*args, **kwargs)

    @property
    def frequency_months(self):
        """Length of the billing cycle in months — the proration divisor."""
        if self.frequency == self.Frequency.CUSTOM:
            return self.custom_months or 1
        return self.FREQUENCY_MONTHS.get(self.frequency, 1)

    @property
    def frequency_display(self):
        """Human label, spelling out the cycle when it is a custom one.

        `get_frequency_display()` would read "Personalizada" for every custom
        record, which tells the operator nothing in the table, the export or
        the totals-by-frequency breakdown.
        """
        if self.frequency == self.Frequency.CUSTOM and self.custom_months:
            return f'Cada {self.custom_months} meses'
        return self.get_frequency_display()

    @property
    def monthly_price(self):
        """Price prorated to a monthly figure, in the record's own currency.

        Sibling of `monthly_cop_cost`: same proration, but it keeps the
        currency the payment was agreed in, so a USD subscription stays
        comparable against other USD ones.
        """
        if not self.price:
            return Decimal('0')
        return (self.price / self.frequency_months).quantize(Decimal('0.01'))

    @property
    def monthly_cop_cost(self):
        """Prorated monthly cost in COP for dashboard aggregation."""
        if not self.cop_equivalent:
            return Decimal('0')
        return (self.cop_equivalent / self.frequency_months).quantize(
            Decimal('0.01')
        )
