from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create fake data for contacts, designs, and models3d'

    def add_arguments(self, parser):
        parser.add_argument('number', type=int, help='Number of records to create')

    def handle(self, *args, **options):
        number_of_records = options['number']

        # Create fake data for contacts
        self.stdout.write(self.style.SUCCESS('Creating fake contacts...'))
        call_command('create_contacts', number_of_records)

        # Create fake data for designs
        self.stdout.write(self.style.SUCCESS('Creating fake designs...'))
        call_command('create_designs', number_of_records)

        # Create fake data for 3D models
        self.stdout.write(self.style.SUCCESS('Creating fake 3D models...'))
        call_command('create_model3ds', number_of_records)

        # Create fake data for products
        self.stdout.write(self.style.SUCCESS('Creating fake products...'))
        call_command('create_products', number_of_records)

        # Create fake data for business proposals
        self.stdout.write(self.style.SUCCESS('Creating fake business proposals...'))
        call_command('create_fake_proposals')

        self.stdout.write(self.style.SUCCESS('All fake data has been created'))
