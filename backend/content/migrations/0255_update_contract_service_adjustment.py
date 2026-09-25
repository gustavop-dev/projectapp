"""Align the default contract's minimum adjustment with commercial terms.

Patch only the shipped paragraph, preserving manually negotiated wording and
all other clauses. Existing PDFs and custom proposal contracts are untouched.
"""

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


OLD_PARAGRAPH = """\
### Parágrafo Tercero — Reajuste Anual del Valor del Servicio

El valor del servicio se reajustará automáticamente cada primero (1.º) de enero, aplicando al valor vigente del año inmediatamente anterior el porcentaje en que el Gobierno Nacional haya incrementado el salario mínimo mensual legal vigente (SMMLV) para ese año. Si para un año determinado no se decretare incremento del SMMLV, el reajuste se calculará con la variación anual del Índice de Precios al Consumidor (IPC) certificada por el DANE para el año inmediatamente anterior. El valor así reajustado constituye el valor vigente del servicio para todos los efectos del presente contrato. Las partes reconocen que este reajuste no constituye un incremento del precio ni un cobro adicional, sino un mecanismo de corrección monetaria destinado a conservar el valor real de la contraprestación, dado que los costos que sostienen la operación del servicio se incrementan anualmente cuando menos en la misma proporción."""

NEW_PARAGRAPH = """\
### Parágrafo Tercero — Condiciones Mínimas de Reajuste del Valor del Servicio

El valor del servicio estará sujeto a reajuste anual, conforme a las condiciones mínimas previstas en este parágrafo y a las condiciones particulares establecidas en el Documento Propuesta Comercial aceptado por las partes.

Como base mínima de reajuste se aplicará al valor vigente del servicio el porcentaje de incremento del salario mínimo mensual legal vigente (SMMLV) decretado por el Gobierno Nacional para el año en que corresponda efectuar el ajuste. Si para dicho año no se decretare incremento del SMMLV, se utilizará la variación anual del Índice de Precios al Consumidor (IPC) certificada por el DANE para el año inmediatamente anterior.

La periodicidad de pago, la fecha del primer reajuste, su aplicación en las renovaciones y los porcentajes o componentes adicionales que integren la fórmula de actualización serán los expresamente establecidos en el Documento Propuesta Comercial aceptado por las partes, respetando la base mínima aquí prevista. En consecuencia, el reajuste no se causará por el solo inicio del año calendario, sino en la oportunidad pactada en dicho documento, sin duplicarse por razón de la periodicidad de facturación.

El reajuste tiene por finalidad actualizar la contraprestación del servicio y atender la evolución de sus costos de operación, mantenimiento y soporte."""


def _patch_default_template(apps, schema_editor, old, new):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    database = schema_editor.connection.alias
    template = (
        ContractTemplate.objects.using(database).filter(is_default=True).first()
    )
    if template is None or new in template.content_markdown:
        return
    if old not in template.content_markdown:
        logger.warning(
            'Contract service adjustment: paragraph not found in default '
            'template %s; preserving its custom wording.',
            template.pk,
        )
        return
    template.content_markdown = template.content_markdown.replace(old, new, 1)
    template.save(using=database, update_fields=['content_markdown'])


def update_default_template(apps, schema_editor):
    _patch_default_template(apps, schema_editor, OLD_PARAGRAPH, NEW_PARAGRAPH)


def revert_default_template(apps, schema_editor):
    _patch_default_template(apps, schema_editor, NEW_PARAGRAPH, OLD_PARAGRAPH)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0254_linktree_assets'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
