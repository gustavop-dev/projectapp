from django.db import migrations, models


def remap_legacy_categories(apps, schema_editor):
    """Map deprecated categories (credentials, apks) onto 'other'."""
    Deliverable = apps.get_model('accounts', 'Deliverable')
    Deliverable.objects.filter(category__in=['credentials', 'apks']).update(category='other')


def noop(apps, schema_editor):
    return


CATEGORY_CHOICES = [
    ('designs', 'Diseños'),
    ('documents', 'Documentos'),
    ('contract', 'Contrato'),
    ('amendment', 'Otrosí'),
    ('legal_annex', 'Anexo legal'),
    ('other', 'Otros'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_bugreport_source_requirement_and_more'),
    ]

    operations = [
        migrations.RunPython(remap_legacy_categories, noop),
        migrations.AlterField(
            model_name='deliverable',
            name='category',
            field=models.CharField(
                choices=CATEGORY_CHOICES, default='other', max_length=20,
            ),
        ),
    ]
