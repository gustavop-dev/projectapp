from django.db import models


class Nationality(models.TextChoices):
    COL = 'COL', 'Colombia'
    MEX = 'MEX', 'México'
    USA = 'USA', 'Estados Unidos'


# Pricing currency implied by each nationality. MEX quotes in USD by
# commercial decision (no MXN support in the proposal currency enum).
CURRENCY_BY_NATIONALITY = {
    Nationality.COL: 'COP',
    Nationality.MEX: 'USD',
    Nationality.USA: 'USD',
}


class HourPackage(models.Model):
    """
    Catalog entry for a post-delivery development hour package.

    Each package belongs to one nationality (COL/MEX/USA); the pricing
    currency is derived from it (COL→COP, MEX/USA→USD). Active packages
    seed the ``commercial_conditions`` section of newly created proposals
    matching the proposal's nationality; when the catalog is empty for a
    nationality, proposal creation falls back to the hardcoded defaults.
    """

    nationality = models.CharField(
        max_length=3,
        choices=Nationality.choices,
        default=Nationality.COL,
        db_index=True,
    )
    name_es = models.CharField(max_length=255, verbose_name='Name (Spanish)')
    name_en = models.CharField(max_length=255, verbose_name='Name (English)')
    note_es = models.TextField(blank=True, default='')
    note_en = models.TextField(blank=True, default='')
    hours = models.PositiveIntegerField()
    hourly_rate = models.DecimalField(max_digits=14, decimal_places=2)
    discount_percent = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text='Manual sort order (lower first).')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nationality', 'order', 'hours']
        verbose_name = 'Hour Package'
        verbose_name_plural = 'Hour Packages'

    def __str__(self):
        return f'{self.name_es} ({self.nationality}, {self.hours}h)'

    @property
    def currency(self):
        return CURRENCY_BY_NATIONALITY[self.nationality]
