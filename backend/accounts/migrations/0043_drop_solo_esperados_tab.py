"""Drop the seeded "Solo esperados" income tab, now a builtin one.

The uncollected-only cut became a fixed tab in ``incomes.vue`` (it is the view's
landing tab, and a saved tab would be silently rewritten by any filter tweak).
Removing it from ``accounts.default_filter_tabs`` is not enough: the registry
never touches users who already have tabs for the view, so every existing user
would see two identically named tabs side by side.
"""
from django.db import migrations
from django.db.models import F

VIEW = 'accounting_income'
MAX_TABS_PER_VIEW = 12

ALL_EXPECTED = 'Todos los esperados'
ONLY_EXPECTED = 'Solo esperados'

ONLY_EXPECTED_FILTERS = {'kind': 'expected', 'paymentStatus': 'pending'}


def drop_only_expected_tab(apps, schema_editor):
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
        # Keep the remaining tabs contiguous: `Meta.ordering` sorts by `order`
        # and a gap would let the next created tab tie with a sibling.
        tabs.filter(order__gt=order).update(order=F('order') - 1)


def restore_only_expected_tab(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

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
        tabs.filter(order__gt=anchor.order).update(order=F('order') + 1)
        SavedFilterTab.objects.create(
            user_id=user_id, view=VIEW, name=ONLY_EXPECTED,
            filters=ONLY_EXPECTED_FILTERS,
            base_filters=ONLY_EXPECTED_FILTERS,
            order=anchor.order + 1,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0042_savedfiltertab_base_filters'),
    ]

    operations = [
        migrations.RunPython(drop_only_expected_tab, restore_only_expected_tab),
    ]
