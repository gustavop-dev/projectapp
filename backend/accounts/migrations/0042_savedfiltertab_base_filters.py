"""Backfill the restore point (``base_filters``) of existing saved tabs.

Seeded tabs get their definition from the registry even when the live
``filters`` already drifted (the panel auto-saves filter edits onto the
active tab); user-created or renamed tabs fall back to their current
filters. Importing the live registry is safe here: fresh databases reach
this migration with zero rows, so the backfill only ever touches data
created before it existed.
"""
from django.db import migrations, models

from accounts.default_filter_tabs import DEFAULT_FILTER_TABS


def backfill_base_filters(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')
    registry = {
        (view, spec['name']): spec['filters']
        for view, specs in DEFAULT_FILTER_TABS.items()
        for spec in specs
    }
    tabs = list(SavedFilterTab.objects.all())
    for tab in tabs:
        tab.base_filters = registry.get((tab.view, tab.name), tab.filters)
    SavedFilterTab.objects.bulk_update(tabs, ['base_filters'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0041_income_expected_filter_tabs'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedfiltertab',
            name='base_filters',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(backfill_base_filters, migrations.RunPython.noop),
    ]
