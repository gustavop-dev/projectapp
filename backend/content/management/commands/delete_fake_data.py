from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from content.models import BlogPost, BusinessProposal, Contact, Document, DocumentFolder

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete all fake data for contacts, proposals, blog posts, documents and folders'

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
                'This will delete ALL contacts, proposals, blog posts, documents, and folders.\n'
                'Run with --confirm to proceed: python manage.py delete_fake_data --confirm'
            ))
            return

        # Delete all contacts
        for contact in Contact.objects.all():
            contact.delete()
            self.stdout.write(self.style.SUCCESS(f'Contact "{contact}" deleted'))

        # Delete all business proposals (CASCADE deletes sections, groups, items)
        for proposal in BusinessProposal.objects.all():
            proposal.delete()
            self.stdout.write(self.style.SUCCESS(f'BusinessProposal "{proposal}" deleted'))

        # Delete all blog posts
        for post in BlogPost.objects.all():
            post.delete()
            self.stdout.write(self.style.SUCCESS(f'BlogPost "{post}" deleted'))

        # Delete all documents first (folders have PROTECT for documents via
        # SET_NULL — clearing them first means subsequent folder deletion is
        # unambiguous about cause when something goes wrong).
        doc_count = Document.objects.count()
        Document.objects.all().delete()
        if doc_count:
            self.stdout.write(self.style.SUCCESS(f'{doc_count} document(s) deleted'))

        # Delete folders. `parent` is PROTECT, so blank out the FK first to
        # avoid ProtectedError; then a single bulk delete clears the table.
        folder_count = DocumentFolder.objects.count()
        DocumentFolder.objects.all().update(parent=None)
        DocumentFolder.objects.all().delete()
        if folder_count:
            self.stdout.write(self.style.SUCCESS(f'{folder_count} document folder(s) deleted'))

        # Superusers and staff users are intentionally never deleted
        protected = User.objects.filter(is_superuser=True).count() + User.objects.filter(is_staff=True).count()
        if protected:
            self.stdout.write(self.style.WARNING(
                f'Skipped {protected} superuser/staff account(s) — protected from deletion'
            ))

        self.stdout.write(self.style.SUCCESS('All fake data has been deleted'))
