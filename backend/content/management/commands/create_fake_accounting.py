"""Seed plausible fake data for the accounting module (dev/staging).

Usage:
    python manage.py create_fake_accounting [--count N]

Every row is tagged source_ref='fake:accounting' so delete_fake_data can
remove exactly these rows. Written with the plain ORM: no change logs,
no email notifications.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from content.models import (
    AccountingSettings,
    CreditCardStatement,
    CreditCardTransaction,
    MerchantAlias,
    AdsSpendRecord,
    CardBalanceSnapshot,
    CreditCard,
    ExpenseRecord,
    HostingCycle,
    HostingRecord,
    IncomeRecord,
    Ledger,
    PocketMovement,
    RecurringPayment,
)
from content.serializers.accounting import split_half

FAKE_REF = 'fake:accounting'

INCOME_CONCEPTS = [
    'Acme SAS - Inicio 40%', 'Acme SAS - Diseño 30%', 'Acme SAS - Entrega 30%',
    'Globex - Inicio 40%', 'Globex - Hosting', 'Initech - Entrega 30%',
    'Umbrella - Diseño 30%', 'Hooli - Inicio 40%',
]
EXPENSE_CONCEPTS = [
    ('Claude Code 20x', 'business'), ('Google Ads - Campaña', 'business'),
    ('Figma mensual', 'business'), ('Anuncios FB', 'business'),
    ('Almuerzo equipo', 'personal'), ('Gasolina carro', 'personal'),
    ('Aporte casa EPM', 'personal'), ('Windsurf', 'business'),
]
CLIENTS = [
    ('Acme SAS', 'https://acme.example.com/'),
    ('Globex', 'https://globex.example.com/'),
    ('Initech', 'https://initech.example.com/'),
    ('Umbrella', 'https://umbrella.example.com/'),
]


def _month_start(months_ago):
    today = date.today().replace(day=1)
    year = today.year
    month = today.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


class Command(BaseCommand):
    help = 'Create fake accounting data (tagged fake:accounting).'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10)

    def handle(self, *args, **options):
        count = options['count']
        rng = random.Random(42)

        created = 0
        for index in range(count):
            period = _month_start(rng.randrange(0, 12))
            total = Decimal(rng.randrange(400_000, 4_000_000, 10_000))
            gustavo, carlos = split_half(total)
            concept = rng.choice(INCOME_CONCEPTS)
            # Written off: money we already know will never arrive. It stays
            # out of the expected projection, so it never gets a liquid row.
            is_lost = index % 8 == 3
            income = IncomeRecord.objects.create(
                concept=concept,
                kind=(
                    IncomeRecord.Kind.LOST if is_lost
                    else IncomeRecord.Kind.EXPECTED
                ),
                period_date=period,
                total_amount=total,
                gustavo_amount=gustavo,
                carlos_amount=carlos,
                source_ref=FAKE_REF,
            )
            created += 1
            if is_lost:
                continue
            # Fulfilment mix covering the three states the Ingresos tab
            # renders: a 40% partial for a quarter of the rows, a full
            # payment for the (remaining) even rows — a third of those into
            # the company pocket — and nothing for the rest.
            if index % 4 == 1:
                paid_fraction = Decimal('0.4')
            elif index % 2 == 0:
                paid_fraction = Decimal('1')
            else:
                continue
            paid = (total * paid_fraction).quantize(Decimal('0.01'))
            paid_gustavo, paid_carlos = split_half(paid)
            # index % 6 == 0 is always even, so a partial row never lands
            # in the pocket branch.
            to_pocket = index % 6 == 0
            movement = None
            if to_pocket:
                movement = PocketMovement.objects.create(
                    concept=f'Ingreso: {concept}',
                    movement_date=period + timedelta(days=14),
                    direction=PocketMovement.Direction.IN,
                    amount=paid,
                    source_ref=FAKE_REF,
                )
                created += 1
            IncomeRecord.objects.create(
                concept=concept,
                kind=IncomeRecord.Kind.LIQUID,
                # Pocket liquidations record the exact payment day, the
                # liquidate modal's optional toggle; the rest stay monthly.
                period_date=(
                    period + timedelta(days=14) if to_pocket else period
                ),
                destination=(
                    IncomeRecord.Destination.POCKET
                    if to_pocket else IncomeRecord.Destination.PARTNERS
                ),
                total_amount=paid,
                gustavo_amount=Decimal('0') if to_pocket else paid_gustavo,
                carlos_amount=Decimal('0') if to_pocket else paid_carlos,
                expected_income=income,
                pocket_movement=movement,
                source_ref=FAKE_REF,
            )
            created += 1

        for index in range(count):
            concept, category = EXPENSE_CONCEPTS[index % len(EXPENSE_CONCEPTS)]
            total = Decimal(rng.randrange(20_000, 1_200_000, 1_000))
            half = (total / 2).quantize(Decimal('0.01'))
            custom_split = index % 3 == 0
            ExpenseRecord.objects.create(
                concept=concept,
                period_date=_month_start(rng.randrange(0, 12)),
                category=category,
                total_amount=total,
                gustavo_amount=total if custom_split else half,
                carlos_amount=Decimal('0') if custom_split else total - half,
                source_ref=FAKE_REF,
            )
            created += 1

        for client_name, domain in CLIENTS[:max(1, min(count, len(CLIENTS)))]:
            monthly = Decimal(rng.randrange(20_000, 100_000, 1_000))
            cycles = rng.randrange(1, 4)
            hosting = HostingRecord.objects.create(
                client_name=client_name,
                client_email=f'facturacion@{domain.split("//")[-1].strip("/")}',
                domain_url=domain,
                monthly_value=monthly,
                payment_modality=rng.choice(list(HostingRecord.Modality)),
                valid_from=_month_start(6),
                valid_to=_month_start(0) + timedelta(days=180),
                cycles_count=cycles,
                payment_per_cycle=monthly * 6,
                total_paid=monthly * 6 * cycles,
                source_ref=FAKE_REF,
            )
            # Cycle history is the source of truth for total_paid.
            for cycle_index in range(cycles):
                HostingCycle.objects.create(
                    hosting_record=hosting,
                    modality=hosting.payment_modality,
                    amount=monthly * 6,
                    paid_at=_month_start(6 * (cycles - cycle_index)),
                    source_ref=FAKE_REF,
                )
                created += 1
            created += 1

        # Pocket egresos follow the operating model: every draw is a
        # company-ledger expense (a partner attribution assigns it 100%
        # to that partner, category personal), mirroring _sync_from_pocket.
        # A third of the rows stay unlinked to represent historical
        # movements created before the linkage existed (no backfill).
        for index in range(count):
            movement_date = _month_start(rng.randrange(0, 6)) + timedelta(
                days=rng.randrange(0, 28),
            )
            amount = Decimal(rng.randrange(50_000, 900_000, 1_000))
            shape = index % 3
            if shape == 2:
                PocketMovement.objects.create(
                    concept=rng.choice(['Trans. histórica', 'Ajuste inicial']),
                    movement_date=movement_date,
                    direction=rng.choice(list(PocketMovement.Direction)),
                    amount=amount,
                    source_ref=FAKE_REF,
                )
                created += 1
                continue
            if shape == 0:
                attribution = rng.choice([Ledger.GUSTAVO, Ledger.CARLOS])
                concept = f'Retiro {attribution.label}'
                category = ExpenseRecord.Category.PERSONAL
            else:
                attribution = Ledger.COMPANY
                concept = 'Pago T.C'
                category = ExpenseRecord.Category.BUSINESS
            if attribution == Ledger.GUSTAVO:
                gustavo, carlos = amount, Decimal('0')
            elif attribution == Ledger.CARLOS:
                gustavo, carlos = Decimal('0'), amount
            else:
                gustavo, carlos = split_half(amount)
            movement = PocketMovement.objects.create(
                concept=concept,
                movement_date=movement_date,
                direction=PocketMovement.Direction.OUT,
                amount=amount,
                source_ref=FAKE_REF,
            )
            ExpenseRecord.objects.create(
                concept=concept,
                period_date=movement_date.replace(day=1),
                ledger=Ledger.COMPANY,
                category=category,
                total_amount=amount,
                gustavo_amount=gustavo,
                carlos_amount=carlos,
                pocket_movement=movement,
                source_ref=FAKE_REF,
            )
            created += 2

        for name, price, currency, cop in [
            ('Claude Code 20x', '200.00', 'USD', '800000.00'),
            ('Netflix', '39800.00', 'COP', '39800.00'),
            ('NameCheap', '10.98', 'USD', '43920.00'),
        ]:
            RecurringPayment.objects.create(
                name=name,
                price=Decimal(price),
                currency=currency,
                cop_equivalent=Decimal(cop),
                frequency=(
                    RecurringPayment.Frequency.ANNUAL
                    if name == 'NameCheap'
                    else RecurringPayment.Frequency.MONTHLY
                ),
                billing_day=rng.randrange(1, 29),
                source_ref=FAKE_REF,
            )
            created += 1

        for index in range(count):
            AdsSpendRecord.objects.create(
                spend_date=_month_start(rng.randrange(0, 6)) + timedelta(
                    days=rng.randrange(0, 28),
                ),
                origin_card=rng.choice(['T.C 0655', 'T.C 0656']),
                amount=Decimal(rng.randrange(30_000, 200_000, 1_000)),
                source_ref=FAKE_REF,
            )
            created += 1

        # Card catalog: 'T.C 0064' may already exist as the real seeded
        # card (source_ref='') — get_or_create leaves it intact and only
        # tags cards this command actually creates.
        catalog_specs = [
            ('T.C 0064', Decimal('8000000.00'), _month_start(5)),
            ('T.C 0655', Decimal('5000000.00'), _month_start(2)),
        ]
        for name, credit_limit, statements_since in catalog_specs:
            _, was_created = CreditCard.objects.get_or_create(
                name=name,
                defaults={
                    'credit_limit': credit_limit,
                    'statements_since': statements_since,
                    'source_ref': FAKE_REF,
                },
            )
            if was_created:
                created += 1

        main_card = CreditCard.objects.get(name='T.C 0064')
        for months_ago in range(3):
            debt = Decimal(rng.randrange(1_000_000, 8_000_000, 1_000))
            CardBalanceSnapshot.objects.create(
                snapshot_date=_month_start(months_ago),
                card_name=main_card.name,
                available_amount=main_card.credit_limit - debt,
                debt_amount=debt,
                source_ref=FAKE_REF,
            )
            created += 1

        # Credit-card statements: two cards, mixed draft/processed, with
        # installments, a USD purchase, a refund and an unidentified line.
        aliases = [
            ('PAYU*NETFLIX', 'Netflix', 'software'),
            ('PRIMAX MEDELLIN', 'Primax', 'fuel'),
            ('FACEBK ADS', 'Meta Ads', 'advertising'),
        ]
        for match_text, merchant, category in aliases:
            MerchantAlias.objects.get_or_create(
                match_text=match_text,
                defaults={
                    'merchant_name': merchant,
                    'default_category': category,
                    'source_ref': FAKE_REF,
                },
            )
            created += 1

        statement_specs = [
            ('T.C 0064', 2, CreditCardStatement.Status.PROCESSED),
            ('T.C 0064', 1, CreditCardStatement.Status.PROCESSED),
            ('T.C 0064', 0, CreditCardStatement.Status.DRAFT),
            ('T.C 0655', 1, CreditCardStatement.Status.PROCESSED),
        ]
        for card_name, months_ago, statement_status in statement_specs:
            period = _month_start(months_ago)
            transactions = [
                {
                    'raw_description': 'PAYU*NETFLIX 990011',
                    'merchant_name': 'Netflix', 'category': 'software',
                    'amount': Decimal('44900.00'), 'is_identified': True,
                },
                {
                    'raw_description': 'PRIMAX MEDELLIN 8811',
                    'merchant_name': 'Primax', 'category': 'fuel',
                    'amount': Decimal(rng.randrange(120_000, 260_000, 5_000)),
                    'is_identified': True,
                },
                {
                    'raw_description': 'ANTHROP*CLAUDE.AI SF',
                    'merchant_name': 'Anthropic', 'category': 'software',
                    'amount': Decimal('88000.00'), 'is_identified': True,
                    'original_amount': Decimal('20.00'),
                    'original_currency': 'USD',
                },
                {
                    'raw_description': 'EXITO POBLADO POS 4451',
                    'merchant_name': 'Éxito', 'category': 'groceries',
                    'amount': Decimal(rng.randrange(150_000, 500_000, 10_000)),
                    'is_identified': True,
                    'installment_number': 1 + months_ago,
                    'installments_total': 12,
                },
                {
                    'raw_description': 'COMERCIALIZADORA XYZ SAS',
                    'amount': Decimal('99900.00'),
                },
                {
                    'raw_description': 'REVERSION PAYU*NETFLIX',
                    'merchant_name': 'Netflix', 'category': 'software',
                    'amount': Decimal('-44900.00'), 'is_identified': True,
                },
            ]
            purchases_total = sum(tx['amount'] for tx in transactions)
            statement, was_created = CreditCardStatement.objects.get_or_create(
                card_name=card_name,
                period_date=period,
                defaults={
                    'status': statement_status,
                    'purchases_total': purchases_total,
                    'previous_balance': Decimal(
                        rng.randrange(1_000_000, 5_000_000, 10_000),
                    ),
                    'payments_total': Decimal(
                        rng.randrange(500_000, 2_000_000, 10_000),
                    ),
                    'interest_and_fees': Decimal(
                        rng.randrange(30_000, 120_000, 1_000),
                    ),
                    'minimum_payment': Decimal(
                        rng.randrange(200_000, 600_000, 10_000),
                    ),
                    'due_date': period + timedelta(days=45),
                    'source_ref': FAKE_REF,
                },
            )
            if was_created:
                CreditCardTransaction.objects.bulk_create(
                    CreditCardTransaction(
                        statement=statement,
                        transaction_date=period + timedelta(
                            days=rng.randrange(1, 27),
                        ),
                        source_ref=FAKE_REF,
                        **tx,
                    )
                    for tx in transactions
                )
                created += 1 + len(transactions)

        settings_obj = AccountingSettings.load()
        if not settings_obj.notification_recipients:
            settings_obj.notification_recipients = [
                'gustavo@example.com', 'carlos@example.com',
            ]
            settings_obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'Created {created} fake accounting rows (source_ref={FAKE_REF}).',
        ))
