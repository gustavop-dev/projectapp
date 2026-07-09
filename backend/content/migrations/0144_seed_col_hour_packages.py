"""Seed the COL hour-package catalog from the historical hardcoded defaults.

Mirrors the three packages defined in proposal_service DEFAULT_SECTIONS /
DEFAULT_SECTIONS_EN (commercial_conditions section) so the panel catalog
starts populated and proposal seeding output stays identical to the
pre-catalog behavior. MEX/USA start empty: proposal creation falls back to
the hardcoded defaults until the admin creates packages for them.
"""

from django.db import migrations

SEED_COL_PACKAGES = [
    {
        'name_es': 'Paquete Ágil',
        'name_en': 'Agile Pack',
        'note_es': 'Ideal para ajustes puntuales.',
        'note_en': 'Ideal for one-off adjustments.',
        'hours': 20,
        'hourly_rate': 90000,
        'discount_percent': 0,
        'order': 1,
    },
    {
        'name_es': 'Paquete Pro',
        'name_en': 'Pro Pack',
        'note_es': 'Para mejoras continuas.',
        'note_en': 'For continuous improvements.',
        'hours': 60,
        'hourly_rate': 90000,
        'discount_percent': 10,
        'order': 2,
    },
    {
        'name_es': 'Paquete Premium',
        'name_en': 'Premium Pack',
        'note_es': 'Para la evolución sostenida del producto.',
        'note_en': 'For sustained product evolution.',
        'hours': 180,
        'hourly_rate': 90000,
        'discount_percent': 30,
        'order': 3,
    },
]


def seed_col_packages(apps, schema_editor):
    HourPackage = apps.get_model('content', 'HourPackage')
    if HourPackage.objects.exists():
        return
    HourPackage.objects.bulk_create(
        HourPackage(nationality='COL', is_active=True, **fields)
        for fields in SEED_COL_PACKAGES
    )


def unseed_col_packages(apps, schema_editor):
    HourPackage = apps.get_model('content', 'HourPackage')
    HourPackage.objects.filter(
        nationality='COL',
        name_es__in=[fields['name_es'] for fields in SEED_COL_PACKAGES],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0143_hourpackage_businessproposal_nationality'),
    ]

    operations = [
        migrations.RunPython(seed_col_packages, unseed_col_packages),
    ]
