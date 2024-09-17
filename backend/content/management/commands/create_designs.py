import random
from faker import Faker
from django.core.management.base import BaseCommand
from content.models import Design

class Command(BaseCommand):
    help = 'Create Design records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_designs', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_designs = options['number_of_designs']
        fake = Faker()

        # List of test images for designs
        test_images = [
            'media/temp/designs/cover_temp1.jpg',
            'media/temp/designs/cover_temp2.jpg',
            'media/temp/designs/cover_temp3.jpg',
            'media/temp/designs/cover_temp4.jpg',
        ]

        for i in range(1, number_of_designs + 1):
            title_en = f'Title Design {i} EN'
            title_es = f'Title Design {i} ES'
            category_title_en = f'Category Title {i} EN'
            category_title_es = f'Category Title {i} ES'

            # Random image selection
            cover_image = random.choice(test_images)
            detail_image = random.choice(test_images)

            # Create a new design
            design = Design.objects.create(
                title_en=title_en,
                title_es=title_es,
                cover_image=cover_image,
                detail_image=detail_image,
                category_title_en=category_title_en,
                category_title_es=category_title_es
            )

            self.stdout.write(self.style.SUCCESS(f'Design "{design.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_designs} Design records created'))
