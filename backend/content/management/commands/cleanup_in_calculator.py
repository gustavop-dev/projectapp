"""
One-off management command to:
1. Remove the deprecated 'in_calculator' key from all FR section JSON data
2. Normalize: move any group with is_calculator_module=True to additionalModules[]

Usage:
    python manage.py cleanup_in_calculator          # dry-run
    python manage.py cleanup_in_calculator --apply   # actually update
"""
from django.core.management.base import BaseCommand

from content.models import ProposalSection


class Command(BaseCommand):
    help = 'Remove in_calculator flag and normalize groups/additionalModules'

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
            changed = False

            # 1. Strip in_calculator from groups and additionalModules
            for arr_key in ('groups', 'additionalModules'):
                for item in cj.get(arr_key, []):
                    if 'in_calculator' in item:
                        self.stdout.write(
                            f"  Proposal {section.proposal_id} | "
                            f"{arr_key} '{item.get('id', '?')}': "
                            f"removing in_calculator={item['in_calculator']}"
                        )
                        del item['in_calculator']
                        changed = True

            # 2. Move is_calculator_module groups to additionalModules
            groups = cj.get('groups', [])
            additional = cj.get('additionalModules', [])
            existing_ids = {m.get('id') for m in additional}
            final_groups = []
            for g in groups:
                if g.get('is_calculator_module'):
                    if g.get('id') not in existing_ids:
                        self.stdout.write(
                            f"  Proposal {section.proposal_id} | "
                            f"moving '{g.get('id', '?')}' from groups -> additionalModules"
                        )
                        additional.append(g)
                        changed = True
                    else:
                        self.stdout.write(
                            f"  Proposal {section.proposal_id} | "
                            f"removing duplicate '{g.get('id', '?')}' from groups "
                            f"(already in additionalModules)"
                        )
                        changed = True
                else:
                    final_groups.append(g)

            if changed:
                cj['groups'] = final_groups
                cj['additionalModules'] = additional
                updated_count += 1
                if apply:
                    section.content_json = cj
                    section.save(update_fields=['content_json'])

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(
            f'[{mode}] {updated_count} section(s) '
            f'{"updated" if apply else "would be updated"}.'
        ))
