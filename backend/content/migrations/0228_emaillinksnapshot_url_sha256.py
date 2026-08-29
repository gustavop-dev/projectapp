import hashlib

from django.db import migrations, models
from django.db.models import Count


BATCH_SIZE = 500


def populate_url_sha256(apps, _schema_editor):
    EmailLinkSnapshot = apps.get_model('content', 'EmailLinkSnapshot')
    pending = []
    queryset = EmailLinkSnapshot.objects.only('id', 'url').iterator(
        chunk_size=BATCH_SIZE,
    )
    for link in queryset:
        link.url_sha256 = hashlib.sha256(link.url.encode('utf-8')).hexdigest()
        pending.append(link)
        if len(pending) == BATCH_SIZE:
            EmailLinkSnapshot.objects.bulk_update(
                pending,
                ['url_sha256'],
                batch_size=BATCH_SIZE,
            )
            pending = []
    if pending:
        EmailLinkSnapshot.objects.bulk_update(
            pending,
            ['url_sha256'],
            batch_size=BATCH_SIZE,
        )

    has_duplicate = (
        EmailLinkSnapshot.objects
        .values('snapshot_id', 'url_sha256')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
        .exists()
    )
    if has_duplicate:
        raise RuntimeError(
            'Cannot enforce email link uniqueness because one delivery '
            'contains duplicate URL fingerprints.',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0227_merge_email_history_additional_modules_project_folders'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillinksnapshot',
            name='url_sha256',
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(populate_url_sha256, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='emaillinksnapshot',
            name='url_sha256',
            field=models.CharField(editable=False, max_length=64),
        ),
        migrations.AddConstraint(
            model_name='emaillinksnapshot',
            constraint=models.UniqueConstraint(
                fields=('snapshot', 'url_sha256'),
                name='uniq_email_snapshot_link_hash',
            ),
        ),
    ]
