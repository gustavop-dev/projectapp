from django.core.management.base import BaseCommand

from faker import Faker

from content.fake_data import add_seed_arguments, ensure_fake_data_allowed, seed_context
from content.models import Contact


class Command(BaseCommand):
    help = 'Create Contact records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_contacts', type=int, nargs='?', default=10)
        add_seed_arguments(parser)

    def handle(self, *args, **options):
        ensure_fake_data_allowed('create_contacts')
        number_of_contacts = options['number_of_contacts']
        fake = Faker()
        fake.seed_instance(seed_context(options, 'contacts').module_seed)

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
