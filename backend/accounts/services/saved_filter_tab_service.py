"""
Seeding helpers for the code-level ``SavedFilterTab`` defaults.

The registry lives in ``accounts.default_filter_tabs``; this module turns it
into per-user rows without ever clobbering tabs the user created or renamed.
"""

from accounts.default_filter_tabs import DEFAULT_FILTER_TABS
from accounts.models import SavedFilterTab


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

    existing_qs = SavedFilterTab.objects.filter(user=user, view=view)
    if not force and existing_qs.exists():
        return (0, 0)

    all_tabs = list(existing_qs)
    # Matching is restricted to the factory rows: a user's tab that happens to
    # be called "Fallidos" too is their own, and re-seeding must not overwrite
    # its filters or claim it as seeded.
    seeded = {tab.name: tab for tab in all_tabs if tab.is_seeded}
    created = updated = 0
    for idx, spec in enumerate(defaults[:SavedFilterTab.MAX_TABS_PER_VIEW]):
        tab = seeded.get(spec['name'])
        if tab is None:
            if len(all_tabs) + created >= SavedFilterTab.MAX_TABS_PER_VIEW:
                break
            SavedFilterTab.objects.create(
                user=user, view=view, name=spec['name'],
                filters=spec['filters'], base_filters=spec['filters'],
                order=idx, is_seeded=True,
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


def reset_default_tabs(user, view):
    """Put a view's factory tabs back, leaving the user's own alone.

    Only the seeded rows are dropped and re-created; a tab the user saved is
    theirs and outlives the reset. Restoring used to wipe the whole view,
    which made "Restablecer" a button people learned not to press.
    """
    SavedFilterTab.objects.filter(
        user=user, view=view, is_seeded=True,
    ).delete()
    return seed_default_tabs(user, view, force=True)


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
