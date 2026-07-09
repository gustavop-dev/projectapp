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
    - With ``force``: upsert by ``(user, view, name)`` — update the filters
      of matching tabs, create missing ones, and never delete extra tabs.
    - Respects ``SavedFilterTab.MAX_TABS_PER_VIEW``.

    Returns ``(created_count, updated_count)``.
    """
    defaults = DEFAULT_FILTER_TABS.get(view) or []
    if not defaults:
        return (0, 0)

    existing_qs = SavedFilterTab.objects.filter(user=user, view=view)
    if not force and existing_qs.exists():
        return (0, 0)

    existing = {tab.name: tab for tab in existing_qs}
    created = updated = 0
    for idx, spec in enumerate(defaults[:SavedFilterTab.MAX_TABS_PER_VIEW]):
        tab = existing.get(spec['name'])
        if tab is None:
            if len(existing) + created >= SavedFilterTab.MAX_TABS_PER_VIEW:
                break
            SavedFilterTab.objects.create(
                user=user, view=view, name=spec['name'],
                filters=spec['filters'], order=idx,
            )
            created += 1
        elif tab.filters != spec['filters']:
            tab.filters = spec['filters']
            tab.save(update_fields=['filters', 'updated_at'])
            updated += 1
    return (created, updated)
