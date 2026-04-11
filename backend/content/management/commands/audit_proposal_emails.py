"""Audit active proposals for invalid email domains (no MX/A records).

Usage:
    python manage.py audit_proposal_emails          # dry-run report
    python manage.py audit_proposal_emails --fix    # pause automations for bad domains
"""

from collections import defaultdict

from django.core.management.base import BaseCommand

from content.models import BusinessProposal
from content.utils import check_domain_mx


class Command(BaseCommand):
    help = 'Audit active proposals for client emails with invalid domains.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Set automations_paused=True on proposals with invalid email domains.',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        proposals = (
            BusinessProposal.objects
            .filter(is_active=True, automations_paused=False)
            .exclude(client_email='')
        )

        # Group by domain to minimize DNS lookups
        by_domain = defaultdict(list)
        for p in proposals:
            domain = p.client_email.rsplit('@', 1)[-1].lower().strip()
            by_domain[domain].append(p)

        invalid_domains = {}
        valid_count = 0

        for domain, props in sorted(by_domain.items()):
            ok = check_domain_mx(domain)
            if ok:
                valid_count += len(props)
            else:
                invalid_domains[domain] = props

        self.stdout.write(f'\nDomains checked: {len(by_domain)}')
        self.stdout.write(f'Valid domains:   {valid_count} proposals across {len(by_domain) - len(invalid_domains)} domains')
        self.stdout.write(f'Invalid domains: {sum(len(p) for p in invalid_domains.values())} proposals across {len(invalid_domains)} domains\n')

        if not invalid_domains:
            self.stdout.write(self.style.SUCCESS('All email domains are valid.'))
            return

        for domain, props in sorted(invalid_domains.items(), key=lambda x: -len(x[1])):
            self.stdout.write(self.style.WARNING(
                f'  @{domain} — {len(props)} proposal(s):'
            ))
            for p in props:
                self.stdout.write(f'    - [{p.status}] {p.client_name} <{p.client_email}> (id={p.id})')

        if fix:
            ids = [p.id for props in invalid_domains.values() for p in props]
            updated = BusinessProposal.objects.filter(id__in=ids).update(automations_paused=True)
            self.stdout.write(self.style.SUCCESS(
                f'\nPaused automations on {updated} proposal(s).'
            ))
        else:
            self.stdout.write(self.style.NOTICE(
                '\nDry-run mode. Use --fix to pause automations on these proposals.'
            ))
