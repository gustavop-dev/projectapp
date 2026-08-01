from decimal import Decimal

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
        MONTHLY = 'monthly', 'Mensual'
        ANNUAL = 'annual', 'Anual'
        BIENNIAL = 'biennial', 'Cada 2 años'
        TRIENNIAL = 'triennial', 'Cada 3 años'

    FREQUENCY_MONTHS = {
        Frequency.MONTHLY: 1,
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
        max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY,
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
        return f'{self.name} ({self.get_frequency_display()})'

    @property
    def monthly_price(self):
        """Price prorated to a monthly figure, in the record's own currency.

        Sibling of `monthly_cop_cost`: same proration, but it keeps the
        currency the payment was agreed in, so a USD subscription stays
        comparable against other USD ones.
        """
        months = self.FREQUENCY_MONTHS.get(self.frequency, 1)
        if not self.price:
            return Decimal('0')
        return (self.price / months).quantize(Decimal('0.01'))

    @property
    def monthly_cop_cost(self):
        """Prorated monthly cost in COP for dashboard aggregation."""
        months = self.FREQUENCY_MONTHS.get(self.frequency, 1)
        if not self.cop_equivalent:
            return Decimal('0')
        return (self.cop_equivalent / months).quantize(Decimal('0.01'))
