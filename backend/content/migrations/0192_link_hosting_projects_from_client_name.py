"""Consolidate the legacy `Marca` half of hostings into the Project relation.

The house convention crammed client AND project into ``client_name`` as
``Persona - Marca`` ("German - Kore"). The client half became a relation
first, and #163 added the ``project`` FK — but rows created before it keep
``project`` NULL with the brand still inside the text. This materializes
ONLY the deterministic case: a hosting whose client is already linked and
whose name carries the ``' - '`` separator. The client is known, so
extracting the brand guesses no identities (the PA-25 criterion); rows
without a separator are skipped on purpose — they surface in
``/panel/projects``, which is the deliberate completion mechanism.

The logic stays inline with ``apps.get_model`` on purpose: a migration must
not import runtime services or helpers. The normalization mirrors the
semantics of ``utils/clientMatch.js`` ``normalizeName`` (NFKD accents
stripped, casefolded, whitespace collapsed) so an accent or case variant
reuses the client's existing project instead of duplicating it.

Idempotent by construction (it only touches ``project__isnull=True`` rows).
Reverse is a noop: unlinking would need to remember which projects were
born here.
"""
import logging
import unicodedata

from django.db import migrations

logger = logging.getLogger(__name__)


def _normalize(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return ' '.join(text.casefold().split())


def link_projects_from_client_name(apps, schema_editor):
    HostingRecord = apps.get_model('content', 'HostingRecord')
    Project = apps.get_model('accounts', 'Project')

    pending = (
        HostingRecord.objects
        .filter(project__isnull=True, client__isnull=False)
        .select_related('client')
    )

    linked = created = skipped = 0
    updated = []
    projects_by_user = {}

    for hosting in pending:
        raw = hosting.client_name or ''
        if ' - ' not in raw:
            skipped += 1
            continue
        brand = raw.split(' - ', 1)[1].strip()
        if not brand:
            skipped += 1
            continue
        user_id = hosting.client.user_id
        if user_id not in projects_by_user:
            projects_by_user[user_id] = {
                _normalize(project.name): project
                for project in Project.objects.filter(client_id=user_id)
            }
        catalog = projects_by_user[user_id]
        project = catalog.get(_normalize(brand))
        if project is None:
            project = Project.objects.create(
                client_id=user_id, name=brand, status='active',
            )
            catalog[_normalize(brand)] = project
            created += 1
        hosting.project_id = project.pk
        updated.append(hosting)
        linked += 1

    if updated:
        HostingRecord.objects.bulk_update(updated, ['project'])
    logger.info(
        'Hosting project consolidation: %s linked (%s projects created, '
        '%s rows skipped for manual completion).',
        linked, created, skipped,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0191_notification_recipient_catalog'),
        ('accounts', '0046_savedfiltertab_collections_view'),
    ]

    operations = [
        migrations.RunPython(
            link_projects_from_client_name, migrations.RunPython.noop,
        ),
    ]
