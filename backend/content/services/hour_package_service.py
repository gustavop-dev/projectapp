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

# Canonical catalog defaults per nationality. The «restore defaults» panel
# action and the data migration that reset the catalog both derive from this
# table. Rates: COL base $40.000 COP/h (July 2026 pricing test), MEX $20
# USD/h, USA $35 USD/h; the discount ladder is shared.
DEFAULT_PACKAGES = {
    'COL': [
        {'name_es': 'Hora Puntual', 'name_en': 'Single Hour',
         'note_es': 'Para un ajuste express.', 'note_en': 'For a quick one-off tweak.',
         'hours': 1, 'hourly_rate': 40000, 'discount_percent': 0, 'order': 1},
        {'name_es': 'Paquete Inicial', 'name_en': 'Starter Pack',
         'note_es': 'Para ajustes puntuales.', 'note_en': 'For one-off adjustments.',
         'hours': 10, 'hourly_rate': 40000, 'discount_percent': 5, 'order': 2},
        {'name_es': 'Paquete Ágil', 'name_en': 'Agile Pack',
         'note_es': 'Para iteraciones cortas.', 'note_en': 'For short iterations.',
         'hours': 20, 'hourly_rate': 40000, 'discount_percent': 10, 'order': 3},
        {'name_es': 'Paquete Pro', 'name_en': 'Pro Pack',
         'note_es': 'Para mejoras continuas.', 'note_en': 'For continuous improvements.',
         'hours': 60, 'hourly_rate': 40000, 'discount_percent': 20, 'order': 4},
        {'name_es': 'Paquete Premium', 'name_en': 'Premium Pack',
         'note_es': 'Para la evolución sostenida del producto.',
         'note_en': 'For sustained product evolution.',
         'hours': 180, 'hourly_rate': 40000, 'discount_percent': 30, 'order': 5},
    ],
}
_LADDER = [(1, 0), (10, 5), (20, 10), (60, 20), (180, 30)]
for _nat, _rate in (('MEX', 20), ('USA', 35)):
    DEFAULT_PACKAGES[_nat] = [
        {**pkg, 'hourly_rate': _rate, 'discount_percent': disc}
        for pkg, (_hours, disc) in zip(DEFAULT_PACKAGES['COL'], _LADDER)
    ]


def restore_default_packages(nationality):
    """Replace the ``nationality`` catalog with :data:`DEFAULT_PACKAGES` rows.

    Destructive on purpose: the panel action asks for confirmation before
    calling this. Returns the freshly created packages.
    """
    HourPackage.objects.filter(nationality=nationality).delete()
    return HourPackage.objects.bulk_create(
        HourPackage(nationality=nationality, is_active=True, **fields)
        for fields in DEFAULT_PACKAGES[nationality]
    )


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
