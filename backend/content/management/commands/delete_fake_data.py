from content.models import Contact, Design, Model3D, Product, Category, Item, BusinessProposal
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Delete all fake data for contacts, designs, models3d, and products'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data
    """

    def handle(self, *args, **options):
        # Delete all contacts
        for contact in Contact.objects.all():
            contact.delete()
            self.stdout.write(self.style.SUCCESS(f'Contact "{contact}" deleted'))

        # Delete all designs
        for design in Design.objects.all():
            design.delete()
            self.stdout.write(self.style.SUCCESS(f'Design "{design}" deleted'))

        # Delete all 3D models
        for model3d in Model3D.objects.all():
            model3d.delete()
            self.stdout.write(self.style.SUCCESS(f'Model3D "{model3d}" deleted'))

        # Delete all products
        for product in Product.objects.all():
            product.delete()
            self.stdout.write(self.style.SUCCESS(f'Product "{product}" deleted'))

        # Delete all categories
        for category in Category.objects.all():
            category.delete()
            self.stdout.write(self.style.SUCCESS(f'Category "{category}" deleted'))

        # Delete all items
        for item in Item.objects.all():
            item.delete()
            self.stdout.write(self.style.SUCCESS(f'Item "{item}" deleted'))

        # Delete all business proposals (CASCADE deletes sections, groups, items)
        for proposal in BusinessProposal.objects.all():
            proposal.delete()
            self.stdout.write(self.style.SUCCESS(f'BusinessProposal "{proposal}" deleted'))

        self.stdout.write(self.style.SUCCESS('All fake data has been deleted'))
