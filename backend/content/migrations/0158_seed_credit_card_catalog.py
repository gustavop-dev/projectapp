"""Seed the credit-card catalog with the card in use since May 2026.

'T.C 0064' is the only real card today: cupo 8,000,000 COP and bank
statements available from 2026-05. Seeded with source_ref='' (manual
record) so fake-data cleanup never touches it.
"""

from datetime import date
from decimal import Decimal

from django.db import migrations

SEED_CARD = {
    'name': 'T.C 0064',
    'credit_limit': Decimal('8000000.00'),
    'is_active': True,
    'statements_since': date(2026, 5, 1),
}


def seed_credit_card(apps, schema_editor):
    CreditCard = apps.get_model('content', 'CreditCard')
    CreditCard.objects.get_or_create(
        name=SEED_CARD['name'],
        defaults={key: value for key, value in SEED_CARD.items() if key != 'name'},
    )


def unseed_credit_card(apps, schema_editor):
    CreditCard = apps.get_model('content', 'CreditCard')
    CreditCard.objects.filter(name=SEED_CARD['name'], source_ref='').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0157_credit_card_catalog_statement_pdf_reminder'),
    ]

    operations = [
        migrations.RunPython(seed_credit_card, unseed_credit_card),
    ]
