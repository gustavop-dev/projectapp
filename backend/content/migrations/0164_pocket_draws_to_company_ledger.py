from django.db import migrations


def draws_to_company(apps, schema_editor):
    """Convert pocket-linked personal-ledger expenses into company draws.

    Money that left the pocket is company money: keeping the mirrored
    expense on a personal ledger drained the pocket balance without
    reducing the company utility. The full-to-owner split these records
    already carry becomes the partner attribution, so amounts stay intact.
    """
    ExpenseRecord = apps.get_model('content', 'ExpenseRecord')
    ExpenseRecord.objects.filter(
        pocket_movement__isnull=False,
        ledger__in=('gustavo', 'carlos'),
    ).update(ledger='company')


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0163_viewmapsettings'),
    ]

    operations = [
        migrations.RunPython(draws_to_company, migrations.RunPython.noop),
    ]
