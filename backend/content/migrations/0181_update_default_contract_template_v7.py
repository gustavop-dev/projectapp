# Generated 2026-08-11 — update default contract template v7:
#   1. Identify EL CONTRATISTA by whichever document is on file. The parties
#      preamble and the bank-transfer sentence said "número de cédula
#      {contractor_nit}" — the token was renamed by 0120 but the surrounding
#      words never were, so a NIT has been printing under the word "cédula"
#      ever since. Both now use the {contractor_id_type}/{contractor_id_number}
#      pair, which resolves to the NIT when there is one and to the cédula
#      otherwise, carrying the matching label.
#   2. Same treatment for the NDA, whose "NIT/C.C. número" hedge no longer has
#      to hedge.
#   3. Rename the annex to "Documento Propuesta Comercial" in the five places
#      the v6 service clauses still called it "Documento Propuesta de Negocio"
#      (wording inherited from the pre-v5 template; every other reference in
#      the contract already uses "Comercial").
#
# Item 3 is done here, and not by editing 0179 in place, because 0179 has
# already been applied in production: an edit to an applied migration never
# re-runs, so the live text would have kept the old annex name.
#
# Patch migration in the style of 0165/0179. It touches BOTH templates in one
# go, as 0120 did.

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contract template
# ---------------------------------------------------------------------------

# The client is introduced by the very same words immediately before the
# contractor, so each anchor carries its party name to stay unambiguous.
CONTRACT_PAIRS = [
    (
        'identificado con número de cédula {contractor_nit}, quien en adelante '
        'y para los efectos del presente contrato se denomina como '
        '**EL CONTRATISTA**',
        'identificado con {contractor_id_type} número {contractor_id_number}, '
        'quien en adelante y para los efectos del presente contrato se '
        'denomina como **EL CONTRATISTA**',
    ),
    (
        'a nombre de EL CONTRATISTA identificado con número de cédula '
        '{contractor_nit}.',
        'a nombre de EL CONTRATISTA identificado con {contractor_id_type} '
        'número {contractor_id_number}.',
    ),
    # Annex name, five occurrences across the v6 service clauses.
    (
        'condiciones económicas se definen en el Documento Propuesta de Negocio '
        'o en el documento que las partes suscriban',
        'condiciones económicas se definen en el Documento Propuesta Comercial '
        'o en el documento que las partes suscriban',
    ),
    (
        'conforme a la periodicidad definida en el Documento Propuesta de '
        'Negocio. EL CONTRATISTA remitirá la cuenta de cobro',
        'conforme a la periodicidad definida en el Documento Propuesta '
        'Comercial. EL CONTRATISTA remitirá la cuenta de cobro',
    ),
    (
        'conforme a la periodicidad definida en el Documento Propuesta de '
        'Negocio, sea esta mensual, trimestral',
        'conforme a la periodicidad definida en el Documento Propuesta '
        'Comercial, sea esta mensual, trimestral',
    ),
    (
        'cuya capacidad técnica se describe en el Documento Propuesta de '
        'Negocio.',
        'cuya capacidad técnica se describe en el Documento Propuesta '
        'Comercial.',
    ),
    (
        'y por las condiciones económicas definidas en el Documento Propuesta '
        'de Negocio.',
        'y por las condiciones económicas definidas en el Documento Propuesta '
        'Comercial.',
    ),
]


# ---------------------------------------------------------------------------
# Confidentiality (NDA) template
# ---------------------------------------------------------------------------

CONFIDENTIALITY_PAIRS = [
    (
        '**{contractor_full_name}**, identificado con NIT/C.C. número '
        '{contractor_nit}, quien en adelante y para los efectos del presente '
        'acuerdo se denominará **EL CONSULTOR**',
        '**{contractor_full_name}**, identificado con {contractor_id_type} '
        'número {contractor_id_number}, quien en adelante y para los efectos '
        'del presente acuerdo se denominará **EL CONSULTOR**',
    ),
]


def apply_pairs(markdown, pairs, label):
    """Apply (old, new) replacements in order.

    A missing anchor is skipped rather than raising, so a manually edited
    template does not block the deploy — but it is logged, because a silent
    skip is exactly how a half-applied change would slip through.
    """
    for old, new in pairs:
        if old in markdown:
            markdown = markdown.replace(old, new)
        else:
            logger.warning('Contract template v7 (%s): anchor not found, skipped: %r',
                           label, old[:80])
    return markdown


def _patch_default(apps, model_name, pairs, label):
    Model = apps.get_model('content', model_name)
    template = Model.objects.filter(is_default=True).first()
    if not template:
        return
    updated = apply_pairs(template.content_markdown, pairs, label)
    if updated != template.content_markdown:
        template.content_markdown = updated
        template.save(update_fields=['content_markdown'])


def update_templates(apps, schema_editor):
    _patch_default(apps, 'ContractTemplate', CONTRACT_PAIRS, 'contract')
    _patch_default(apps, 'ConfidentialityTemplate', CONFIDENTIALITY_PAIRS, 'nda')


def revert_templates(apps, schema_editor):
    _patch_default(
        apps, 'ContractTemplate',
        [(new, old) for old, new in reversed(CONTRACT_PAIRS)], 'contract',
    )
    _patch_default(
        apps, 'ConfidentialityTemplate',
        [(new, old) for old, new in reversed(CONFIDENTIALITY_PAIRS)], 'nda',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0180_contractor_cedula_and_placeholder_help_text'),
    ]

    operations = [
        migrations.RunPython(update_templates, revert_templates),
    ]
