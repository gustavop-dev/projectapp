import random
from faker import Faker
from django.core.management.base import BaseCommand
from content.models import Model3D

class Command(BaseCommand):
    help = 'Create Model3D records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_models3d', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_models3d = options['number_of_models3d']
        fake = Faker()

        # List of test images and 3D files for models
        test_images = [
            'media/temp/models3d/image_temp1.jpg',
            'media/temp/models3d/image_temp2.jpg',
            'media/temp/models3d/image_temp3.jpg',
            'media/temp/models3d/image_temp4.jpg',
        ]

        test_files = [
            'media/temp/models3d/file_temp1.obj',
            'media/temp/models3d/file_temp2.obj',
            'media/temp/models3d/file_temp3.obj',
            'media/temp/models3d/file_temp4.obj',
        ]

        for i in range(1, number_of_models3d + 1):
            title_en = f'Title Model3D {i} EN'
            title_es = f'Title Model3D {i} ES'

            # Random image and file selection
            image = random.choice(test_images)
            file = random.choice(test_files)

            # Create a new Model3D
            model_3d = Model3D.objects.create(
                title_en=title_en,
                title_es=title_es,
                image=image,
                file=file
            )

            self.stdout.write(self.style.SUCCESS(f'Model3D "{model_3d.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_models3d} Model3D records created'))
