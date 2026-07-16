from django.db import models


class Nationality(models.TextChoices):
    COL = 'COL', 'Colombia'
    EXT = 'EXT', 'Extranjero'
    USA = 'USA', 'Estados Unidos'


# Pricing currency implied by each nationality. EXT covers any country other
# than Colombia and USA and always quotes in USD by commercial decision.
CURRENCY_BY_NATIONALITY = {
    Nationality.COL: 'COP',
    Nationality.EXT: 'USD',
    Nationality.USA: 'USD',
}


class HourPackage(models.Model):
    """
    Catalog entry for a post-delivery development hour package.

    Each package belongs to one nationality (COL/EXT/USA); the pricing
    currency is derived from it (COL→COP, EXT/USA→USD). Active packages
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


class HourPackageSettings(models.Model):
    """
    Singleton storing hour-packages panel preferences.

    Usage:
        settings = HourPackageSettings.load()
        settings.default_view_mode  # → 'table' | 'cards' | 'compare'
    """

    class ViewMode(models.TextChoices):
        TABLE = 'table', 'Tabla'
        CARDS = 'cards', 'Tarjetas'
        COMPARE = 'compare', 'Comparativa'

    default_view_mode = models.CharField(
        max_length=10, choices=ViewMode.choices, default=ViewMode.TABLE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hour package settings'
        verbose_name_plural = 'Hour package settings'

    def __str__(self):
        return f'HourPackageSettings — vista {self.default_view_mode}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
