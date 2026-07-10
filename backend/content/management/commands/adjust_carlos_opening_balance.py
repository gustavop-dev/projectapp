"""One-off adjustment: leave Carlos's partner net at half the pocket balance.

Registers a personal-ledger expense for Carlos ("Ajuste de cuentas para
coherencia e inicio módulo contable") so his net equals pocket_balance / 2.
All figures are read live from the dashboard at execution time.

Usage:
    python manage.py adjust_carlos_opening_balance --dry-run   # preview
    python manage.py adjust_carlos_opening_balance             # apply

Idempotent: aborts if an expense with the source_ref already exists.
Goes through the write serializer + accounting_service.create_record so
the personal-ledger validation, audit log and partner notification email
apply exactly as a panel-created expense.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from content.models import AccountingChangeLog, ExpenseRecord
from content.serializers.accounting import (
    TWO_PLACES,
    ExpenseRecordCreateUpdateSerializer,
)
from content.services import accounting_service
from content.utils import today_bogota

CONCEPT = 'Ajuste de cuentas para coherencia e inicio módulo contable'
DEFAULT_SOURCE_REF = 'adjust:carlos-inicio-modulo-2026'


class Command(BaseCommand):
    help = "Register Carlos's opening-balance adjustment expense (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--source-ref', default=DEFAULT_SOURCE_REF)

    def handle(self, *args, **options):
        source_ref = options['source_ref']
        today = today_bogota()

        if ExpenseRecord.objects.filter(source_ref=source_ref).exists():
            raise CommandError(
                f'Ya existe un gasto con source_ref={source_ref!r}; '
                'el ajuste no se aplica dos veces.'
            )

        summary = accounting_service.dashboard_summary(today.year)
        carlos_net = Decimal(summary['partners']['carlos']['net'])
        pocket = Decimal(summary['pocket_balance'])
        target = (pocket / 2).quantize(TWO_PLACES)
        adjustment = (carlos_net - target).quantize(TWO_PLACES)

        self.stdout.write(f'Neto actual Carlos:  {carlos_net}')
        self.stdout.write(f'Bolsillo:            {pocket}')
        self.stdout.write(f'Objetivo (mitad):    {target}')
        self.stdout.write(f'Gasto de ajuste:     {adjustment}')

        if adjustment <= 0:
            raise CommandError(
                'El neto de Carlos ya es menor o igual al objetivo; '
                'un gasto de ajuste no aplica.'
            )

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: no se escribió nada.'))
            return

        serializer = ExpenseRecordCreateUpdateSerializer(data={
            'concept': CONCEPT,
            'period_date': f'{today.year}-{today.month:02d}',
            'category': ExpenseRecord.Category.PERSONAL,
            'ledger': 'carlos',
            'total_amount': str(adjustment),
            'carlos_amount': str(adjustment),
            'gustavo_amount': '0',
            'notes': (
                'Ajuste automático: deja el neto de Carlos en la mitad del '
                'bolsillo/valor líquido al inicio del módulo contable.'
            ),
        })
        serializer.is_valid(raise_exception=True)
        instance = accounting_service.create_record(
            AccountingChangeLog.EntityType.EXPENSE, serializer, user=None,
        )
        # source_ref is not part of the write serializer; stamp it directly.
        ExpenseRecord.objects.filter(pk=instance.pk).update(source_ref=source_ref)

        new_summary = accounting_service.dashboard_summary(today.year)
        new_net = Decimal(new_summary['partners']['carlos']['net'])
        self.stdout.write(
            f'Gasto #{instance.pk} creado. Nuevo neto Carlos: {new_net}'
        )
        if new_net != target:
            self.stdout.write(self.style.WARNING(
                f'Aviso: el nuevo neto ({new_net}) difiere del objetivo '
                f'({target}); revisa movimientos concurrentes.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Neto de Carlos == mitad del bolsillo.'))
