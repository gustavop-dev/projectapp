import io
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

MAX_DIMENSION = 1200
JPEG_QUALITY = 70


def optimize_avatar(image_file):
    """
    Optimize an uploaded image to WhatsApp-like quality:
    - Max 1200px on the longest side
    - JPEG at quality 70
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
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        if width >= height:
            new_width = MAX_DIMENSION
            new_height = int(height * (MAX_DIMENSION / width))
        else:
            new_height = MAX_DIMENSION
            new_width = int(width * (MAX_DIMENSION / height))
        img = img.resize((new_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    buffer.seek(0)

    filename = f'{uuid.uuid4().hex[:12]}.jpg'

    return InMemoryUploadedFile(
        file=buffer,
        field_name='avatar',
        name=filename,
        content_type='image/jpeg',
        size=buffer.getbuffer().nbytes,
        charset=None,
    )
