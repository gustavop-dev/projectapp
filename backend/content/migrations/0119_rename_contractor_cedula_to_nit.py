from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0118_roi_projection_section'),
    ]

    operations = [
        migrations.RenameField(
            model_name='companysettings',
            old_name='contractor_cedula',
            new_name='contractor_nit',
        ),
        migrations.AlterField(
            model_name='companysettings',
            name='contractor_nit',
            field=models.CharField(
                blank=True,
                default='',
                help_text='NIT del contratista (persona natural con NIT registrado).',
                max_length=30,
            ),
        ),
    ]
