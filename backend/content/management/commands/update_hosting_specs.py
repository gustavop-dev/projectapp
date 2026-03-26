"""
Management command to update hosting specs in all existing investment sections.

Updates vCPU, RAM, Storage, and Bandwidth to new default values:
  - vCPU: 4 cores
  - RAM: 8 GB
  - Storage: 100 GB NVMe
  - Bandwidth: 4 TB

Detects language by inspecting the current spec value to avoid cross-language overwrites.
"""

from django.core.management.base import BaseCommand
from content.models.proposal_section import ProposalSection


# Maps old value → new value (exact match to preserve language)
VALUE_MAP = {
    # Spanish
    '1 núcleo de vCPU': '4 núcleos de vCPU',
    '1 GB de RAM dedicada': '8 GB de RAM dedicada',
    '2 GB de almacenamiento NVMe': '100 GB de almacenamiento NVMe',
    '600 GB mensual': '4 TB mensual',
    # English
    '1 vCPU core': '4 vCPU cores',
    '1 GB dedicated RAM': '8 GB dedicated RAM',
    '2 GB NVMe storage': '100 GB NVMe storage',
    '600 GB monthly': '4 TB monthly',
}


class Command(BaseCommand):
    help = 'Update hosting specs (vCPU, RAM, Storage, Bandwidth) in all existing investment sections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sections = ProposalSection.objects.filter(section_type='investment')
        updated = 0
        skipped = 0

        for section in sections:
            cj = section.content_json or {}
            hosting = cj.get('hostingPlan') or {}
            specs = hosting.get('specs') or []

            changed = False
            for spec in specs:
                old_value = spec.get('value', '')
                if old_value in VALUE_MAP:
                    new_value = VALUE_MAP[old_value]
                    if dry_run:
                        self.stdout.write(
                            f'  [DRY RUN] Section {section.id} '
                            f'(proposal: {section.proposal_id}): '
                            f'{spec["label"]}: "{old_value}" → "{new_value}"'
                        )
                    spec['value'] = new_value
                    changed = True

            if changed:
                if not dry_run:
                    section.save(update_fields=['content_json'])
                updated += 1
            else:
                skipped += 1

        verb = 'Would update' if dry_run else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{verb} {updated} investment section(s). '
                f'{skipped} already had current values or no hosting specs.'
            )
        )
