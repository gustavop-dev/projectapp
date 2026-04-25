"""Manually trigger publication for a single scheduled blog post.

Usage:
    python manage.py publish_blog_post --id 54           # respects guards (skips if not yet time)
    python manage.py publish_blog_post --id 54 --force   # backdate published_at to now and publish
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from content.models import BlogPost
from content.tasks import publish_single_scheduled_blog


class Command(BaseCommand):
    help = 'Force publication (site + LinkedIn) for a single blog post.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            required=True,
            help='Primary key of the BlogPost to publish.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Set published_at=now() before publishing to bypass the future-time guard.',
        )

    def handle(self, *args, **options):
        post_id = options['id']
        force = options['force']

        post = BlogPost.objects.filter(pk=post_id).first()
        if not post:
            raise CommandError(f'BlogPost id={post_id} no existe.')

        if force and (not post.published_at or post.published_at > timezone.now()):
            post.published_at = timezone.now()
            post.save(update_fields=['published_at'])
            self.stdout.write(
                self.style.WARNING(
                    f'--force: published_at backdated to {post.published_at} for post {post_id}.'
                )
            )

        publish_single_scheduled_blog.call_local(post_id)
        post.refresh_from_db()

        if post.is_published:
            li = post.linkedin_post_id or '-'
            self.stdout.write(
                self.style.SUCCESS(
                    f'Post {post_id} ({post.slug}) publicado. linkedin_post_id={li}'
                )
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    f'Post {post_id} no fue publicado (revisa logs; usa --force si published_at está en el futuro).'
                )
            )
