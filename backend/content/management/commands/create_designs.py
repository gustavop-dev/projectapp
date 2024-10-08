from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from content.models import Design

class Command(BaseCommand):
    help = 'Create fake data for designs'

    def add_arguments(self, parser):
        parser.add_argument('number_of_records', type=int, nargs='?', default=12)

    def handle(self, *args, **options):
        number_of_records = options['number_of_records']

        # Simulate image files (this creates dummy images in memory)
        cover_image_content = ContentFile(b'fake_image_data', name='cover_image_1.png')
        detail_image_content = ContentFile(b'fake_image_data', name='detail_image_1.jpg')

        for i in range(1, number_of_records + 1):
            title_en = f'Title Design {i} EN'
            title_es = f'Title Design {i} ES'
            category_title_en = f'Category Title {i} EN'
            category_title_es = f'Category Title {i} ES'

            # Create the Design object with the simulated images
            design = Design.objects.create(
                title_en=title_en,
                title_es=title_es,
                cover_image=cover_image_content,  # Use in-memory file for cover_image
                detail_image=detail_image_content,  # Use in-memory file for detail_image
                category_title_en=category_title_en,
                category_title_es=category_title_es
            )

            self.stdout.write(self.style.SUCCESS(f'Design "{design.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_records} Design records created'))
