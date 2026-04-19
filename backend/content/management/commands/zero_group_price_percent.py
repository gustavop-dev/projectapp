"""
One-off management command to set price_percent=0 for the 6 standard
functional-requirements groups on all existing proposals.

Usage:
    python manage.py zero_group_price_percent          # dry-run
    python manage.py zero_group_price_percent --apply   # actually update
"""
from django.core.management.base import BaseCommand

from content.models import ProposalSection

STANDARD_GROUP_IDS = {'views', 'components', 'features', 'admin_module',
                      'analytics_dashboard', 'kpi_dashboard_module', 'manual_module'}


class Command(BaseCommand):
    help = 'Set price_percent to 0 for standard FR groups on existing proposals'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Actually write changes (default is dry-run)')

    def handle(self, *args, **options):
        apply = options['apply']
        sections = ProposalSection.objects.filter(
            section_type='functional_requirements',
        )
        updated_count = 0

        for section in sections:
            cj = section.content_json or {}
            groups = cj.get('groups', [])
            changed = False

            for group in groups:
                if group.get('id') in STANDARD_GROUP_IDS and group.get('price_percent', 0) != 0:
                    self.stdout.write(
                        f"  Proposal {section.proposal_id} | "
                        f"group '{group['id']}': {group['price_percent']} -> 0"
                    )
                    group['price_percent'] = 0
                    changed = True

            if changed:
                updated_count += 1
                if apply:
                    section.content_json = cj
                    section.save(update_fields=['content_json'])

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(
            f'[{mode}] {updated_count} section(s) {"updated" if apply else "would be updated"}.'
        ))
