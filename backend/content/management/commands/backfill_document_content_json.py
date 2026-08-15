"""Management command — rebuild ``content_json`` for markdown documents missing it.

Some documents were written by a path that saved ``content_markdown`` without
parsing it into blocks. Their PDF download answered 400 and
``standalone_email`` skipped them as attachments without saying so. The
markdown is intact, so the blocks can simply be derived again.

Idempotent and dry-run by default: pass ``--apply`` to write.
"""

from django.core.management.base import BaseCommand

from content.models import Document
from content.services.document_content import build_content_json


class Command(BaseCommand):
    help = (
        'Rebuild content_json for documents that have markdown but no parsed '
        'blocks. Dry-run unless --apply is given.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Persist the rebuilt content_json (default: dry-run).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        # El filtro fino va en Python: `blocks` vive dentro del JSONField y
        # cubrir con SQL "sin la clave", "lista vacía" y "content_json {}" a la
        # vez no compensa para una tabla de este tamaño.
        candidates = Document.objects.exclude(content_markdown='').order_by('pk')
        targets = [
            doc for doc in candidates
            if doc.content_markdown.strip() and not (doc.content_json or {}).get('blocks')
        ]

        if not targets:
            self.stdout.write(self.style.SUCCESS(
                'Nothing to do: every document with markdown already has blocks.'
            ))
            return

        for doc in targets:
            content_json = build_content_json(doc)
            if apply_changes:
                doc.content_json = content_json
                doc.save(update_fields=['content_json'])
            verb = 'rebuilt' if apply_changes else 'would rebuild'
            self.stdout.write(
                f'  #{doc.pk} "{doc.title}" — {verb} {len(content_json["blocks"])} blocks.'
            )

        summary = (
            f'{len(targets)} document(s) repaired.' if apply_changes
            else f'{len(targets)} document(s) would be repaired. '
                 'Re-run with --apply to write.'
        )
        self.stdout.write(self.style.SUCCESS(summary))
