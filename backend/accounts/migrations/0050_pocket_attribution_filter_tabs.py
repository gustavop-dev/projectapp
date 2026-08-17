"""Add the pocket attribution + unlinked filter tabs to existing users.

The registry in ``accounts.default_filter_tabs`` only reaches users with zero
tabs for the view, so users who already have "Entradas"/"Salidas" would never
see the four new cuts. Same shape as ``0041_income_expected_filter_tabs``:
insert per user, skip what is already there, respect the per-view cap and keep
``order`` contiguous.
"""
from django.db import migrations
from django.db.models import F

VIEW = 'accounting_pocket'
MAX_TABS_PER_VIEW = 12

NEW_TABS = [
    {'name': 'Gustavo', 'filters': {'attribution': ['gustavo']}},
    {'name': 'Carlos', 'filters': {'attribution': ['carlos']}},
    {'name': 'Empresa', 'filters': {'attribution': ['company']}},
    {'name': 'Sin vincular', 'filters': {'linked': 'false'}},
]


def add_attribution_tabs(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    user_ids = list(
        SavedFilterTab.objects.filter(view=VIEW)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        existing = set(tabs.values_list('name', flat=True))
        # Append after whatever the user already has, so a reordered strip and
        # any tab of their own keep their place.
        next_order = (
            max(tabs.values_list('order', flat=True), default=-1) + 1
        )
        count = tabs.count()
        for spec in NEW_TABS:
            if spec['name'] in existing or count >= MAX_TABS_PER_VIEW:
                continue
            SavedFilterTab.objects.create(
                user_id=user_id,
                view=VIEW,
                name=spec['name'],
                filters=spec['filters'],
                # Same value, so "Restaurar filtros" has a point to return to.
                base_filters=dict(spec['filters']),
                order=next_order,
                is_seeded=True,
            )
            next_order += 1
            count += 1


def drop_attribution_tabs(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    names = [spec['name'] for spec in NEW_TABS]
    user_ids = list(
        SavedFilterTab.objects.filter(view=VIEW, name__in=names)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        # Highest order first: removing a row shifts only the tabs above it, so
        # descending keeps the remaining orders contiguous without a rewrite.
        doomed = list(
            tabs.filter(name__in=names).order_by('-order')
            .values_list('id', 'order')
        )
        for tab_id, order in doomed:
            SavedFilterTab.objects.filter(id=tab_id).delete()
            tabs.filter(order__gt=order).update(order=F('order') - 1)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_drop_client_status_tabs'),
    ]

    operations = [
        migrations.RunPython(add_attribution_tabs, drop_attribution_tabs),
    ]
