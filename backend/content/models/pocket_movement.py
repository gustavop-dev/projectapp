from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .accounting_base import AccountingRecordBase


class PocketMovement(AccountingRecordBase):
    """
    Ledger entry of the company pocket (Bolsillo ProjectApp).

    Direction + positive amount keeps validation trivial and aggregation
    explicit: balance = Sum(in) - Sum(out). Movements can be auto-managed
    by income records (see the `pocket_movement` reverse relation);
    those rows are not editable through the pocket CRUD.
    """

    class Direction(models.TextChoices):
        IN = 'in', 'Ingreso'
        OUT = 'out', 'Egreso'

    concept = models.CharField(max_length=255)
    movement_date = models.DateField()
    direction = models.CharField(max_length=3, choices=Direction.choices)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['movement_date']),
        ]

    def __str__(self):
        sign = '+' if self.direction == self.Direction.IN else '-'
        return f'{self.concept} ({sign}{self.amount})'

    @property
    def is_auto_managed(self):
        """True when this movement is controlled by an income record."""
        return getattr(self, 'income_record', None) is not None
