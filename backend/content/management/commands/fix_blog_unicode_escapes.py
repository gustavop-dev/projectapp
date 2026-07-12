"""Repair blog posts whose text fields contain literal \\uXXXX sequences.

Some MCP clients double-escaped non-ASCII characters, so rows were saved
with the escape sequences as plain text (e.g. "Caf\\u00e9" instead of
"Café"). The serializers now decode these on input; this command fixes
the rows that were written before the fix.

Dry-run by default; pass --apply to persist changes.
"""
from django.core.management.base import BaseCommand

from content.models import BlogPost
from content.serializers.blog import decode_literal_unicode_escapes

TEXT_FIELDS = (
    'title_es', 'title_en',
    'excerpt_es', 'excerpt_en',
    'content_es', 'content_en',
    'meta_title_es', 'meta_title_en',
    'meta_description_es', 'meta_description_en',
    'meta_keywords_es', 'meta_keywords_en',
    'linkedin_summary_es', 'linkedin_summary_en',
    'cover_image_credit',
)
JSON_FIELDS = ('content_json_es', 'content_json_en', 'sources')


class Command(BaseCommand):
    help = 'Decode literal \\uXXXX escape sequences stored in BlogPost text fields.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Persist the fixes (default is a dry-run report).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        fixed_posts = 0
        for post in BlogPost.objects.all():
            changed_fields = []
            for field in TEXT_FIELDS + JSON_FIELDS:
                value = getattr(post, field)
                decoded = decode_literal_unicode_escapes(value)
                if decoded != value:
                    setattr(post, field, decoded)
                    changed_fields.append(field)
            if not changed_fields:
                continue
            fixed_posts += 1
            label = 'FIXED' if apply_changes else 'WOULD FIX'
            self.stdout.write(f'{label} post {post.id} ({post.slug}): {", ".join(changed_fields)}')
            if apply_changes:
                post.save(update_fields=changed_fields + ['updated_at'])
        mode = 'applied' if apply_changes else 'dry-run (use --apply to persist)'
        self.stdout.write(self.style.SUCCESS(f'{fixed_posts} post(s) affected — {mode}'))
