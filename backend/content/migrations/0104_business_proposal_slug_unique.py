"""Populate, deduplicate and enforce uniqueness on BusinessProposal.slug.

Up to this point the field was ``blank=True`` and non-unique. This migration:

1. Fills in slugs for rows where it was blank, deriving them from
   ``client_name`` (or a ``propuesta-<id>`` fallback).
2. Resolves collisions deterministically by appending ``-2``, ``-3``… in
   ascending ``id`` order so older rows keep the base slug.
3. Alters the column to ``unique=True`` and ``max_length=120``.
"""
from django.db import migrations, models
from django.utils.text import slugify


def _safe_slug(value, fallback):
    return slugify(value or '') or fallback


def populate_and_dedupe_slug(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')

    instances = list(BusinessProposal.objects.all().order_by('id').only('id', 'slug', 'client_name'))
    taken = set()
    to_update = []
    for inst in instances:
        existing = (inst.slug or '').strip()[:120]
        base = existing or _safe_slug(inst.client_name, f'propuesta-{inst.id}')[:120]
        candidate = base
        counter = 2
        while candidate in taken:
            suffix = f'-{counter}'
            candidate = base[: 120 - len(suffix)] + suffix
            counter += 1
        taken.add(candidate)
        if candidate != inst.slug:
            inst.slug = candidate
            to_update.append(inst)

    if to_update:
        BusinessProposal.objects.bulk_update(to_update, ['slug'], batch_size=500)


def noop_reverse(apps, schema_editor):
    # Values populated by this migration remain valid under the old schema
    # (blank=True, non-unique); no rollback data work is necessary.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0103_swap_value_added_modules_order'),
    ]

    operations = [
        migrations.RunPython(populate_and_dedupe_slug, noop_reverse),
        migrations.AlterField(
            model_name='businessproposal',
            name='slug',
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text=(
                    'Personal, human-friendly handle used in the public URL '
                    '/proposal/<slug>/.'
                ),
                max_length=120,
                unique=True,
            ),
        ),
    ]
