from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


TEMPLATE_NAME = 'Otrosí de financiación'
TEMPLATE_VERSION = 2
TEMPLATE_MARKDOWN = """# OTROSÍ DE FINANCIACIÓN {agreement_number}

Entre los suscritos, **{client_full_name}**, identificado(a) con {client_id_type} No. {client_id_number}, en adelante **EL CONTRATANTE**, y **{contractor_full_name}**, identificado(a) con {contractor_id_type} No. {contractor_id_number}, en adelante **EL CONTRATISTA**, se celebra el presente otrosí al contrato **{original_contract_reference}**, suscrito el {original_contract_date}.

## PRIMERA. OBJETO

Las partes incorporan un mecanismo de financiación para el desarrollo e implementación de **{project_name}**, limitado al siguiente alcance aprobado:

> {financed_scope}

Este otrosí complementa el contrato original. Las cláusulas no modificadas conservan plena vigencia.

## SEGUNDA. ELEGIBILIDAD DEL ALCANCE

El proyecto, fase o conjunto de fases objeto de este ciclo tiene un valor de **{total_value}**. Para aplicar al programa, su valor debe estar entre **{minimum_project_value_cop}** y **{maximum_project_value_cop}**, ambos inclusive y expresados como valor equivalente en pesos colombianos.

{eligibility_equivalence_note}

## TERCERA. ANÁLISIS DE RIESGO, APORTE INICIAL Y SALDO

El aporte inicial se determina como resultado del análisis de riesgo y será de **{initial_payment}**, sin que pueda ser inferior al **{minimum_initial_payment_percent}%** del valor total. Project App. financiará como máximo el **{maximum_financed_percent}%**; para este ciclo el saldo financiado corresponde a **{financed_balance}**, durante {financing_months} meses y con interés ordinario del cero por ciento (0 %).

## CUARTA. CALENDARIO DE PAGOS

Cada cuota se paga entre los días **{installment_due_day_start}** y **{installment_due_day_end}** calendario del mes correspondiente, conforme al siguiente calendario:

{installment_schedule}

El pago de una cuota no extingue las cuotas anteriores que continúen pendientes.

## QUINTA. MORA Y AUMENTO DEL HOSTING

Por cada cuota que no sea pagada dentro de la ventana acordada, el costo vigente del Hosting —actualmente **{hosting_value}** con periodicidad {hosting_period}— aumentará en un **{late_hosting_increase_percent}%**. Cada aumento es acumulativo, permanente y opera automáticamente desde el vencimiento, sin necesidad de requerimiento previo. Esta consecuencia no sustituye la obligación de pagar la cuota vencida ni las demás consecuencias legalmente procedentes que se pacten y resulten aplicables.

Las partes reconocen que esta condición distribuye el riesgo de impago asumido por EL CONTRATISTA al entregar y operar el producto antes de recuperar la totalidad del saldo financiado.

## SEXTA. MODALIDAD, EXCLUSIVIDAD Y CONTINUIDAD

La modalidad elegida es **{modality_label}**, vigente desde el {partnership_start_date} hasta el {partnership_end_date}.

{modality_terms}

Durante este periodo EL CONTRATISTA será la casa desarrolladora exclusiva del producto financiado para su desarrollo, mantenimiento, soporte, infraestructura, actualizaciones y continuidad técnica. La exclusividad se limita a este producto y no restringe iniciativas independientes de EL CONTRATANTE.

## SÉPTIMA. CUSTODIA DEL CÓDIGO

EL CONTRATISTA conservará la custodia operativa de repositorios, versiones, respaldos, accesos e integridad del código durante la vigencia acordada. La custodia no transfiere a EL CONTRATISTA la propiedad intelectual ni autoriza una explotación distinta de la necesaria para ejecutar el contrato. La entrega material de repositorios se realizará al terminar la custodia y estar cumplidas las obligaciones pactadas, mediante acta.

## OCTAVA. CALCULADORA DE REQUERIMIENTOS

EL CONTRATANTE podrá describir en lenguaje natural una necesidad, su objetivo y el contexto esencial del producto. La calculadora devolverá una referencia de esfuerzo, trabajo, tiempo y rango de precio. El resultado es orientativo: sólo una cotización formal aprobada por ambas partes fija alcance, cronograma y precio definitivo.

## NOVENA. PREVALENCIA Y REVISIÓN

En caso de contradicción, este otrosí prevalece únicamente sobre las materias que modifica expresamente. Los datos, valores y fechas aquí incorporados forman parte integral del acuerdo. El documento debe ser revisado por las partes y por su asesoría jurídica antes de firma.

Firmado en {contract_city}, el {contract_date}.

| EL CONTRATANTE | EL CONTRATISTA |
| --- | --- |
| {client_full_name} | {contractor_full_name} |
| {client_id_type} {client_id_number} | {contractor_id_type} {contractor_id_number} |
| {client_email} | {contractor_email} |
"""


