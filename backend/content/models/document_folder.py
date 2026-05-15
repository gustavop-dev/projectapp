from django.core.exceptions import ValidationError
from django.db import models

from content.utils import safe_slug


MAX_FOLDER_DEPTH = 5  # depth values 0..4 — root is 0, deepest leaf is 4


class DocumentFolder(models.Model):
    """Hierarchical folder used to organize documents in the admin panel."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
    )
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

    def get_depth(self):
        """0 for a root folder, +1 for each ancestor."""
        depth = 0
        current = self.parent
        seen = set()
        while current is not None:
            if current.pk in seen:
                break  # defensive: cycle in stored data
            seen.add(current.pk)
            depth += 1
            current = current.parent
        return depth

    def get_ancestors(self):
        """List of ancestors ordered root→parent (excludes self)."""
        chain = []
        current = self.parent
        seen = set()
        while current is not None:
            if current.pk in seen:
                break
            seen.add(current.pk)
            chain.append(current)
            current = current.parent
        chain.reverse()
        return chain

    def get_descendant_ids(self, include_self=False):
        """All descendant ids (BFS over `children`). Optionally include self."""
        result = set()
        if include_self and self.pk is not None:
            result.add(self.pk)
        if self.pk is None:
            return result
        frontier = [self.pk]
        while frontier:
            child_ids = list(
                DocumentFolder.objects.filter(parent_id__in=frontier).values_list('id', flat=True)
            )
            if not child_ids:
                break
            new_ids = [cid for cid in child_ids if cid not in result]
            if not new_ids:
                break
            result.update(new_ids)
            frontier = new_ids
        return result

    def clean(self):
        """Validate parent assignment: no self-parent, no cycle, depth ≤ MAX."""
        super().clean()
        if self.parent_id is None:
            return
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({'parent': 'Una carpeta no puede ser su propio padre.'})
        if self.pk:
            descendants = self.get_descendant_ids(include_self=False)
            if self.parent_id in descendants:
                raise ValidationError(
                    {'parent': 'No se puede mover una carpeta dentro de sus descendientes.'}
                )
        parent_depth = self.parent.get_depth() if self.parent else -1
        if parent_depth + 1 >= MAX_FOLDER_DEPTH:
            raise ValidationError(
                {'parent': f'Profundidad máxima de {MAX_FOLDER_DEPTH} niveles excedida.'}
            )
