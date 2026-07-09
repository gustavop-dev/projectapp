from django.core.management.base import BaseCommand

from content.models import HourPackage

# COL packages are seeded by migration 0144 (mirrors the historical defaults);
# this command fills the MEX/USA tiers with USD demo pricing so the panel
# nationality tabs and proposal seeding are exercisable in dev/staging.
DEMO_PACKAGES = [
    {
        'nationality': 'MEX',
        'name_es': 'Paquete Ágil MX', 'name_en': 'Agile Pack MX',
        'note_es': 'Ideal para ajustes puntuales.',
        'note_en': 'Ideal for one-off adjustments.',
        'hours': 20, 'hourly_rate': 45, 'discount_percent': 0, 'order': 1,
    },
    {
        'nationality': 'MEX',
        'name_es': 'Paquete Pro MX', 'name_en': 'Pro Pack MX',
        'note_es': 'Para mejoras continuas.',
        'note_en': 'For continuous improvements.',
        'hours': 60, 'hourly_rate': 45, 'discount_percent': 10, 'order': 2,
    },
    {
        'nationality': 'MEX',
        'name_es': 'Paquete Premium MX', 'name_en': 'Premium Pack MX',
        'note_es': 'Para la evolución sostenida del producto.',
        'note_en': 'For sustained product evolution.',
        'hours': 180, 'hourly_rate': 45, 'discount_percent': 30, 'order': 3,
    },
    {
        'nationality': 'USA',
        'name_es': 'Paquete Ágil US', 'name_en': 'Agile Pack US',
        'note_es': 'Ideal para ajustes puntuales.',
        'note_en': 'Ideal for one-off adjustments.',
        'hours': 20, 'hourly_rate': 60, 'discount_percent': 0, 'order': 1,
    },
    {
        'nationality': 'USA',
        'name_es': 'Paquete Pro US', 'name_en': 'Pro Pack US',
        'note_es': 'Para mejoras continuas.',
        'note_en': 'For continuous improvements.',
        'hours': 60, 'hourly_rate': 60, 'discount_percent': 10, 'order': 2,
    },
    {
        'nationality': 'USA',
        'name_es': 'Paquete Premium US', 'name_en': 'Premium Pack US',
        'note_es': 'Para la evolución sostenida del producto.',
        'note_en': 'For sustained product evolution.',
        'hours': 180, 'hourly_rate': 60, 'discount_percent': 30, 'order': 3,
    },
]


class Command(BaseCommand):
    help = (
        'Seed demo hour packages for MEX and USA (USD pricing). '
        'Idempotent: existing packages (matched by nationality + name_es) are kept.'
    )

    def handle(self, *args, **options):
        created = 0
        for fields in DEMO_PACKAGES:
            _, was_created = HourPackage.objects.get_or_create(
                nationality=fields['nationality'],
                name_es=fields['name_es'],
                defaults=fields,
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f'Hour packages: {created} created, '
            f'{len(DEMO_PACKAGES) - created} already existed.'
        ))