def seed_policy_and_template(apps, schema_editor):
    Policy = apps.get_model('content', 'FinancingPolicyRevision')
    Agreement = apps.get_model('content', 'FinancingAgreement')
    Template = apps.get_model('content', 'FinancingAgreementTemplate')

    legacy, _ = Policy.objects.update_or_create(
        version=1,
        defaults={
            'minimum_project_value_cop': Decimal('0.00'),
            'maximum_project_value_cop': Decimal('999999999999.99'),
            'financing_months': 12,
            'maximum_financed_percent': Decimal('100.00'),
            'late_hosting_increase_percent': Decimal('1.00'),
            'installment_due_day_start': 1,
            'installment_due_day_end': 5,
        },
    )
    Policy.objects.update_or_create(
        version=2,
        defaults={
            'minimum_project_value_cop': Decimal('20000000.00'),
            'maximum_project_value_cop': Decimal('140000000.00'),
            'financing_months': 12,
            'maximum_financed_percent': Decimal('80.00'),
            'late_hosting_increase_percent': Decimal('2.00'),
            'installment_due_day_start': 1,
            'installment_due_day_end': 5,
        },
    )
    Agreement.objects.filter(policy_revision__isnull=True).update(
        policy_revision=legacy,
    )

    Template.objects.filter(is_default=True).update(
        is_default=False,
        is_active=False,
    )
    Template.objects.update_or_create(
        name=TEMPLATE_NAME,
        version=TEMPLATE_VERSION,
        defaults={
            'content_markdown': TEMPLATE_MARKDOWN,
            'is_default': True,
            'is_active': True,
        },
    )


def restore_legacy_defaults(apps, schema_editor):
    Agreement = apps.get_model('content', 'FinancingAgreement')
    Template = apps.get_model('content', 'FinancingAgreementTemplate')
    Agreement.objects.update(policy_revision=None)
    Template.objects.filter(name=TEMPLATE_NAME, version=TEMPLATE_VERSION).update(
        is_default=False,
        is_active=False,
    )
    Template.objects.filter(name=TEMPLATE_NAME, version=1).update(
        is_default=True,
        is_active=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0243_merge_mcp_financing'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancingPolicyRevision',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('version', models.PositiveIntegerField(unique=True)),
                (
                    'minimum_project_value_cop',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('20000000.00'),
                        max_digits=14,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    'maximum_project_value_cop',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('140000000.00'),
                        max_digits=14,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ('financing_months', models.PositiveSmallIntegerField(default=12)),
                (
                    'maximum_financed_percent',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('80.00'),
                        max_digits=5,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                (
                    'late_hosting_increase_percent',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('2.00'),
                        max_digits=5,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ('installment_due_day_start', models.PositiveSmallIntegerField(default=1)),
                ('installment_due_day_end', models.PositiveSmallIntegerField(default=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='financing_policy_revisions_created',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-version'],
                'constraints': [
                    models.CheckConstraint(
                        condition=models.Q(minimum_project_value_cop__gte=0),
                        name='financing_policy_minimum_nonnegative',
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            maximum_project_value_cop__gte=models.F(
                                'minimum_project_value_cop',
                            ),
                        ),
                        name='financing_policy_maximum_gte_minimum',
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(financing_months__gte=1)
                            & models.Q(financing_months__lte=36)
                        ),
                        name='financing_policy_months_range',
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(maximum_financed_percent__gt=0)
                            & models.Q(maximum_financed_percent__lte=100)
                        ),
                        name='financing_policy_financed_percent_range',
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(late_hosting_increase_percent__gte=0)
                            & models.Q(late_hosting_increase_percent__lte=100)
                        ),
                        name='financing_policy_hosting_percent_range',
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(installment_due_day_start__gte=1)
                            & models.Q(installment_due_day_start__lte=28)
                            & models.Q(
                                installment_due_day_end__gte=models.F(
                                    'installment_due_day_start',
                                ),
                            )
                            & models.Q(installment_due_day_end__lte=28)
                        ),
                        name='financing_policy_due_days_range',
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name='financingagreement',
            name='eligibility_exchange_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='COP per USD snapshot used to evaluate the policy limits.',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='financingagreement',
            name='policy_revision',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='agreements',
                to='content.financingpolicyrevision',
            ),
        ),
        migrations.RunPython(seed_policy_and_template, restore_legacy_defaults),
        migrations.AlterField(
            model_name='financingagreement',
            name='policy_revision',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='agreements',
                to='content.financingpolicyrevision',
            ),
        ),
    ]
