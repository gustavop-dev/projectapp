"""Replace the MEX nationality with EXT (Extranjero) and apply new rates.

Extranjero covers any country other than Colombia and USA (recent leads come
from Argentina, not México) and always quotes in USD. The price book changes
at the same time (owner-approved, 2026-07-16): COL drops to 30.000 COP/h,
USA to 30 USD/h, EXT starts at 18 USD/h, and the 10-hour «Paquete Inicial»
leaves the catalog. Proposals keep their nationality via a MEX→EXT rename;
their commercial-conditions snapshots in ``content_json`` are not touched.

Data mirrors ``content.services.hour_package_service.DEFAULT_PACKAGES``
(kept inline so this migration stays self-contained; that constant is the
canonical source for the panel's «restore defaults» action).
"""

from django.db import migrations, models

LADDER = [
    # (hours, discount_percent, name_es, name_en, note_es, note_en)
    (1, 0, 'Hora Puntual', 'Single Hour',
     'Para un ajuste express.', 'For a quick one-off tweak.'),
    (20, 10, 'Paquete Ágil', 'Agile Pack',
     'Para iteraciones cortas.', 'For short iterations.'),
    (60, 20, 'Paquete Pro', 'Pro Pack',
     'Para mejoras continuas.', 'For continuous improvements.'),
    (180, 30, 'Paquete Premium', 'Premium Pack',
     'Para la evolución sostenida del producto.',
     'For sustained product evolution.'),
]

RATE_BY_NATIONALITY = {'COL': 30000, 'EXT': 18, 'USA': 30}


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
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    BusinessProposal.objects.filter(nationality='MEX').update(nationality='EXT')
    HourPackage.objects.all().delete()
    for nationality in ('COL', 'EXT', 'USA'):
        HourPackage.objects.bulk_create(_rows(HourPackage, nationality))


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0159_alter_incomerecord_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hourpackage',
            name='nationality',
            field=models.CharField(
                choices=[('COL', 'Colombia'), ('EXT', 'Extranjero'),
                         ('USA', 'Estados Unidos')],
                db_index=True, default='COL', max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name='businessproposal',
            name='nationality',
            field=models.CharField(
                choices=[('COL', 'Colombia'), ('EXT', 'Extranjero'),
                         ('USA', 'Estados Unidos')],
                default='COL',
                help_text='Drives hour-package catalog seeding and suggested currency.',
                max_length=3,
            ),
        ),
        # Irreversible on purpose: the pre-reset rows cannot be reconstructed.
        migrations.RunPython(apply_defaults, migrations.RunPython.noop),
    ]
