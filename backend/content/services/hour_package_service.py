"""Seeding of proposal commercial conditions from the hour-package catalog.

The ``commercial_conditions`` section of a proposal (PDF-only appendix) lists
post-delivery hour packages. Historically its packages were hardcoded in
``proposal_service`` defaults; the :class:`content.models.HourPackage` catalog
makes them administrable per nationality (COL/MEX/USA). This service replaces
the default packages with catalog data at proposal-creation time, falling back
to the hardcoded defaults when the catalog has no active packages for the
proposal's nationality.
"""

import copy

from content.models import CURRENCY_BY_NATIONALITY, HourPackage


def seed_commercial_conditions_from_catalog(content_json, *, nationality, language):
    """Return a copy of ``content_json`` seeded from the hour-package catalog.

    Replaces ``currency``, ``hourlyRate`` and ``packages`` with the active
    catalog packages for ``nationality`` (names/notes localized by
    ``language``). Every seeded package carries its own ``hourlyRate`` so
    per-package pricing survives even when rates differ; the section-level
    ``hourlyRate`` keeps the first package's rate as the editor baseline.

    When the catalog has no active packages for ``nationality``, the input is
    returned untouched (hardcoded defaults remain in effect). Titles, intro
    texts, effort badge and scope clause are never modified — they belong to
    the language defaults, not to the catalog.
    """
    packages = list(
        HourPackage.objects.filter(
            nationality=nationality, is_active=True,
        ).order_by('order', 'hours')
    )
    if not packages:
        return content_json

    seeded = copy.deepcopy(content_json)
    seeded['currency'] = CURRENCY_BY_NATIONALITY[nationality]
    seeded['hourlyRate'] = float(packages[0].hourly_rate)
    seeded['packages'] = [
        {
            'name': pkg.name_en if language == 'en' else pkg.name_es,
            'hours': pkg.hours,
            'discountPercent': pkg.discount_percent,
            'note': pkg.note_en if language == 'en' else pkg.note_es,
            'hourlyRate': float(pkg.hourly_rate),
        }
        for pkg in packages
    ]
    return seeded
