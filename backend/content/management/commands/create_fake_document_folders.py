"""Seed a realistic nested folder tree for local development.

Builds three root folders with mixed depths so all nested-folder branches
(recursive filter, recursive count, drag reparent, drag reorder, breadcrumb
chip, depth limit, double-delete-guard) are exercisable from the UI.

Tree layout::

    Clientes
    ├── Activos
    │   ├── 2026
    │   │   └── Contratos          (depth 3)
    │   └── Pendientes de firma
    ├── Inactivos
    └── Prospectos

    Internos
    ├── Plantillas
    └── Recursos legales
        └── NDAs                    (depth 2)

    Archivo                         (empty — covers the empty-leaf branch)

Idempotent: re-running does not duplicate folders.
"""
from django.core.management.base import BaseCommand

from content.models import DocumentFolder


TREE = [
    ('Clientes', [
        ('Activos', [
            ('2026', [
                ('Contratos', []),
            ]),
            ('Pendientes de firma', []),
        ]),
        ('Inactivos', []),
        ('Prospectos', []),
    ]),
    ('Internos', [
        ('Plantillas', []),
        ('Recursos legales', [
            ('NDAs', []),
        ]),
    ]),
    ('Archivo', []),
]


def _create_subtree(specs, parent=None, order_offset=0):
    """Recursively create folders, returning a count of folders touched."""
    touched = 0
    for index, (name, children) in enumerate(specs):
        folder, created = DocumentFolder.objects.get_or_create(
            name=name,
            parent=parent,
            defaults={'order': order_offset + index},
        )
        touched += 1
        if children:
            touched += _create_subtree(children, parent=folder)
    return touched


class Command(BaseCommand):
    help = 'Seed a 3-tree nested folder hierarchy for documents (idempotent).'

    def handle(self, *args, **options):
        touched = _create_subtree(TREE)
        total = DocumentFolder.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'{touched} folder(s) ensured (total in DB: {total}).'
            )
        )
