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

    # Build base-slug per row (derive if blank, truncate to 120 chars).
    rows = list(BusinessProposal.objects.all().order_by('id').values('id', 'slug', 'client_name'))
    desired_base = {}
    for row in rows:
        existing = (row['slug'] or '').strip()[:120]
        if existing:
            desired_base[row['id']] = existing
        else:
            desired_base[row['id']] = _safe_slug(row['client_name'], f"propuesta-{row['id']}")[:120]

    # Deduplicate: first row keeps the base, subsequent rows get -2, -3…
    taken = set()
    final = {}
    for row in rows:
        base = desired_base[row['id']]
        candidate = base
        counter = 2
        while candidate in taken:
            suffix = f'-{counter}'
            # Keep under max_length=120 including suffix.
            candidate = (base[: 120 - len(suffix)] + suffix)
            counter += 1
        taken.add(candidate)
        final[row['id']] = candidate

    for row_id, value in final.items():
        BusinessProposal.objects.filter(pk=row_id).update(slug=value)


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
