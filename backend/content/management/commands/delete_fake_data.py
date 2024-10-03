from django.core.management.base import BaseCommand
from content.models import Component, Contact, Design, Model3D, Example, UISectionCategory, Section, Product, Category, Item

class Command(BaseCommand):
    help = 'Delete all fake data for components, contacts, designs, models3d, and products'

    """
    To delete fake data via console, run:
    python3 manage.py delete_fake_data
    """

    def handle(self, *args, **options):
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

        # Delete all components
        for component in Component.objects.all():
            component.delete()
            self.stdout.write(self.style.SUCCESS(f'Component "{component}" deleted'))

        # Delete all UISectionCategories
        for category in UISectionCategory.objects.all():
            category.delete()
            self.stdout.write(self.style.SUCCESS(f'UISectionCategory "{category}" deleted'))

        # Delete all sections
        for section in Section.objects.all():
            section.delete()
            self.stdout.write(self.style.SUCCESS(f'Section "{section}" deleted'))

        # Delete all examples
        for example in Example.objects.all():
            example.delete()
            self.stdout.write(self.style.SUCCESS(f'Example "{example}" deleted'))

        # Delete all contacts
        for contact in Contact.objects.all():
            contact.delete()
            self.stdout.write(self.style.SUCCESS(f'Contact "{contact}" deleted'))

        # Delete all designs
        for design in Design.objects.all():
            design.delete()
            self.stdout.write(self.style.SUCCESS(f'Design "{design}" deleted'))

        # Delete all Model3D entries
        for model_3d in Model3D.objects.all():
            model_3d.delete()
            self.stdout.write(self.style.SUCCESS(f'Model3D "{model_3d}" deleted'))

        self.stdout.write(self.style.SUCCESS('All fake data deleted successfully'))
