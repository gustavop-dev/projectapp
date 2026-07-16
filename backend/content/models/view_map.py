from django.db import models


class ViewMapSettings(models.Model):
    """
    Singleton storing view-map panel preferences.

    Usage:
        settings = ViewMapSettings.load()
        settings.default_view_mode  # → 'list' | 'map'
        settings.default_filters    # → {'categories': [...], 'audiences': [...], 'viewTypes': [...]}
    """

    class ViewMode(models.TextChoices):
        LIST = 'list', 'Lista'
        MAP = 'map', 'Mapa'

    default_view_mode = models.CharField(
        max_length=10, choices=ViewMode.choices, default=ViewMode.LIST,
    )
    # Same camelCase shape as SavedFilterTab.filters for the view_map view:
    # keys categories/audiences/viewTypes, each a list of strings.
    default_filters = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'View map settings'
        verbose_name_plural = 'View map settings'

    def __str__(self):
        return f'ViewMapSettings — vista {self.default_view_mode}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
