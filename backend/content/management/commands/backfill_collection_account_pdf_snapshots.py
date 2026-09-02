"""Archive immutable PDFs for collection accounts created before PA-109 parity."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.models import Document
from content.services.collection_account_snapshot_service import (
    EMAIL_HISTORY_SOURCE,
    LEGACY_RECONSTRUCTION_SOURCE,
    CollectionAccountSnapshotError,
    discard_stored_collection_account_pdf,
    first_email_snapshot_pdf,
    persist_collection_account_pdf,
    render_collection_account_pdf,
)
from content.services.document_type_codes import COLLECTION_ACCOUNT


class Command(BaseCommand):
    help = (
        'Archive immutable PDFs for issued historical collection accounts. '
        'Dry-run by default; pass --apply to persist files.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Persist generated_file and provenance metadata.',
        )
        parser.add_argument(
            '--document-id', type=int,
            help='Limit the operation to one Document id.',
        )
        parser.add_argument(
            '--limit', type=int,
            help='Process at most this many eligible accounts.',
        )

    def handle(self, *args, **options):
        queryset = (
            Document.objects.filter(
                document_type__code=COLLECTION_ACCOUNT,
                generated_file='',
                public_number__gt='',
                issue_date__isnull=False,
                commercial_status__in=(
                    Document.CommercialStatus.ISSUED,
                    Document.CommercialStatus.PAID,
                    Document.CommercialStatus.CANCELLED,
                ),
            )
            .select_related('collection_account')
            .prefetch_related('items', 'payment_methods')
            .order_by('pk')
        )
        if options.get('document_id'):
            queryset = queryset.filter(pk=options['document_id'])
        if options.get('limit'):
            if options['limit'] < 1:
                raise CommandError('--limit debe ser mayor que cero.')
            queryset = queryset[:options['limit']]

        apply_changes = options['apply']
        totals = {'eligible': 0, 'email_history': 0, 'reconstructed': 0, 'failed': 0}

        for document in queryset.iterator(chunk_size=100):
            totals['eligible'] += 1
            stored = None
            try:
                historical_pdf = first_email_snapshot_pdf(document)
                if historical_pdf is not None:
                    pdf_bytes = historical_pdf
                    source = EMAIL_HISTORY_SOURCE
                    totals['email_history'] += 1
                else:
                    pdf_bytes = render_collection_account_pdf(document)
                    source = LEGACY_RECONSTRUCTION_SOURCE
                    totals['reconstructed'] += 1

                if apply_changes:
                    try:
                        with transaction.atomic():
                            locked = (
                                Document.objects.select_for_update()
                                .select_related('collection_account')
                                .prefetch_related('items', 'payment_methods')
                                .get(pk=document.pk)
                            )
                            if locked.generated_file:
                                continue
                            stored = persist_collection_account_pdf(
                                locked, pdf_bytes=pdf_bytes, source=source,
                            )
                    except Exception:
                        discard_stored_collection_account_pdf(stored)
                        raise
                self.stdout.write(
                    f'#{document.pk} {document.public_number}: {source}'
                )
            except (CollectionAccountSnapshotError, OSError, ValueError) as exc:
                totals['failed'] += 1
                self.stderr.write(
                    self.style.ERROR(f'#{document.pk}: {exc}')
                )

        verb = 'applied' if apply_changes else 'dry-run'
        self.stdout.write(self.style.SUCCESS(
            f'{verb}: eligible={totals["eligible"]} '
            f'email_history={totals["email_history"]} '
            f'reconstructed={totals["reconstructed"]} '
            f'failed={totals["failed"]}'
        ))
        if totals['failed']:
            raise CommandError(
                'Algunas cuentas no pudieron archivarse; revisa los errores.',
            )
