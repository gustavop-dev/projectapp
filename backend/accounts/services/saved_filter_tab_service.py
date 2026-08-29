"""
Seeding helpers for the code-level ``SavedFilterTab`` defaults.

The registry lives in ``accounts.default_filter_tabs``; this module turns it
into per-user rows without ever clobbering tabs the user created or renamed.
"""

from django.db import models, transaction

from accounts.default_filter_tabs import BUILTIN_FILTER_TABS, DEFAULT_FILTER_TABS
from accounts.models import SavedFilterTab


def builtin_order_offset(view):
    """How many order slots the builtins reserve at the front of ``view``."""
    return len(BUILTIN_FILTER_TABS.get(view) or [])


@transaction.atomic
def seed_builtin_tabs(user, view):
    """
    Idempotently create the placeholder rows for ``view``'s builtin filters.

    A placeholder exists so a builtin quick-filter can be dragged and hidden
    like any other chip: it carries ``order`` and ``is_hidden`` and nothing
    else. ``filters`` stays empty on purpose — the definition lives in the
    frontend constant that ``builtin_key`` matches, which is what keeps a
    date-based builtin like "Hoy" from freezing on the day it was seeded.

    Placeholders take the FIRST order slots, so the factory order reads
    builtins -> seeded -> the user's own: exactly what the strip rendered
    back when builtins had no rows and were simply concatenated first.

    Runs on every GET, so the no-op path is one query. Returns rows created.
    """
    specs = BUILTIN_FILTER_TABS.get(view) or []
    if not specs:
        return 0

    rows = list(
        SavedFilterTab.objects.select_for_update()
        .filter(user=user, view=view)
        .order_by('order', 'created_at')
    )
    existing = {row.builtin_key for row in rows if row.builtin_key}
    missing = [
        (idx, spec) for idx, spec in enumerate(specs)
        if spec['key'] not in existing
    ]
    if not missing:
        return 0

    SavedFilterTab.objects.bulk_create(
        [
            SavedFilterTab(
                user=user, view=view, name=spec['name'],
                builtin_key=spec['key'], order=idx,
            )
            for idx, spec in missing
        ],
        # Two tabs of the same view opening at once both see the row missing;
        # the unique constraint turns the loser into a no-op instead of a 500.
        ignore_conflicts=True,
    )
    # This is the upgrade path for a view that already had user-created tabs
    # before it gained builtins (Communications is the first such view). The
    # factory strip gets its canonical leading slots once; the user's existing
    # relative order is preserved after it.
    if not existing:
        own_rows = [row for row in rows if not row.builtin_key]
        changed = []
        for index, tab in enumerate(own_rows, start=len(specs)):
            if tab.order != index:
                tab.order = index
                changed.append(tab)
        if changed:
            SavedFilterTab.objects.bulk_update(changed, ['order'])
    return len(missing)


def seed_default_tabs(user, view, *, force=False):
    """
    Idempotently create the registry defaults for ``(user, view)``.

    - No-op when the registry has no defaults for ``view``.
    - Without ``force``: no-op when the user already has ANY tab for the
      view (no-clobber; a single ``.exists()`` query in the common case).
    - With ``force``: upsert by ``(user, view, name)`` over the SEEDED rows —
      update the filters of matching tabs, create missing ones, and never
      delete or rewrite a tab the user saved, even one that happens to share
      a factory name.
    - Respects ``SavedFilterTab.MAX_TABS_PER_VIEW``.

    Returns ``(created_count, updated_count)``.
    """
    defaults = DEFAULT_FILTER_TABS.get(view) or []
    if not defaults:
        return (0, 0)

    # Placeholders are scaffolding, not tabs: they must not count as "the user
    # already has tabs here" (seeding them first would otherwise cancel the
    # factory seeding for every new user), nor eat slots from the cap.
    existing_qs = SavedFilterTab.objects.filter(
        user=user, view=view, builtin_key='',
    )
    if not force and existing_qs.exists():
        return (0, 0)

    all_tabs = list(existing_qs)
    # Matching is restricted to the factory rows: a user's tab that happens to
    # be called "Fallidos" too is their own, and re-seeding must not overwrite
    # its filters or claim it as seeded.
    seeded = {tab.name: tab for tab in all_tabs if tab.is_seeded}
    # The builtins hold the first slots, so the seeded ones start after them.
    offset = builtin_order_offset(view)
    created = updated = 0
    for idx, spec in enumerate(defaults[:SavedFilterTab.MAX_TABS_PER_VIEW]):
        tab = seeded.get(spec['name'])
        if tab is None:
            if len(all_tabs) + created >= SavedFilterTab.MAX_TABS_PER_VIEW:
                break
            SavedFilterTab.objects.create(
                user=user, view=view, name=spec['name'],
                filters=spec['filters'], base_filters=spec['filters'],
                order=offset + idx, is_seeded=True,
            )
            created += 1
        elif (
            tab.filters != spec['filters']
            or tab.base_filters != spec['filters']
        ):
            tab.filters = spec['filters']
            tab.base_filters = spec['filters']
            tab.save(update_fields=['filters', 'base_filters', 'updated_at'])
            updated += 1
    return (created, updated)


@transaction.atomic
def reset_default_tabs(user, view):
    """Put a view's factory tabs back, leaving the user's own alone.

    Only the seeded rows and the builtin placeholders are dropped and rebuilt;
    a tab the user saved is theirs and outlives the reset. Restoring used to
    wipe the whole view, which made "Restablecer" a button people learned not
    to press.

    Dropping the placeholders is what returns the builtins to their factory
    position (and un-hides any that were hidden), so one button covers the
    whole strip instead of the order needing a reset mechanism of its own.
    """
    SavedFilterTab.objects.filter(user=user, view=view).filter(
        models.Q(is_seeded=True) | ~models.Q(builtin_key=''),
    ).delete()
    seed_builtin_tabs(user, view)
    result = seed_default_tabs(user, view, force=True)

    factory_count = SavedFilterTab.objects.filter(
        user=user, view=view,
    ).filter(
        models.Q(is_seeded=True) | ~models.Q(builtin_key=''),
    ).count()
    own_tabs = list(
        SavedFilterTab.objects.filter(
            user=user, view=view, is_seeded=False, builtin_key='',
        ).order_by('order', 'created_at')
    )
    changed = []
    for index, tab in enumerate(own_tabs, start=factory_count):
        if tab.order != index:
            tab.order = index
            changed.append(tab)
    if changed:
        SavedFilterTab.objects.bulk_update(changed, ['order'])
    return result


def reorder_tabs(user, view, ids):
    """Apply the strip's order, ignoring ids that are not the user's."""
    tabs = {
        tab.id: tab
        for tab in SavedFilterTab.objects.filter(user=user, view=view)
    }
    changed = []
    for position, raw_id in enumerate(ids):
        try:
            tab = tabs.get(int(raw_id))
        except (TypeError, ValueError):
            continue
        if tab is not None and tab.order != position:
            tab.order = position
            changed.append(tab)
    if changed:
        SavedFilterTab.objects.bulk_update(changed, ['order'])
    return len(changed)
