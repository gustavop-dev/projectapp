from django.db import models

from content.utils import safe_slug


class DocumentFolder(models.Model):
    """Carpeta jerárquica para organizar documentos en el panel admin.

    Soporta anidación ilimitada vía la self-FK `parent`: las carpetas sin
    padre son raíces; las demás son subcarpetas.
    """

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='children',
        null=True,
        blank=True,
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = safe_slug(self.name, 'folder')
            slug = base
            index = 2
            while DocumentFolder.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_ancestors(self):
        """Devuelve la cadena de carpetas desde la raíz hasta el padre directo."""
        ancestors = []
        node = self.parent
        visited = set()
        while node is not None and node.pk not in visited:
            visited.add(node.pk)
            ancestors.append(node)
            node = node.parent
        ancestors.reverse()
        return ancestors

    def get_descendant_ids(self):
        """Devuelve el set de IDs de todas las subcarpetas (recursivo)."""
        descendant_ids = set()
        pending = list(self.children.values_list('pk', flat=True))
        while pending:
            child_id = pending.pop()
            if child_id in descendant_ids:
                continue
            descendant_ids.add(child_id)
            pending.extend(
                DocumentFolder.objects.filter(parent_id=child_id)
                .values_list('pk', flat=True)
            )
        return descendant_ids
