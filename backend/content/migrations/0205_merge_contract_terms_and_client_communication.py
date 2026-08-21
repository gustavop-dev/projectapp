"""Reunify the two content migration branches created at 0204.

The contract-terms and private client-communication features were developed in
parallel, so both migrations depend on 0203.  Once both feature branches landed,
Django correctly reported two leaf nodes and refused to migrate.

This migration is intentionally empty.  It records that both independent schema
changes must run before later content migrations without renaming or re-parenting
either migration after merge.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0204_businessproposal_contract_terms_mode'),
        ('content', '0204_document_client_communication'),
    ]

    operations = []
