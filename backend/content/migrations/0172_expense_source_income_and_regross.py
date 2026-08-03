"""Link deductions to their income and restore gross expected totals.

The accounting convention flips from net to gross income: the settlement
stops shrinking the expected income by its deductions, the deduction
expense now reduces utility like any other expense, and payment credit
counts liquid children + linked deductions. Two data fixes follow:

1. Backfill ``source_income`` from the ``income:<pk>:settlement`` stamp the
   settlement flow already writes into ``source_ref``.
2. Re-gross the parents that earlier settlements shrank: add each linked
   deduction's ``total_amount`` (and its stored partner split — exact
   recovery, no proportional re-derivation) back onto its income.

Reverse is a noop on purpose: re-netting would need to know which parents
were grossed here, and the new code only works over gross totals.
"""
import re

from django.db import migrations, models
import django.db.models.deletion

SETTLEMENT_REF = re.compile(r'^income:(\d+):settlement$')


def link_and_regross(apps, schema_editor):
    ExpenseRecord = apps.get_model('content', 'ExpenseRecord')
    IncomeRecord = apps.get_model('content', 'IncomeRecord')

    deductions = ExpenseRecord.objects.exclude(deduction_type='')
    income_ids = set(IncomeRecord.objects.values_list('pk', flat=True))

    linked = []
    for expense in deductions:
        match = SETTLEMENT_REF.match(expense.source_ref or '')
        if not match:
            continue
        income_id = int(match.group(1))
        if income_id not in income_ids:
            continue
        expense.source_income_id = income_id
        linked.append(expense)
    ExpenseRecord.objects.bulk_update(linked, ['source_income'])

    incomes = {}
    for expense in linked:
        income = incomes.setdefault(
            expense.source_income_id,
            IncomeRecord.objects.get(pk=expense.source_income_id),
        )
        income.total_amount += expense.total_amount
        income.gustavo_amount += expense.gustavo_amount
        income.carlos_amount += expense.carlos_amount
    IncomeRecord.objects.bulk_update(
        incomes.values(), ['total_amount', 'gustavo_amount', 'carlos_amount'],
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0171_recurring_category_and_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenserecord',
            name='source_income',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'kind': 'expected'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deduction_records',
                to='content.incomerecord',
            ),
        ),
        migrations.RunPython(link_and_regross, migrations.RunPython.noop),
    ]
