"""File historical folderless collection accounts using the live rule."""

from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Document
from content.services import accounting_service
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.generated_document_filing_service import (
    collection_account_title,
    describe_generated_folder_path,
    file_collection_account,
)


class Command(BaseCommand):
    help = (
        'Preview or apply automatic filing to collection accounts that still '
        'have no folder. Dry-run is the default.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Create folders and move eligible accounts.',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        documents = list(
            Document.objects.filter(
                document_type__code=COLLECTION_ACCOUNT,
                folder__isnull=True,
            )
            .select_related(
                'document_type',
                'project__client__profile',
                'client_user__profile',
                'collection_account',
            )
            .prefetch_related('items')
            .order_by('pk')
        )

        eligible = []
        skipped = []
        for document in documents:
            cancelled = (
                document.commercial_status == Document.CommercialStatus.CANCELLED
            )
            unissued = cancelled and not document.issue_date
            if not document.issue_date and not unissued:
                skipped.append(document)
                self.stdout.write(
                    f'SKIP #{document.pk}: sin fecha de emisión; no se inventó una fecha.'
                )
                continue
            path = describe_generated_folder_path(
                COLLECTION_ACCOUNT,
                business_date=document.issue_date,
                project=document.project,
                client_user=document.client_user,
                cancelled=cancelled,
                unissued=unissued,
            )
            desired_title = collection_account_title(document)
            eligible.append(document)
            self.stdout.write(
                f'{"APPLY" if apply_changes else "WOULD FILE"} '
                f'#{document.pk}: {path} | {desired_title}'
            )

        if apply_changes:
            with transaction.atomic():
                for document in eligible:
                    old_values = accounting_service.snapshot_values(
                        document,
                        accounting_service.EntityType.COLLECTION_ACCOUNT,
                    )
                    file_collection_account(document)
                    accounting_service.log_entity_diff(
                        accounting_service.EntityType.COLLECTION_ACCOUNT,
                        document,
                        old_values,
                        user=None,
                    )

        mode = 'aplicada' if apply_changes else 'simulada'
        self.stdout.write(self.style.SUCCESS(
            f'Pasada {mode}: {len(eligible)} elegible(s), '
            f'{len(skipped)} omitida(s), {len(documents)} revisada(s).'
        ))
