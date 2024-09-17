import random
from faker import Faker
from django.core.management.base import BaseCommand
from content.models import Example, Component, Section, UISectionCategory

class Command(BaseCommand):
    help = 'Create fake data for Example, Component, Section, and UISectionCategory models'

    def add_arguments(self, parser):
        parser.add_argument('number_of_records', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_records = options['number_of_records']
        fake = Faker()

        # Step 1: Create Example data
        self.stdout.write(self.style.SUCCESS('Creating fake examples...'))
        examples = []
        for i in range(1, number_of_records + 1):
            title_en = f'Title Example {i} EN'
            title_es = f'Title Example {i} ES'
            image = fake.image_url()

            example = Example.objects.create(
                title_en=title_en,
                title_es=title_es,
                image=image
            )
            examples.append(example)
            self.stdout.write(self.style.SUCCESS(f'Example "{example.title_en}" created'))

        # Step 2: Create Component data and associate examples
        self.stdout.write(self.style.SUCCESS('Creating fake components...'))
        components = []
        for i in range(1, number_of_records + 1):
            title_en = f'Title Component {i} EN'
            title_es = f'Title Component {i} ES'
            image = fake.image_url()

            component = Component.objects.create(
                title_en=title_en,
                title_es=title_es,
                image=image
            )

            # Add random examples to the component
            if examples:
                component.examples.add(*random.sample(examples, k=random.randint(1, len(examples))))

            components.append(component)
            self.stdout.write(self.style.SUCCESS(f'Component "{component.title_en}" created'))

        # Step 3: Create Section data and associate components
        self.stdout.write(self.style.SUCCESS('Creating fake sections...'))
        sections = []
        for i in range(1, number_of_records + 1):
            title_en = f'Title Section {i} EN'
            title_es = f'Title Section {i} ES'

            section = Section.objects.create(
                title_en=title_en,
                title_es=title_es
            )

            # Add random components to the section
            if components:
                section.components.add(*random.sample(components, k=random.randint(1, len(components))))

            sections.append(section)
            self.stdout.write(self.style.SUCCESS(f'Section "{section.title_en}" created'))

        # Step 4: Create UISectionCategory data and associate sections
        self.stdout.write(self.style.SUCCESS('Creating fake UISectionCategories...'))
        for i in range(1, number_of_records + 1):
            title_en = f'Title UISectionCategory {i} EN'
            title_es = f'Title UISectionCategory {i} ES'
            description_en = fake.text(max_nb_chars=500) + ' (EN)'
            description_es = fake.text(max_nb_chars=500) + ' (ES)'

            category = UISectionCategory.objects.create(
                title_en=title_en,
                title_es=title_es,
                description_en=description_en,
                description_es=description_es
            )

            # Add random sections to the category
            if sections:
                category.sections.add(*random.sample(sections, k=random.randint(1, len(sections))))

            self.stdout.write(self.style.SUCCESS(f'UISectionCategory "{category.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_records} records created for all models'))
