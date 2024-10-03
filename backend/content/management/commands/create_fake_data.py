from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create fake data for components, contacts, designs, and models3d'

    def add_arguments(self, parser):
        parser.add_argument('number_of_records', type=int, nargs='?', default=12)

    def handle(self, *args, **options):
        number_of_records = options['number_of_records']

        # Create fake data for components
        self.stdout.write(self.style.SUCCESS('Creating fake components...'))
        call_command('create_components', number_of_records)

        # Create fake data for contacts
        self.stdout.write(self.style.SUCCESS('Creating fake contacts...'))
        call_command('create_contacts', number_of_records)

        # Create fake data for designs
        self.stdout.write(self.style.SUCCESS('Creating fake designs...'))
        call_command('create_designs', number_of_records)

        # Create fake data for 3D models
        self.stdout.write(self.style.SUCCESS('Creating fake 3D models...'))
        call_command('create_models_3d', number_of_records)

        # Create fake data for products, categories, and items
        self.stdout.write(self.style.SUCCESS('Creating fake products, categories, and items...'))
        call_command('create_products', number_of_records)

        self.stdout.write(self.style.SUCCESS('All fake data created successfully'))
