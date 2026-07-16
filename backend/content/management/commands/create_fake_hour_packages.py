from django.core.management.base import BaseCommand

from content.models import HourPackage
from content.services.hour_package_service import DEFAULT_PACKAGES

# All three nationalities are normally seeded by migration 0147 from the
# canonical DEFAULT_PACKAGES ladder; this command only refills a nationality
# whose catalog was emptied (e.g. after delete_fake_data or manual cleanup)
# so the panel tabs and proposal seeding stay exercisable in dev/staging.


class Command(BaseCommand):
    help = (
        'Seed the default hour packages for any nationality whose catalog '
        'is empty (COL/EXT/USA). Idempotent: non-empty catalogs are kept.'
    )

    def handle(self, *args, **options):
        created = 0
        for nationality, packages in DEFAULT_PACKAGES.items():
            if HourPackage.objects.filter(nationality=nationality).exists():
                continue
            HourPackage.objects.bulk_create(
                HourPackage(nationality=nationality, is_active=True, **fields)
                for fields in packages
            )
            created += len(packages)
        self.stdout.write(self.style.SUCCESS(
            f'Hour packages: {created} created from defaults.'
        ))
