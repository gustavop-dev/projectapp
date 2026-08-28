"""Enforce DocumentState system-key uniqueness on every supported database."""

from django.db import migrations, models
from django.db.models import Count


def validate_unique_system_keys(apps, schema_editor):
    """Stop before DDL when MySQL contains keys the old constraint ignored."""
    DocumentState = apps.get_model('content', 'DocumentState')
    duplicate_keys = list(
        DocumentState.objects.using(schema_editor.connection.alias)
        .filter(system_key__isnull=False)
        .values('catalog', 'system_key')
        .annotate(occurrences=Count('id'))
        .filter(occurrences__gt=1)
        .order_by('catalog', 'system_key')
    )
    if not duplicate_keys:
        return

    details = ', '.join(
        f"{item['catalog']}:{item['system_key']!r} ({item['occurrences']})"
        for item in duplicate_keys
    )
    raise RuntimeError(
        'Cannot enforce DocumentState system-key uniqueness. '
        f'Resolve duplicate catalog/system_key pairs first: {details}'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0217_merge_disabled_controls_notes_viewmap'),
    ]

    operations = [
        migrations.RunPython(
            validate_unique_system_keys,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name='documentstate',
            name='unique_state_system_key_per_catalog',
        ),
        migrations.AddConstraint(
            model_name='documentstate',
            constraint=models.UniqueConstraint(
                fields=('catalog', 'system_key'),
                name='unique_state_system_key_per_catalog',
            ),
        ),
    ]
