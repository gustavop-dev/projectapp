from django.db import models

from content.utils import safe_slug


class RecurringCategory(models.Model):
    """User-editable grouping for recurring payments.

    The panel groups the Recurrentes tab by these categories and shows a
    monthly COP subtotal per group, so the taxonomy has to follow how the
    operator actually thinks about the spend (AI, ads, infrastructure...)
    rather than a fixed list baked into the code.
    """

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    order = models.PositiveIntegerField(
        default=0, help_text='Manual sort order (lower first).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Recurring categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = safe_slug(self.name, 'category')
            slug = base
            index = 2
            while RecurringCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)
