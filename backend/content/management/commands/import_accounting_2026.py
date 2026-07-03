"""Import the 2026 accounting spreadsheet fixture into the accounting module.

Usage:
    python manage.py import_accounting_2026 [--file path.json] [--dry-run] [--prune]

Fixture schema (JSON): top-level keys `incomes_expected`, `incomes_liquid`,
`expenses`, `hostings`, `pocket_movements`, `recurring_payments`,
`ads_spend`, `card_snapshots`. Row fields use the model field names, with
`period` as "YYYY-MM" (see content/fixtures/accounting_2026.json). Income
and expense rows accept an optional `ledger` ("company" default, "gustavo"
or "carlos" for personal-ledger records excluded from company totals).

Idempotent: every row gets a deterministic `source_ref` built from its
section + natural key (+ occurrence index for duplicated rows), and rows
are written with update_or_create — re-running after fixing an amount in
the fixture updates the existing record instead of duplicating it.

`--prune` deletes previously imported rows (`source_ref` starting with
`import:`) that this run did not regenerate — use it after renaming or
removing fixture rows. Manual records (empty source_ref) and fake data
(`fake:*`) are never touched, and only models present in the fixture are
pruned.

No notifications are sent: rows are written with the plain ORM and a
single summary AccountingChangeLog row is recorded per touched section.
Pocket-bound liquid incomes are linked to their matching imported pocket
movement so later panel edits mirror into the existing ledger row instead
of creating a duplicate.
"""
import hashlib
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.models import (
    AccountingChangeLog,
    AdsSpendRecord,
    CardBalanceSnapshot,
    ExpenseRecord,
    HostingRecord,
    IncomeRecord,
    PocketMovement,
    RecurringPayment,
)

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'accounting_2026.json'


def _period_to_date(period):
    year, month = period.split('-')
    return date(int(year), int(month), 1)


def _source_ref(section, natural_key, occurrence):
    digest = hashlib.sha1(
        f'{section}|{natural_key}|{occurrence}'.encode('utf-8'),
    ).hexdigest()[:40]
    return f'import:{digest}'


def _normalize(concept):
    return ' '.join((concept or '').lower().split())


