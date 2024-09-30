import os
import random
from faker import Faker
from django.core.files import File
from django.core.management.base import BaseCommand
from content.models import Model3D
from django.conf import settings

class Command(BaseCommand):
    help = 'Create Model3D records in the database'

    def add_arguments(self, parser):
        parser.add_argument('number_of_models3d', type=int, nargs='?', default=10)

    def handle(self, *args, **options):
        number_of_models3d = options['number_of_models3d']
        fake = Faker()

        # Define the path for the image and the 3D model file
        media_path = os.path.join(settings.MEDIA_ROOT, 'temp/model_3d')

        # Paths for the files in your media/temp directory
        image_path = os.path.join(media_path, '3d_picture_1.png')
        model_file_path = os.path.join(media_path, 'scene_1.splinecode')

        if not os.path.exists(image_path) or not os.path.exists(model_file_path):
            self.stdout.write(self.style.ERROR(f'Files not found in {media_path}'))
            return

        for i in range(1, number_of_models3d + 1):
            title_en = f'Title Model3D {i} EN'
            title_es = f'Title Model3D {i} ES'

            # Open the image and 3D model file
            with open(image_path, 'rb') as image_file, open(model_file_path, 'rb') as model_file:
                # Create a new Model3D record with actual files from disk
                model_3d = Model3D.objects.create(
                    title_en=title_en,
                    title_es=title_es,
                    image=File(image_file, name=f'3d_picture_{i}.png'),  # Use actual image file
                    file=File(model_file, name=f'scene_{i}.splinecode')  # Use actual 3D model file
                )

                self.stdout.write(self.style.SUCCESS(f'Model3D "{model_3d.title_en}" created'))

        self.stdout.write(self.style.SUCCESS(f'{number_of_models3d} Model3D records created'))
