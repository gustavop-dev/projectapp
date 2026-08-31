"""Rename the client's inactive marker to the archive vocabulary.

``deactivated_at`` becomes ``archived_at`` so clients speak the same word as
projects, whose non-active lifecycle bucket the panel already labels
"archivado". ``RenameField`` — not drop + add — because the column carries the
state of every client that was ever put away, and a drop would silently reset
them all to active.

``archived_by`` is new: the panel used to forget who archived a client the
moment someone reactivated it.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0061_remove_project_document_manager_enabled'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='deactivated_at',
            new_name='archived_at',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='archived_at',
            field=models.DateTimeField(
                blank=True,
                default=None,
                help_text='When set, this client is archived and hidden from '
                          'the default panel client lists. Archiving is the '
                          'client-side twin of a project moving out of an '
                          'active state, and it cascades its projects to '
                          '"suspended". Independent from auth.User.is_active, '
                          'which is False for client shells.',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='archived_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Who archived this client last. Cleared on '
                          'unarchive; the durable trail is the '
                          'AccountingChangeLog row.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='archived_client_profiles',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
