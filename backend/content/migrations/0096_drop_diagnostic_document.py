from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0095_seed_diagnostic_sections'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DiagnosticDocument',
        ),
    ]
