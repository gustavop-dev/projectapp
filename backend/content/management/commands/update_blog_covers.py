"""Management command to update existing blog posts with cover image URLs."""
from django.core.management.base import BaseCommand

from content.models import BlogPost


# Curated Unsplash image URLs related to tech/AI topics (free to use)
COVER_IMAGES = [
    'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200&q=80',  # AI chip
    'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1200&q=80',  # AI brain
    'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1200&q=80',  # Robot
    'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&q=80',  # Matrix code
    'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&q=80',  # Code screen
    'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&q=80',  # Tech globe
    'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&q=80',  # Circuit board
    'https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=1200&q=80',  # AI network
    'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&q=80',  # Cybersecurity
    'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1200&q=80',  # Laptop code
]


class Command(BaseCommand):
    help = 'Update existing blog posts that have no cover image with Unsplash URLs'

    def handle(self, *args, **options):
        posts = BlogPost.objects.filter(
            cover_image='',
            cover_image_url='',
        ).order_by('id')

        if not posts.exists():
            self.stdout.write(self.style.WARNING('All blog posts already have cover images.'))
            return

        updated = 0
        for i, post in enumerate(posts):
            url = COVER_IMAGES[i % len(COVER_IMAGES)]
            post.cover_image_url = url
            post.save(update_fields=['cover_image_url', 'updated_at'])
            updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  [{post.id}] "{post.title_es}" → {url[:60]}...'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Updated {updated} blog post(s) with cover images.'
        ))
