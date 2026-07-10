"""Reset the hour-package catalog to the July 2026 pricing defaults.

COL is replaced in full: the 90.000 COP/h three-tier seed (migration 0144)
gives way to a five-tier ladder starting at a 1-hour package at 40.000 COP/h
(owner-approved pricing test, 2026-07-10). MEX/USA are seeded only when empty
so admin-entered rows are never clobbered.

Data mirrors ``content.services.hour_package_service.DEFAULT_PACKAGES``
(kept inline so this migration stays self-contained; that constant is the
canonical source for the panel's «restore defaults» action).
"""

from django.db import migrations

LADDER = [
    # (hours, discount_percent, name_es, name_en, note_es, note_en)
    (1, 0, 'Hora Puntual', 'Single Hour',
     'Para un ajuste express.', 'For a quick one-off tweak.'),
    (10, 5, 'Paquete Inicial', 'Starter Pack',
     'Para ajustes puntuales.', 'For one-off adjustments.'),
    (20, 10, 'Paquete Ágil', 'Agile Pack',
     'Para iteraciones cortas.', 'For short iterations.'),
    (60, 20, 'Paquete Pro', 'Pro Pack',
     'Para mejoras continuas.', 'For continuous improvements.'),
    (180, 30, 'Paquete Premium', 'Premium Pack',
     'Para la evolución sostenida del producto.',
     'For sustained product evolution.'),
]

RATE_BY_NATIONALITY = {'COL': 40000, 'MEX': 20, 'USA': 35}


def _rows(HourPackage, nationality):
    rate = RATE_BY_NATIONALITY[nationality]
    return [
        HourPackage(
            nationality=nationality, is_active=True, order=index,
            hours=hours, hourly_rate=rate, discount_percent=discount,
            name_es=name_es, name_en=name_en, note_es=note_es, note_en=note_en,
        )
        for index, (hours, discount, name_es, name_en, note_es, note_en)
        in enumerate(LADDER, start=1)
    ]


def apply_defaults(apps, schema_editor):
    HourPackage = apps.get_model('content', 'HourPackage')
    HourPackage.objects.filter(nationality='COL').delete()
    HourPackage.objects.bulk_create(_rows(HourPackage, 'COL'))
    for nationality in ('MEX', 'USA'):
        if not HourPackage.objects.filter(nationality=nationality).exists():
            HourPackage.objects.bulk_create(_rows(HourPackage, nationality))


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0146_hourpackagesettings'),
    ]

    operations = [
        # Irreversible on purpose: the pre-reset rows cannot be reconstructed.
        migrations.RunPython(apply_defaults, migrations.RunPython.noop),
    ]
