"""Backfill UserProfile rows for any auth.User missing one.

Pairs with the post_save ``ensure_user_profile`` signal so every User in the
DB has a profile. Existing orphans typically come from
``manage.py createsuperuser``, which historically did not create a profile.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    # Literal role strings: data migrations cannot import current model
    # constants because they must operate on the historical schema.
    profiles = [
        UserProfile(user=user, role='admin' if user.is_superuser else 'client')
        for user in User.objects.filter(profile__isnull=True)
    ]
    if profiles:
        UserProfile.objects.bulk_create(profiles)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_project_access_fields'),
    ]

    operations = [
        migrations.RunPython(backfill, reverse_code=migrations.RunPython.noop),
    ]
