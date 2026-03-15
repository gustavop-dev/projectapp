from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from content.models import BlogPost, BusinessProposal, Contact

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete all fake data for contacts, proposals, and blog posts'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data
    """

    def handle(self, *args, **options):
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

        # Superusers and staff users are intentionally never deleted
        protected = User.objects.filter(is_superuser=True).count() + User.objects.filter(is_staff=True).count()
        if protected:
            self.stdout.write(self.style.WARNING(
                f'Skipped {protected} superuser/staff account(s) — protected from deletion'
            ))

        self.stdout.write(self.style.SUCCESS('All fake data has been deleted'))
