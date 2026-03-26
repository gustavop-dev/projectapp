import io
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

MAX_DIMENSION = 1200
JPEG_QUALITY = 70


def optimize_image(image_file, field_name='image', max_dimension=MAX_DIMENSION, quality=JPEG_QUALITY):
    """
    Optimize an uploaded image to WhatsApp-like quality:
    - Max `max_dimension` px on the longest side
    - JPEG at given `quality`
    - Strip EXIF metadata
    - Returns an InMemoryUploadedFile ready for ImageField.save()
    """
    img = Image.open(image_file)

    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    width, height = img.size
    if width > max_dimension or height > max_dimension:
        if width >= height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        img = img.resize((new_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)

    filename = f'{uuid.uuid4().hex[:12]}.jpg'

    return InMemoryUploadedFile(
        file=buffer,
        field_name=field_name,
        name=filename,
        content_type='image/jpeg',
        size=buffer.getbuffer().nbytes,
        charset=None,
    )


def optimize_avatar(image_file):
    """Convenience wrapper for avatar optimization — 512px max, 80% quality."""
    return optimize_image(image_file, field_name='avatar', max_dimension=512, quality=80)
