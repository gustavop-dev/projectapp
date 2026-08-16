"""Mark the pre-existing factory tabs as seeded.

Until now nothing told a tab the seeding created apart from one the user
saved, which is why "Restablecer" had to delete the whole view. Rows whose
name matches the registry for their view are the factory ones; anything else
is the user's and must survive the next reset.

A user who happened to name a tab exactly like a factory one loses that
distinction here — the row is adopted as seeded. That is the same collision
the old reset resolved by deleting everything, so nothing gets worse, and
after this the two kinds are told apart by a column instead of by name.
"""

from django.db import migrations

from accounts.default_filter_tabs import DEFAULT_FILTER_TABS


def forwards(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')
    for view, specs in DEFAULT_FILTER_TABS.items():
        names = [spec['name'] for spec in specs]
        if names:
            SavedFilterTab.objects.filter(
                view=view, name__in=names,
            ).update(is_seeded=True)


def backwards(apps, schema_editor):
    SavedFilterTab = apps.get_model('accounts', 'SavedFilterTab')
    SavedFilterTab.objects.update(is_seeded=False)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_saved_filter_tab_seeded_hidden'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
