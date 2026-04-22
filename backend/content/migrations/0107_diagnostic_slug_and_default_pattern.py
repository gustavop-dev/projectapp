"""Populate, deduplicate and enforce uniqueness on WebAppDiagnostic.slug,
and add ``default_slug_pattern`` to DiagnosticDefaultConfig.

Mirrors the proposal slug rollout (migrations 0104 + 0105):

1. Add ``slug`` to WebAppDiagnostic as blank SlugField.
2. Populate slugs by deriving from ``client_name`` (or a ``diagnostico-<id>``
   fallback), resolving collisions deterministically with ``-2``, ``-3``…
3. Alter the column to ``unique=True``.
4. Add ``default_slug_pattern`` CharField to DiagnosticDefaultConfig.
"""
from django.db import migrations, models
from django.utils.text import slugify


def _safe_slug(value, fallback):
    return slugify(value or '') or fallback


def populate_and_dedupe_slug(apps, schema_editor):
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')

    instances = list(
        WebAppDiagnostic.objects.all().order_by('id').only('id', 'slug', 'client_name')
    )
    taken = set()
    to_update = []
    for inst in instances:
        existing = (inst.slug or '').strip()[:120]
        base = existing or _safe_slug(inst.client_name, f'diagnostico-{inst.id}')[:120]
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
        WebAppDiagnostic.objects.bulk_update(to_update, ['slug'], batch_size=500)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0106_proposaldefaultconfig_default_currency_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='webappdiagnostic',
            name='slug',
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text=(
                    'Personal, human-friendly handle used in the public URL '
                    '/diagnostic/<slug>/.'
                ),
                max_length=120,
            ),
        ),
        migrations.RunPython(populate_and_dedupe_slug, noop_reverse),
        migrations.AlterField(
            model_name='webappdiagnostic',
            name='slug',
            field=models.SlugField(
                blank=True,
                db_index=True,
                help_text=(
                    'Personal, human-friendly handle used in the public URL '
                    '/diagnostic/<slug>/.'
                ),
                max_length=120,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='diagnosticdefaultconfig',
            name='default_slug_pattern',
            field=models.CharField(
                blank=True,
                default='{client_name}',
                help_text=(
                    'Template used to auto-generate the public slug when an admin '
                    'does not provide one at creation time. Placeholders: '
                    '{client_name}, {year}. The rendered value is slugified and '
                    'deduplicated with numeric suffixes.'
                ),
                max_length=200,
            ),
        ),
    ]
