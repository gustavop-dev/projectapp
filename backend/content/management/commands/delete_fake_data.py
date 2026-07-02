from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import HostingSubscription, Payment, PaymentHistory, Project
from content.models import (
    BlogPost,
    BusinessProposal,
    Contact,
    Document,
    DocumentFolder,
    DocumentTag,
    PortfolioWork,
    Task,
    WebAppDiagnostic,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Delete fake content data across features (contacts, proposals, blog, portfolio, '
        'tasks, diagnostics, commercial documents). Superusers, staff and catalog/config '
        'rows (DocumentType, IssuerProfile) are preserved.'
    )

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data --confirm
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all fake data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'This will delete ALL contacts, proposals, blog posts, portfolio works, '
                'tasks, diagnostics and commercial documents.\n'
                'Run with --confirm to proceed: python manage.py delete_fake_data --confirm'
            ))
            return

        # Order matters because of PROTECT chains:
        #   Payment ─PROTECT→ HostingSubscription ─PROTECT→ Project
        #   ProjectPhase ─PROTECT→ BusinessProposal
        # So: payments → subscriptions → projects (cascades the platform graph:
        # phases, requirements, deliverables, change requests, bugs) → proposals.
        for model, label in (
            (Contact, 'contacts'),
            (PaymentHistory, 'payment history'),
            (Payment, 'payments'),
            (HostingSubscription, 'hosting subscriptions'),
            (Project, 'projects (+ platform graph)'),
            (BusinessProposal, 'business proposals'),
            (BlogPost, 'blog posts'),
            (PortfolioWork, 'portfolio works'),
            (Task, 'tasks'),
            (WebAppDiagnostic, 'diagnostics'),
        ):
            deleted, _ = model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {label} ({deleted} rows)'))

        # Documents cascade to items, collection account, payment methods.
        deleted, _ = Document.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted documents ({deleted} rows)'))

        # Tags are independent (M2M cleared with documents already).
        deleted, _ = DocumentTag.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted document tags ({deleted} rows)'))

        # Folders use a PROTECT self-FK: delete leaves first, repeat until a pass
        # deletes nothing (empty, or a cycle we can't break).
        total_folders = 0
        while True:
            count, _ = DocumentFolder.objects.filter(children__isnull=True).delete()
            if not count:
                break
            total_folders += count
        self.stdout.write(self.style.SUCCESS(f'Deleted document folders ({total_folders} rows)'))

        # Accounting: only rows tagged fake:accounting are removed (imported
        # spreadsheet data and manual records are preserved). Unlink pocket
        # references first so OneToOne SET_NULL ordering never matters.
        from content.models import (
            AdsSpendRecord as AccAds,
            CardBalanceSnapshot as AccCards,
            ExpenseRecord as AccExpenses,
            HostingRecord as AccHostings,
            IncomeRecord as AccIncomes,
            PocketMovement as AccPocket,
            RecurringPayment as AccRecurring,
        )
        accounting_total = 0
        for model in (
            AccIncomes, AccExpenses, AccHostings,
            AccPocket, AccRecurring, AccAds, AccCards,
        ):
            deleted, _ = model.objects.filter(
                source_ref='fake:accounting',
            ).delete()
            accounting_total += deleted
        self.stdout.write(self.style.SUCCESS(
            f'Deleted fake accounting rows ({accounting_total} rows)'
        ))

        # Superusers and staff users are intentionally never deleted.
        protected = User.objects.filter(is_superuser=True).count() \
            + User.objects.filter(is_staff=True, is_superuser=False).count()
        if protected:
            self.stdout.write(self.style.WARNING(
                f'Skipped {protected} superuser/staff account(s) — protected from deletion'
            ))

        self.stdout.write(self.style.SUCCESS(
            'Fake content data deleted. DocumentType / IssuerProfile catalogs preserved.'
        ))
