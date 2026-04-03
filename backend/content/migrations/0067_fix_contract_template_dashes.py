# Generated 2026-04-03 — normalize double-dash separators in contract template

import re

from django.db import migrations


def fix_dashes(apps, schema_editor):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    for template in ContractTemplate.objects.filter(is_default=True):
        template.content_markdown = re.sub(r' -- ', ' - ', template.content_markdown)
        template.save()


def reverse_fix(apps, schema_editor):
    # Reversing would require knowing the original text; no-op is safe.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0066_populate_company_settings'),
    ]

    operations = [
        migrations.RunPython(fix_dashes, reverse_fix),
    ]
