"""Split the accounting income "Esperados" tab in two.

The registry in ``accounts.default_filter_tabs`` only reaches users with zero
tabs for the view, and ``seed_default_tabs(force=True)`` upserts by name
without deleting anything — a plain re-seed would leave the old "Esperados"
tab orphaned next to the two new ones. So the rename and the insertion of
"Solo esperados" happen here, per user.
"""
from django.db import migrations
from django.db.models import F

VIEW = 'accounting_income'
MAX_TABS_PER_VIEW = 12

OLD_NAME = 'Esperados'
ALL_EXPECTED = 'Todos los esperados'
ONLY_EXPECTED = 'Solo esperados'

ALL_EXPECTED_FILTERS = {'kind': 'expected'}
ONLY_EXPECTED_FILTERS = {'kind': 'expected', 'paymentStatus': 'pending'}


def split_expected_tab(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    SavedFilterTab.objects.filter(view=VIEW, name=OLD_NAME).update(
        name=ALL_EXPECTED, filters=ALL_EXPECTED_FILTERS,
    )

    user_ids = list(
        SavedFilterTab.objects.filter(view=VIEW)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        if tabs.filter(name=ONLY_EXPECTED).exists():
            continue
        if tabs.count() >= MAX_TABS_PER_VIEW:
            continue
        anchor = tabs.filter(name=ALL_EXPECTED).first()
        if anchor is None:
            continue
        # `Meta.ordering` breaks ties by `created_at`, so the brand-new tab
        # would sink below every sibling sharing its order without this shift.
        tabs.filter(order__gt=anchor.order).update(order=F('order') + 1)
        SavedFilterTab.objects.create(
            user_id=user_id, view=VIEW, name=ONLY_EXPECTED,
            filters=ONLY_EXPECTED_FILTERS, order=anchor.order + 1,
        )


def merge_expected_tab(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    user_ids = list(
        SavedFilterTab.objects.filter(view=VIEW, name=ONLY_EXPECTED)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        removed = tabs.filter(name=ONLY_EXPECTED).first()
        order = removed.order
        removed.delete()
        tabs.filter(order__gt=order).update(order=F('order') - 1)

    SavedFilterTab.objects.filter(view=VIEW, name=ALL_EXPECTED).update(
        name=OLD_NAME, filters=ALL_EXPECTED_FILTERS,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0040_alter_savedfiltertab_view'),
    ]

    operations = [
        migrations.RunPython(split_expected_tab, merge_expected_tab),
    ]
