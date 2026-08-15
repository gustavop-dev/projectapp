"""Drop the seeded proposal-status tabs of the ``client`` view.

The seven cuts (Draft, Sent/Viewed, Negociación, …) became code-level subfilters
of the Propuestas module in ``frontend/constants/clientFilters.js``: /panel/clients
now groups its filters by business module, and the proposal-status ones are fixed
entries of that module rather than per-user rows.

Removing them from ``accounts.default_filter_tabs`` is not enough: the registry
never touches users who already have tabs for the view, so every existing user
would see each status twice — once as a subfilter, once as a saved tab. Dropping
them also gives the twelve-tab budget back to the tabs the user actually saved.

Mirrors ``0043_drop_solo_esperados_tab`` for the same situation.
"""
from django.conf import settings
from django.db import migrations
from django.db.models import F

VIEW = 'client'
MAX_TABS_PER_VIEW = 12

# Seeded names paired with the filters they carried, so the reverse can rebuild
# them exactly as ``seed_filter_tabs`` would have.
STATUS_TABS = [
    ('Draft', {'lastStatuses': ['draft']}),
    ('Sent/Viewed', {'lastStatuses': ['sent', 'viewed']}),
    ('Negociación', {'lastStatuses': ['negotiating']}),
    ('Accepted', {'lastStatuses': ['accepted']}),
    ('Expired', {'lastStatuses': ['expired']}),
    ('Rejected', {'lastStatuses': ['rejected']}),
    ('Finished', {'lastStatuses': ['finished']}),
]


def drop_status_tabs(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')

    names = [name for name, _ in STATUS_TABS]
    user_ids = list(
        SavedFilterTab.objects.filter(view=VIEW, name__in=names)
        .values_list('user_id', flat=True)
        .distinct()
    )
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        # Delete high-to-low so each shift only has to account for one gap:
        # closing them one at a time keeps `order` contiguous, which
        # `Meta.ordering` relies on to break ties for newly created tabs.
        doomed = list(
            tabs.filter(name__in=names).order_by('-order').values_list('id', 'order')
        )
        for tab_id, order in doomed:
            tabs.filter(id=tab_id).delete()
            tabs.filter(order__gt=order).update(order=F('order') - 1)


def restore_status_tabs(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    # Staff, not "whoever still has client tabs": the forward pass can leave a
    # user with none at all, and those are exactly the ones to rebuild. It is
    # also the audience ``seed_filter_tabs`` targets.
    user_ids = list(User.objects.filter(is_staff=True).values_list('id', flat=True))
    for user_id in user_ids:
        tabs = SavedFilterTab.objects.filter(user_id=user_id, view=VIEW)
        existing = set(tabs.values_list('name', flat=True))
        next_order = (
            max(tabs.values_list('order', flat=True), default=-1) + 1
        )
        for name, filters in STATUS_TABS:
            if name in existing:
                continue
            if tabs.count() >= MAX_TABS_PER_VIEW:
                break
            SavedFilterTab.objects.create(
                user_id=user_id, view=VIEW, name=name,
                filters=filters, base_filters=filters, order=next_order,
            )
            next_order += 1


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0046_savedfiltertab_collections_view'),
    ]

    operations = [
        migrations.RunPython(drop_status_tabs, restore_status_tabs),
    ]
