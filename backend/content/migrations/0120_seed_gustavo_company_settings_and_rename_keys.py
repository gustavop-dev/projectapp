from django.db import migrations


GUSTAVO_DEFAULTS = {
    'contractor_full_name': 'GUSTAVO ADOLFO PEREZ PEREZ',
    'contractor_nit': '1021513348-7',
    'bank_account_number': '00774149350',
}


def _rename_key_in_jsonfield(queryset, json_field, old_key, new_key):
    dirty = []
    for obj in queryset.iterator(chunk_size=500):
        params = getattr(obj, json_field) or {}
        if old_key not in params:
            continue
        params[new_key] = params.pop(old_key)
        setattr(obj, json_field, params)
        dirty.append(obj)
    if dirty:
        queryset.model.objects.bulk_update(dirty, [json_field], batch_size=500)


def _replace_placeholder(queryset, field, old_placeholder, new_placeholder):
    dirty = []
    for obj in queryset.iterator(chunk_size=500):
        text = getattr(obj, field) or ''
        if old_placeholder not in text:
            continue
        setattr(obj, field, text.replace(old_placeholder, new_placeholder))
        dirty.append(obj)
    if dirty:
        queryset.model.objects.bulk_update(dirty, [field], batch_size=500)


def forward(apps, schema_editor):
    CompanySettings = apps.get_model('content', 'CompanySettings')
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    ConfidentialityTemplate = apps.get_model('content', 'ConfidentialityTemplate')

    CompanySettings.objects.update_or_create(pk=1, defaults=GUSTAVO_DEFAULTS)

    _rename_key_in_jsonfield(
        BusinessProposal.objects.exclude(contract_params={}),
        'contract_params', 'contractor_cedula', 'contractor_nit',
    )
    _rename_key_in_jsonfield(
        WebAppDiagnostic.objects.exclude(confidentiality_params={}),
        'confidentiality_params', 'contractor_cedula', 'contractor_nit',
    )

    _replace_placeholder(
        ContractTemplate.objects.all(), 'content_markdown',
        '{contractor_cedula}', '{contractor_nit}',
    )
    _replace_placeholder(
        ConfidentialityTemplate.objects.all(), 'content_markdown',
        '{contractor_cedula}', '{contractor_nit}',
    )


def backward(apps, schema_editor):
    BusinessProposal = apps.get_model('content', 'BusinessProposal')
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    ConfidentialityTemplate = apps.get_model('content', 'ConfidentialityTemplate')

    _rename_key_in_jsonfield(
        BusinessProposal.objects.exclude(contract_params={}),
        'contract_params', 'contractor_nit', 'contractor_cedula',
    )
    _rename_key_in_jsonfield(
        WebAppDiagnostic.objects.exclude(confidentiality_params={}),
        'confidentiality_params', 'contractor_nit', 'contractor_cedula',
    )
    _replace_placeholder(
        ContractTemplate.objects.all(), 'content_markdown',
        '{contractor_nit}', '{contractor_cedula}',
    )
    _replace_placeholder(
        ConfidentialityTemplate.objects.all(), 'content_markdown',
        '{contractor_nit}', '{contractor_cedula}',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0119_rename_contractor_cedula_to_nit'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
