from faker import Faker
from django.core.management.base import BaseCommand
from content.models import Contact

class Command(BaseCommand):
    help = 'Create Contact records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_contacts', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_contacts = options['number_of_contacts']
        fake = Faker()

        for _ in range(number_of_contacts):
            email = fake.email()
            subject = fake.sentence(nb_words=6).rstrip('.')
            message = fake.text(max_nb_chars=500)

            # Create a new contact
            contact = Contact.objects.create(
                email=email,
                subject=subject,
                message=message
            )

            self.stdout.write(self.style.SUCCESS(f'Contact with subject "{contact.subject}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_contacts} Contact records created'))
