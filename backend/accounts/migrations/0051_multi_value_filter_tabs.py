"""Wrap the scalar filter values of saved tabs into single-element lists.

Every filter dimension of the accounting panels became multi-value (a "Cobro"
cut can now be *sin pagos* **and** *parcial* at once), so the matchers read
arrays where these rows still hold a bare string.

Doing this only in the browser would not be enough, and would actively make
things worse: ``sameFilters`` deep-compares ``filters`` against
``base_filters``, so a tab coerced on read would compare unequal against its
own untouched base and light up the "drifted" dot on every seeded tab. Worse,
the auto-save watcher would then persist the coerced ``filters`` while
``base_filters`` kept the scalar — and "Restaurar filtros" would hand back the
old shape. Normalizing both columns here is what keeps the two halves of a tab
speaking the same language.

The frontend still coerces defensively on read (``coerceToDefaultShape``), for
rows written by an older client after this ran.
"""
from django.db import migrations

# Keys that went from a scalar to a list, per view. Anything not listed here
# (ranges, free text, the module selector) keeps its shape.
MULTI_VALUE_KEYS = {
    'accounting_income': ('kind', 'paymentStatus', 'partner', 'ledger', 'muted'),
    'accounting_expense': ('ledger', 'nature'),
    'accounting_hosting': ('isActive',),
    'accounting_pocket': ('direction', 'linked'),
    'accounting_recurring': ('currency', 'cost_type', 'is_active'),
    'accounting_collections': ('status',),
}


def _wrap(filters, keys):
    """Scalar -> ``[scalar]``; empty -> ``[]``. Returns True if it changed."""
    if not isinstance(filters, dict):
        return False
    changed = False
    for key in keys:
        if key not in filters:
            continue
        value = filters[key]
        if isinstance(value, list):
            continue
        filters[key] = [] if value in ('', None) else [value]
        changed = True
    return changed


def _unwrap(filters, keys):
    if not isinstance(filters, dict):
        return False
    changed = False
    for key in keys:
        if key not in filters:
            continue
        value = filters[key]
        if not isinstance(value, list):
            continue
        filters[key] = value[0] if value else ''
        changed = True
    return changed


def _apply(apps, convert):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')
    for view, keys in MULTI_VALUE_KEYS.items():
        for tab in SavedFilterTab.objects.filter(view=view).iterator():
            touched = convert(tab.filters, keys)
            # base_filters is the restore point; leaving it behind would make
            # "Restaurar filtros" undo the migration one tab at a time.
            touched = convert(tab.base_filters, keys) or touched
            if touched:
                tab.save(update_fields=['filters', 'base_filters'])


def to_lists(apps, schema_editor):
    _apply(apps, _wrap)


def to_scalars(apps, schema_editor):
    _apply(apps, _unwrap)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0050_pocket_attribution_filter_tabs'),
    ]

    operations = [
        migrations.RunPython(to_lists, to_scalars),
    ]
