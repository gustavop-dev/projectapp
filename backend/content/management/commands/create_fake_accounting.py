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
    AdsSpendRecord,
    CardBalanceSnapshot,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)

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
            half = (total / 2).quantize(Decimal('0.01'))
            concept = rng.choice(INCOME_CONCEPTS)
            expected = IncomeRecord.objects.create(
                concept=concept,
                kind=IncomeRecord.Kind.EXPECTED,
                period_date=period,
                total_amount=total,
                gustavo_amount=half,
                carlos_amount=total - half,
                source_ref=FAKE_REF,
            )
            created += 1
            # Roughly half of the expected incomes got paid (liquid row),
            # a third of those into the company pocket.
            if index % 2 == 0:
                to_pocket = index % 6 == 0
                movement = None
                if to_pocket:
                    movement = PocketMovement.objects.create(
                        concept=f'Ingreso: {concept}',
                        movement_date=period,
                        direction=PocketMovement.Direction.IN,
                        amount=total,
                        source_ref=FAKE_REF,
                    )
                    created += 1
                IncomeRecord.objects.create(
                    concept=concept,
                    kind=IncomeRecord.Kind.LIQUID,
                    period_date=period,
                    destination=(
                        IncomeRecord.Destination.POCKET
                        if to_pocket else IncomeRecord.Destination.PARTNERS
                    ),
                    total_amount=total,
                    gustavo_amount=Decimal('0') if to_pocket else half,
                    carlos_amount=Decimal('0') if to_pocket else total - half,
                    expected_income=expected,
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
            HostingRecord.objects.create(
                client_name=client_name,
                domain_url=domain,
                monthly_value=monthly,
                payment_modality=rng.choice(list(HostingRecord.Modality)),
                valid_from=_month_start(6),
                valid_to=_month_start(0) + timedelta(days=180),
                cycles_count=rng.randrange(1, 4),
                payment_per_cycle=monthly * 6,
                total_paid=monthly * 6,
                source_ref=FAKE_REF,
            )
            created += 1

        for index in range(count):
            PocketMovement.objects.create(
                concept=rng.choice(['Trans. Gustavo', 'Trans. Carlos', 'Pago T.C']),
                movement_date=_month_start(rng.randrange(0, 6)) + timedelta(
                    days=rng.randrange(0, 28),
                ),
                direction=rng.choice(list(PocketMovement.Direction)),
                amount=Decimal(rng.randrange(50_000, 900_000, 1_000)),
                source_ref=FAKE_REF,
            )
            created += 1

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

        for months_ago in range(3):
            debt = Decimal(rng.randrange(1_000_000, 8_000_000, 1_000))
            CardBalanceSnapshot.objects.create(
                snapshot_date=_month_start(months_ago),
                card_name='T.C 0064',
                available_amount=Decimal('8000000.00') - debt,
                debt_amount=debt,
                source_ref=FAKE_REF,
            )
            created += 1

        settings_obj = AccountingSettings.load()
        if not settings_obj.notification_recipients:
            settings_obj.notification_recipients = [
                'gustavo@example.com', 'carlos@example.com',
            ]
            settings_obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'Created {created} fake accounting rows (source_ref={FAKE_REF}).',
        ))
