"""Management command — create a markdown Document inside a panel folder.

Used by the ``requirement-calculator`` skill to persist estimation results
as real documents visible under ``/panel/documents``. The target folder is
resolved with ``get_or_create`` so re-runs reuse the same top-level folder.
"""

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from content.models import Document, DocumentFolder, DocumentType
from content.services.document_type_codes import MARKDOWN

User = get_user_model()

DEFAULT_FOLDER = 'Requirement Estimates'


class Command(BaseCommand):
    help = (
        'Create a markdown Document from a file inside a top-level folder '
        f'(default: "{DEFAULT_FOLDER}"). The folder is created once and reused.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--title', required=True, help='Document title.')
        parser.add_argument(
            '--file', required=True,
            help='Path to the markdown file with the document content.',
        )
        parser.add_argument(
            '--folder', default=DEFAULT_FOLDER,
            help=f'Top-level folder name (default: "{DEFAULT_FOLDER}").',
        )
        parser.add_argument(
            '--status', default=Document.Status.PUBLISHED,
            choices=[choice for choice, _ in Document.Status.choices],
            help='Document status (default: published).',
        )
        parser.add_argument(
            '--language', default=Document.Language.ES,
            choices=[choice for choice, _ in Document.Language.choices],
            help='Document language (default: es).',
        )
        parser.add_argument(
            '--on-conflict', default='version', choices=['version', 'replace', 'new'],
            help=(
                'Same title in folder: version = append " — vN"; '
                'replace = update the newest match; new = allow duplicate.'
            ),
        )

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.is_file():
            raise CommandError(f'Markdown file not found: {path}')
        content = path.read_text(encoding='utf-8')
        if not content.strip():
            raise CommandError(f'Markdown file is empty: {path}')

        folder, folder_created = DocumentFolder.objects.get_or_create(
            name=options['folder'], parent=None,
        )
        doc_type, _ = DocumentType.objects.get_or_create(
            code=MARKDOWN, defaults={'name': 'Documento markdown'},
        )
        admin = User.objects.filter(is_staff=True).order_by('pk').first()

        title = options['title']
        existing = Document.objects.filter(folder=folder, title=title)
        if existing.exists():
            if options['on_conflict'] == 'replace':
                document = existing.latest('created_at')
                document.content_markdown = content
                document.status = options['status']
                document.updated_by = admin
                document.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Document #{document.pk} "{document.title}" updated (replaced).'
                ))
                self.stdout.write(f'Panel URL: /panel/documents/{document.pk}/edit')
                return
            if options['on_conflict'] == 'version':
                title = f'{title} — v{existing.count() + 1}'

        document = Document.objects.create(
            document_type=doc_type,
            folder=folder,
            title=title,
            status=options['status'],
            content_markdown=content,
            language=options['language'],
            created_by=admin,
            updated_by=admin,
        )

        suffix = ' (folder created)' if folder_created else ''
        self.stdout.write(self.style.SUCCESS(
            f'Document #{document.pk} "{document.title}" created in '
            f'folder "{folder.name}"{suffix}.'
        ))
        self.stdout.write(f'Panel URL: /panel/documents/{document.pk}/edit')
