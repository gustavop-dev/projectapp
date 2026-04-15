from django.db import models
from django.utils.text import slugify


class DocumentTag(models.Model):
    """Label attached to documents (M2M) for cross-cutting filtering."""

    class Color(models.TextChoices):
        GRAY = 'gray', 'Gris'
        EMERALD = 'emerald', 'Verde'
        BLUE = 'blue', 'Azul'
        YELLOW = 'yellow', 'Amarillo'
        RED = 'red', 'Rojo'
        PURPLE = 'purple', 'Morado'

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    color = models.CharField(
        max_length=16, choices=Color.choices, default=Color.GRAY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'tag'
            slug = base
            index = 2
            while DocumentTag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)