class Command(BaseCommand):
    help = 'Import the 2026 accounting spreadsheet fixture (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=str(DEFAULT_FIXTURE),
            help='Path to the fixture JSON (default: content/fixtures/accounting_2026.json)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report per-section counts without writing anything.',
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help=(
                'Delete previously imported rows (source_ref "import:*") '
                'that this run did not regenerate.'
            ),
        )

    def handle(self, *args, **options):
        fixture_path = Path(options['file'])
        if not fixture_path.exists():
            raise CommandError(f'Fixture not found: {fixture_path}')
        with open(fixture_path, encoding='utf-8') as handle:
            data = json.load(handle)

        self.dry_run = options['dry_run']
        self.prune = options['prune']
        self.stats = {}
        self.generated_refs = {}

        with transaction.atomic():
            self._import_incomes(data.get('incomes_expected', []), IncomeRecord.Kind.EXPECTED)
            self._import_incomes(data.get('incomes_liquid', []), IncomeRecord.Kind.LIQUID)
            self._import_expenses(data.get('expenses', []))
            self._import_hostings(data.get('hostings', []))
            self._import_pocket(data.get('pocket_movements', []))
            self._import_recurring(data.get('recurring_payments', []))
            self._import_ads(data.get('ads_spend', []))
            self._import_card_snapshots(data.get('card_snapshots', []))

            if self.prune:
                self._prune_stale()

            if not self.dry_run:
                self._link_liquid_to_expected()
                self._link_pocket_movements()
                self._write_summary_logs()

            if self.dry_run:
                transaction.set_rollback(True)

        for section, (created, updated) in self.stats.items():
            prefix = '[dry-run] ' if self.dry_run else ''
            self.stdout.write(self.style.SUCCESS(
                f'{prefix}{section}: {created} created, {updated} updated',
            ))

    # ── Section importers ──

    def _upsert(self, section, model, rows_with_keys):
        created_count = 0
        updated_count = 0
        occurrences = Counter()
        refs = self.generated_refs.setdefault(model, set())
        for natural_key, defaults in rows_with_keys:
            occurrence = occurrences[natural_key]
            occurrences[natural_key] += 1
            source_ref = _source_ref(section, natural_key, occurrence)
            refs.add(source_ref)
            _, created = model.objects.update_or_create(
                source_ref=source_ref, defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        self.stats[section] = (created_count, updated_count)

    def _import_incomes(self, rows, kind):
        section = f'incomes_{kind}'
        self._upsert(section, IncomeRecord, [
            (
                f'{row["concept"]}|{row["period"]}',
                {
                    'concept': row['concept'],
                    'kind': kind,
                    'period_date': _period_to_date(row['period']),
                    'destination': row.get('destination', 'partners'),
                    'ledger': row.get('ledger', 'company'),
                    'total_amount': Decimal(row['total_amount']),
                    'gustavo_amount': Decimal(row['gustavo_amount']),
                    'carlos_amount': Decimal(row['carlos_amount']),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_expenses(self, rows):
        # Natural key deliberately excludes amounts so fixing a value in
        # the fixture updates the record in place; the occurrence counter
        # disambiguates genuinely duplicated concept+period rows.
        self._upsert('expenses', ExpenseRecord, [
            (
                f'{row["concept"]}|{row["period"]}',
                {
                    'concept': row['concept'],
                    'period_date': _period_to_date(row['period']),
                    'category': row.get('category', 'business'),
                    'paid_from': row.get('paid_from', 'partners'),
                    'ledger': row.get('ledger', 'company'),
                    'total_amount': Decimal(row['total_amount']),
                    'gustavo_amount': Decimal(row['gustavo_amount']),
                    'carlos_amount': Decimal(row['carlos_amount']),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_hostings(self, rows):
        self._upsert('hostings', HostingRecord, [
            (
                row['client_name'],
                {
                    'client_name': row['client_name'],
                    'domain_url': row.get('domain_url', ''),
                    'monthly_value': Decimal(row['monthly_value']),
                    'payment_modality': row['payment_modality'],
                    'benefit': row.get('benefit', ''),
                    'valid_from': row.get('valid_from') or None,
                    'valid_to': row.get('valid_to') or None,
                    'cycles_count': row.get('cycles_count', 0),
                    'payment_per_cycle': Decimal(row.get('payment_per_cycle', '0')),
                    'total_paid': Decimal(row.get('total_paid', '0')),
                    'is_active': row.get('is_active', True),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_pocket(self, rows):
        self._upsert('pocket_movements', PocketMovement, [
            (
                f'{row["concept"]}|{row["movement_date"]}|{row["direction"]}|{row["amount"]}',
                {
                    'concept': row['concept'],
                    'movement_date': row['movement_date'],
                    'direction': row['direction'],
                    'amount': Decimal(row['amount']),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_recurring(self, rows):
        self._upsert('recurring_payments', RecurringPayment, [
            (
                row['name'],
                {
                    'name': row['name'],
                    'price': Decimal(row['price']),
                    'currency': row.get('currency', 'COP'),
                    'cop_equivalent': Decimal(row.get('cop_equivalent', '0')),
                    'payment_method': row.get('payment_method', 'credit_card'),
                    'frequency': row.get('frequency', 'monthly'),
                    'billing_day': row.get('billing_day'),
                    'cost_type': row.get('cost_type', 'fixed'),
                    'is_active': row.get('is_active', True),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_ads(self, rows):
        self._upsert('ads_spend', AdsSpendRecord, [
            (
                f'{row["spend_date"]}|{row["amount"]}|{row.get("origin_card", "")}',
                {
                    'spend_date': row['spend_date'],
                    'platform': row.get('platform', 'facebook'),
                    'origin_card': row.get('origin_card', ''),
                    'amount': Decimal(row['amount']),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    def _import_card_snapshots(self, rows):
        self._upsert('card_snapshots', CardBalanceSnapshot, [
            (
                f'{row["card_name"]}|{row["snapshot_date"]}',
                {
                    'snapshot_date': row['snapshot_date'],
                    'card_name': row['card_name'],
                    'available_amount': Decimal(row['available_amount']),
                    'debt_amount': Decimal(row['debt_amount']),
                    'notes': row.get('notes', ''),
                },
            )
            for row in rows
        ])

    # ── Pruning ──

    def _prune_stale(self):
        """Delete imported rows this run did not regenerate.

        Only models present in the fixture are pruned, so a partial JSON
        never wipes other sections. FKs pointing at pruned rows are
        SET_NULL, so linked records survive.
        """
        for model, refs in self.generated_refs.items():
            stale = model.objects.filter(
                source_ref__startswith='import:',
            ).exclude(source_ref__in=refs)
            count = stale.count()
            if count:
                stale.delete()
            prefix = '[dry-run] ' if self.dry_run else ''
            self.stdout.write(
                f'{prefix}pruned {count} stale {model.__name__} row(s).',
            )

    # ── Post-import linking ──

    def _link_liquid_to_expected(self):
        """Best-effort: match liquid rows to expected rows by concept.

        Matching is scoped per ledger so a company liquid row never links
        to a partner's personal expected row.
        """
        unlinked = 0
        for liquid in IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, expected_income__isnull=False,
        ).select_related('expected_income'):
            if liquid.expected_income.ledger != liquid.ledger:
                liquid.expected_income = None
                liquid.save(update_fields=['expected_income', 'updated_at'])
                unlinked += 1
        if unlinked:
            self.stdout.write(
                f'Unlinked {unlinked} cross-ledger liquid/expected pair(s).',
            )

        expected_by_concept = {}
        for record in IncomeRecord.objects.filter(kind=IncomeRecord.Kind.EXPECTED):
            key = (record.ledger, _normalize(record.concept))
            expected_by_concept.setdefault(key, []).append(record)

        linked = 0
        for liquid in IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID, expected_income__isnull=True,
        ):
            matches = expected_by_concept.get(
                (liquid.ledger, _normalize(liquid.concept)), [],
            )
            if len(matches) == 1:
                liquid.expected_income = matches[0]
                liquid.save(update_fields=['expected_income', 'updated_at'])
                linked += 1
        self.stdout.write(f'Linked {linked} liquid incomes to expected records.')

    def _link_pocket_movements(self):
        """Link pocket-bound liquid incomes to their imported ledger row.

        Prevents a later panel edit from generating a duplicate movement:
        the pocket sync updates the linked row instead.
        """
        linked = 0
        for income in IncomeRecord.objects.filter(
            kind=IncomeRecord.Kind.LIQUID,
            destination=IncomeRecord.Destination.POCKET,
            pocket_movement__isnull=True,
        ):
            movement = (
                PocketMovement.objects
                .filter(
                    direction=PocketMovement.Direction.IN,
                    amount=income.total_amount,
                    income_record__isnull=True,
                    source_ref__startswith='import:',
                )
                .filter(concept__iexact=income.concept)
                .first()
            )
            if movement:
                income.pocket_movement = movement
                income.save(update_fields=['pocket_movement', 'updated_at'])
                linked += 1
        self.stdout.write(f'Linked {linked} pocket incomes to ledger movements.')

    def _write_summary_logs(self):
        section_entities = {
            'incomes_expected': AccountingChangeLog.EntityType.INCOME,
            'incomes_liquid': AccountingChangeLog.EntityType.INCOME,
            'expenses': AccountingChangeLog.EntityType.EXPENSE,
            'hostings': AccountingChangeLog.EntityType.HOSTING,
            'pocket_movements': AccountingChangeLog.EntityType.POCKET,
            'recurring_payments': AccountingChangeLog.EntityType.RECURRING,
            'ads_spend': AccountingChangeLog.EntityType.ADS,
            'card_snapshots': AccountingChangeLog.EntityType.CARD_SNAPSHOT,
        }
        for section, (created, updated) in self.stats.items():
            if created or updated:
                AccountingChangeLog.objects.create(
                    entity_type=section_entities[section],
                    object_id=0,
                    object_repr=f'Importación Excel 2026 — {section}',
                    action=AccountingChangeLog.Action.CREATED,
                    changes=[{
                        'field': 'import',
                        'label': 'Importación',
                        'old': '',
                        'new': f'{created} creados, {updated} actualizados',
                    }],
                    actor_username='importador',
                )
