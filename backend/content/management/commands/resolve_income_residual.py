"""Close the pending residual of an expected income as a deduction expense.

Partial collections registered before the settlement flow existed left
fee-sized residuals that will never arrive — a Wompi gateway fee, a bank fee
or a withholding discounted before the transfer landed. This books that
residual as a deduction through the settlement service with zero received,
which shrinks the expected record so its derived payment status reads paid.

Usage:
    python manage.py resolve_income_residual --income-id 134            # preview
    python manage.py resolve_income_residual --income-id 134 --apply    # write

DRY-RUN BY DEFAULT (unlike older one-off commands that took --dry-run):
nothing is written until --apply is passed. Idempotent: once settled the
pending balance is zero and a re-run is a no-op.

Goes through IncomeSettlementSerializer + settle_expected_income, so the
deduction inherits every settlement guarantee: proportional partner split,
register_in_pocket=False, exclusion from utility, audit log and the
income:<pk>:settlement source_ref.
"""
from django.core.management.base import BaseCommand, CommandError

from content.models import ExpenseRecord, IncomeRecord
from content.serializers.accounting import IncomeSettlementSerializer
from content.services import accounting_settlement_service


class Command(BaseCommand):
    help = (
        'Book the pending residual of an expected income as a deduction '
        'expense (zero received). Dry-run by default; pass --apply to write.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--income-id', type=int, required=True,
            help='Primary key of the expected IncomeRecord to close.',
        )
        parser.add_argument(
            '--type',
            default=ExpenseRecord.DeductionType.GATEWAY_FEE,
            choices=[value for value, _ in ExpenseRecord.DeductionType.choices],
            help='Deduction concept for the residual (default: gateway_fee).',
        )
        parser.add_argument(
            '--detail', default='',
            help='Free-text concept, required when --type is "other".',
        )
        parser.add_argument(
            '--period', default='',
            help='YYYY-MM month for the expense (default: the income month).',
        )
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        income = IncomeRecord.objects.filter(pk=options['income_id']).first()
        if income is None:
            raise CommandError(f"No existe el ingreso #{options['income_id']}.")
        if income.kind != IncomeRecord.Kind.EXPECTED:
            raise CommandError(
                'Solo un ingreso esperado tiene saldo pendiente por resolver.'
            )

        paid = accounting_settlement_service._paid_total(income)
        pending = income.total_amount - paid
        if pending <= 0:
            self.stdout.write(self.style.SUCCESS(
                f'Ingreso #{income.pk} sin saldo pendiente; nada que resolver.'
            ))
            return

        period = options['period'] or f'{income.period_date:%Y-%m}'
        label = ExpenseRecord.DeductionType(options['type']).label
        # `concept` is required by the settlement serializer even though a
        # zero-received settlement never creates the liquid child that uses it.
        serializer = IncomeSettlementSerializer(data={
            'concept': income.concept,
            'period_date': period,
            'total_amount': '0',
            'deductions': [{
                'type': options['type'],
                'detail': options['detail'],
                'amount': str(pending),
            }],
            'expected_incomes': [],
        })
        serializer.is_valid(raise_exception=True)

        self.stdout.write(f'Ingreso #{income.pk}: {income.concept}')
        self.stdout.write(f'  Total esperado: {income.total_amount}')
        self.stdout.write(f'  Pagado:         {paid}')
        self.stdout.write(f'  Pendiente:      {pending}')
        self.stdout.write(f'  Gasto a crear:  {label} — {period}')

        if not options['apply']:
            self.stdout.write(self.style.WARNING(
                'Dry-run: no se escribió nada. Repite con --apply.'
            ))
            return

        result = accounting_settlement_service.settle_expected_income(
            income, serializer.validated_data, user=None,
        )
        expense = result['expenses'][0]
        income.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            f'Gasto #{expense.pk} creado ({expense.source_ref}). '
            f'Ingreso #{income.pk} reducido a {income.total_amount}: cerrado.'
        ))
