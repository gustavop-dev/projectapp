from contextlib import contextmanager
from importlib import import_module
from types import SimpleNamespace

import pytest
from django.db import migrations
from django.db.migrations.state import ProjectState


migration = import_module('content.migrations.0223_email_delivery_snapshots')


class FakeCursor:
    def __init__(self, counts):
        self.counts = counts
        self.query = ''

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False

    def execute(self, query):
        self.query = query

    def fetchone(self):
        table_name = self.query.split('`', 2)[1]
        count_key = (
            (table_name, 'referenced')
            if 'IS NOT NULL' in self.query
            else table_name
        )
        return (self.counts.get(count_key, self.counts.get(table_name, 0)),)


class FakeIntrospection:
    def __init__(self, tables):
        self.tables = tables

    def table_names(self, _cursor):
        return list(self.tables)

    def get_table_description(self, _cursor, table_name):
        columns = self.tables[table_name].get('columns', ())
        return [SimpleNamespace(name=column) for column in columns]

    def get_constraints(self, _cursor, table_name):
        return self.tables[table_name].get('constraints', {})


class FakeConnection:
    alias = 'default'
    vendor = 'mysql'

    def __init__(self, tables, counts):
        self.introspection = FakeIntrospection(tables)
        self.counts = counts
        self.ops = SimpleNamespace(quote_name=lambda name: f'`{name}`')

    def cursor(self):
        return FakeCursor(self.counts)


class FakeSchemaEditor:
    atomic_migration = False

    def __init__(self, tables, counts):
        self.connection = FakeConnection(tables, counts)
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)


def partial_schema_editor(counts=None):
    tables = {
        'content_emaillinksnapshot': {},
        'content_emailattachmentsnapshot': {},
        'content_emaildeliverysnapshot': {},
        'content_emaillog': {
            'columns': ('id', 'snapshot_id'),
            'constraints': {
                'content_emaillog_snapshot_fk': {
                    'columns': ['snapshot_id'],
                    'foreign_key': ('content_emaildeliverysnapshot', 'id'),
                },
            },
        },
    }
    return FakeSchemaEditor(tables, counts or {})


def test_recovery_removes_empty_mysql_artifacts():
    schema_editor = partial_schema_editor()

    migration.reset_empty_mysql_snapshot_artifacts(None, schema_editor)

    assert schema_editor.statements == [
        'DROP TABLE `content_emaillinksnapshot`',
        'DROP TABLE `content_emailattachmentsnapshot`',
        'ALTER TABLE `content_emaillog` DROP FOREIGN KEY '
        '`content_emaillog_snapshot_fk`',
        'ALTER TABLE `content_emaillog` DROP COLUMN `snapshot_id`',
        'DROP TABLE `content_emaildeliverysnapshot`',
    ]


def test_recovery_stays_outside_transaction_on_nontransactional_ddl_backend(
    monkeypatch,
):
    entered_transactions = []

    @contextmanager
    def record_atomic(alias):
        entered_transactions.append(alias)
        yield

    monkeypatch.setattr('django.db.migrations.migration.atomic', record_atomic)
    schema_editor = partial_schema_editor()
    recovery_migration = migrations.Migration(
        'test_recovery_atomicity',
        'content',
    )
    recovery_migration.operations = [migration.Migration.operations[0]]

    recovery_migration.apply(ProjectState(), schema_editor)

    assert entered_transactions == []


def test_recovery_refuses_populated_mysql_artifacts():
    schema_editor = partial_schema_editor({
        'content_emaildeliverysnapshot': 1,
    })

    with pytest.raises(RuntimeError, match='contains data'):
        migration.reset_empty_mysql_snapshot_artifacts(None, schema_editor)

    assert schema_editor.statements == []


def test_recovery_ignores_a_clean_mysql_schema():
    schema_editor = FakeSchemaEditor({'content_emaillog': {'columns': ('id',)}}, {})

    migration.reset_empty_mysql_snapshot_artifacts(None, schema_editor)

    assert schema_editor.statements == []
