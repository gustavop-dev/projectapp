from django.db import migrations


def populate_company_settings(apps, schema_editor):
    """Seed the CompanySettings singleton with default contractor data."""
    CompanySettings = apps.get_model('content', 'CompanySettings')
    CompanySettings.objects.update_or_create(
        pk=1,
        defaults={
            'contractor_full_name': 'CARLOS MARIO BLANCO PEREZ',
            'contractor_cedula': '1.037.635.428',
            'contractor_email': 'team@projectapp.co',
            'contract_city': 'Medellín',
            'bank_name': 'Bancolombia',
            'bank_account_type': 'Ahorros',
            'bank_account_number': '26292039530',
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0065_update_default_contract_template'),
    ]

    operations = [
        migrations.RunPython(populate_company_settings, migrations.RunPython.noop),
    ]
