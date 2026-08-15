"""The composite index the per-client annotations read.

Last of the three so MySQL does not maintain it through the backfill's
UPDATEs. Online (ALGORITHM=INPLACE) on MySQL 8.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0197_backfill_email_log_client'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(
                fields=['client', 'audience', 'sent_at'],
                name='emaillog_client_aud_sent',
            ),
        ),
    ]
