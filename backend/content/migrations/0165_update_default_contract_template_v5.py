# Generated 2026-07-24 — update default contract template v5:
#   1. Add "Parágrafo Décimo — Alcance del Trabajo Contratado" to Cláusula
#      Segunda, porting the scope-exclusion clause already used in the
#      commercial proposal PDF into contract register.
#   2. Add a new "CLÁUSULA NOVENA — ENTREGA DEL CÓDIGO FUENTE Y ACCESO A
#      REPOSITORIOS" that conditions source-code delivery and repository
#      access on 100% payment (collateral against non-payment risk), and
#      condition the intellectual property assignment on the same event.
#   3. Renumber clauses 9-19 -> 10-20 and fix the 5 body cross-references
#      that point at the shifted clauses.
#
# Ordering matters: bare cross-references are rewritten FIRST (while the old
# headings are still in place and cannot be matched by the anchors used here),
# then headings are renamed (each anchored with its full title, so no cascade),
# and only then are the new blocks inserted (their text already carries the
# final numbering).

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# New text blocks
# ---------------------------------------------------------------------------

SCOPE_PARAGRAPH = """\
### Parágrafo Décimo — Alcance del Trabajo Contratado

1. El trabajo contratado y cotizado corresponde únicamente a lo descrito dentro del alcance del Documento Propuesta Comercial y del Documento Detalle Técnico anexos al presente contrato. Cualquier conversación, mensaje, correo electrónico, reunión, idea, recurso, archivo, referencia o solicitud que surja antes o durante la ejecución del contrato y que no esté explícitamente descrita dentro de dicho alcance no constituye, por sí sola, un compromiso de implementación por parte de EL CONTRATISTA ni hace parte del trabajo contratado.
2. Lo anterior no limita la comunicación entre las partes: estas podrán conversar y explorar ideas libremente durante la ejecución del proyecto. Sin embargo, para que una funcionalidad, cambio o entregable pase a formar parte del trabajo contratado, deberá quedar documentado y cotizado como parte del alcance, y formalizarse mediante un OTROSÍ conforme a la CLÁUSULA DÉCIMA TERCERA o mediante un contrato independiente entre las partes. Esto protege a ambas partes: evita malentendidos sobre lo que está incluido, mantiene el proyecto enfocado y asegura que cada esfuerzo adicional se planifique y se remunere de forma justa.
3. En consecuencia, los plazos, precios, garantías y obligaciones del presente contrato aplican exclusivamente sobre el alcance descrito en los anexos. Todo requerimiento que exceda dicho alcance se gestionará mediante los paquetes de horas definidos en el Documento Propuesta Comercial cuando se trate de esfuerzos bajos o medio-bajos, y como una cotización independiente cuando se trate de esfuerzos medios o superiores.
4. La ejecución por parte de EL CONTRATISTA de cualquier actividad no comprendida en el alcance no constituirá modificación del mismo, no generará derecho a exigir prestaciones similares en el futuro, ni podrá interpretarse como renuncia a lo establecido en el presente parágrafo."""


SOURCE_CODE_CLAUSE = """\
## CLÁUSULA NOVENA — ENTREGA DEL CÓDIGO FUENTE Y ACCESO A REPOSITORIOS

La entrega del código fuente y el otorgamiento de acceso a los repositorios del producto software están condicionados al pago íntegro del cien por ciento (100%) del valor total del presente contrato, conforme al calendario de pagos definido en la CLÁUSULA TERCERA y en el Documento Propuesta Comercial anexo. Las partes reconocen expresamente que esta condición constituye una garantía frente al riesgo de impago y es un elemento esencial y determinante del consentimiento de EL CONTRATISTA para la celebración del presente contrato.

### Parágrafo Primero — Elementos Sujetos a la Condición

Hasta tanto no se acredite el pago del cien por ciento (100%) del valor total del contrato, EL CONTRATISTA no estará obligado a entregar, y EL CONTRATANTE no tendrá derecho a exigir ni a acceder a:

a) El código fuente del producto software, en cualquier soporte, formato o medio.
b) El acceso, en cualquier modalidad, a los repositorios de control de versiones del proyecto, así como a su historial de cambios, ramas y confirmaciones.
c) La transferencia de titularidad, propiedad o administración de dichos repositorios a EL CONTRATANTE o a terceros designados por este.
d) Los archivos de configuración de integración y despliegue continuo, scripts de construcción, scripts de despliegue y plantillas de variables de entorno.
e) La documentación técnica de arquitectura, modelo de datos y demás documentación asociada directamente al código fuente.

### Parágrafo Segundo — Proyectos de Fase Única

Cuando el objeto del contrato se ejecute como una sola fase o implementación, con independencia de que el precio se pague en uno o varios contados según el calendario definido en la CLÁUSULA TERCERA, la condición prevista en la presente cláusula se entenderá cumplida únicamente cuando se haya pagado la totalidad del valor del contrato. El pago parcial, aun cuando corresponda a la mayor parte del precio, no habilita la entrega parcial ni el acceso parcial a los elementos señalados en el PARÁGRAFO PRIMERO.

### Parágrafo Tercero — Proyectos Ejecutados por Fases

Cuando el objeto del contrato se ejecute en dos o más fases, la condición prevista en la presente cláusula se entenderá cumplida únicamente cuando se hayan ejecutado todas las fases y pagado la totalidad del valor del contrato. En consecuencia, la aceptación de una fase conforme al PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA y el pago de esa fase no generan, por sí solos, derecho a la entrega del código fuente ni al acceso a los repositorios correspondientes a esa fase ni a las fases anteriores.

### Parágrafo Cuarto — Efectos sobre la Ejecución y la Aceptación

La condición establecida en la presente cláusula no afecta las demás obligaciones de EL CONTRATISTA. En particular:

1. El producto software permanecerá desplegado y operativo en el ambiente de producción, de modo que EL CONTRATANTE pueda usarlo conforme a la licencia temporal prevista en el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA.
2. La revisión y aceptación de los entregables conforme al PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA se realizará sobre el producto software desplegado y en funcionamiento, sin que ello requiera la entrega del código fuente ni el acceso a los repositorios.
3. Se mantiene el acceso de solo lectura al servidor previsto en el numeral 8 del PARÁGRAFO SÉPTIMO de la CLÁUSULA SEGUNDA, para efectos de consulta, verificación y auditoría.
4. La garantía prevista en el PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA se causa desde la aceptación del entregable final, con independencia del momento en que se produzca la entrega del código fuente.
5. La retención prevista en la presente cláusula no constituye incumplimiento contractual por parte de EL CONTRATISTA, en concordancia con el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SÉPTIMA, ni causa mora ni genera indemnización alguna a favor de EL CONTRATANTE.

### Parágrafo Quinto — Entrega una vez Cumplida la Condición

Acreditado el pago del cien por ciento (100%) del valor total del contrato, EL CONTRATISTA dispondrá de cinco (5) días hábiles, contados a partir del día siguiente a la confirmación del pago final, para:

a) Entregar el código fuente del producto software y la documentación técnica asociada.
b) Otorgar a EL CONTRATANTE el acceso a los repositorios del proyecto y transferir su titularidad o administración, según lo acuerden las partes.
c) Suscribir el acta de entrega final correspondiente.

La entrega se notificará conforme a la CLÁUSULA DÉCIMA QUINTA y se documentará mediante acta de entrega, momento a partir del cual operará de pleno derecho la cesión de derechos prevista en la CLÁUSULA DÉCIMA.

### Parágrafo Sexto — Terminación Anticipada

En caso de terminación anticipada del contrato conforme a la CLÁUSULA DÉCIMA SEXTA, la condición prevista en la presente cláusula se entenderá cumplida cuando EL CONTRATANTE haya pagado la totalidad de las sumas liquidadas a su cargo conforme al parágrafo aplicable de dicha cláusula. Acreditado dicho pago, EL CONTRATISTA entregará el código fuente y otorgará el acceso a los repositorios respecto del trabajo efectivamente pagado, dentro del plazo establecido en el PARÁGRAFO QUINTO de la presente cláusula.

### Parágrafo Séptimo — Prohibición de Elusión

EL CONTRATANTE se abstendrá de obtener, intentar obtener, copiar, descompilar, extraer o reproducir el código fuente del producto software por medios distintos a los previstos en la presente cláusula, sea directamente o a través de terceros. El incumplimiento de esta obligación constituirá incumplimiento grave del contrato y facultará a EL CONTRATISTA para darlo por terminado conforme a la CLÁUSULA DÉCIMA SEXTA, sin perjuicio de las acciones legales a que haya lugar."""


TEMPORARY_LICENSE_PARAGRAPH = """\
### Parágrafo Tercero — Licencia Temporal de Uso

Mientras no se cumpla la condición suspensiva establecida en la CLÁUSULA NOVENA, y siempre que EL CONTRATANTE se encuentre al día en sus obligaciones de pago conforme a la CLÁUSULA TERCERA, EL CONTRATISTA otorga a EL CONTRATANTE una licencia de uso temporal, revocable, no exclusiva e intransferible sobre el producto software desplegado, limitada a su uso y operación en el ambiente de producción para los fines propios del negocio de EL CONTRATANTE.

Esta licencia temporal no comprende, y EL CONTRATANTE se abstendrá de ejercer, los derechos de reproducción, modificación, transformación, adaptación, distribución, comercialización, sublicenciamiento o cesión a terceros, ni el encargo a terceros de desarrollos derivados del producto software.

La licencia temporal se extinguirá automáticamente en cualquiera de los siguientes eventos:

a) Al cumplirse la condición suspensiva establecida en la CLÁUSULA NOVENA, momento en el cual operará la cesión plena de derechos prevista en la presente cláusula.
b) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario, conforme al literal a) del PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SEXTA.
c) Por terminación del contrato sin que EL CONTRATANTE haya cumplido la totalidad de sus obligaciones de pago."""


# ---------------------------------------------------------------------------
# Replacement pairs, in the order they must be applied
# ---------------------------------------------------------------------------

# Step 1 — body cross-references to clauses that shift. Each anchor carries
# enough surrounding words that it can never match a `## CLÁUSULA` heading,
# nor the output of a sibling pair when the list is replayed in reverse.
CROSS_REFERENCE_PAIRS = [
    (
        'definido en la CLÁUSULA DÉCIMA CUARTA.',
        'definido en la CLÁUSULA DÉCIMA QUINTA.',
    ),
    (
        'definido en la CLÁUSULA DÉCIMA CUARTA, incluyendo los detalles necesarios',
        'definido en la CLÁUSULA DÉCIMA QUINTA, incluyendo los detalles necesarios',
    ),
    (
        'conforme a lo establecido en la CLÁUSULA DÉCIMA QUINTA, sin perjuicio',
        'conforme a lo establecido en la CLÁUSULA DÉCIMA SEXTA, sin perjuicio',
    ),
    (
        'sujeto a los límites establecidos en la CLÁUSULA DÉCIMA NOVENA.',
        'sujeto a los límites establecidos en la CLÁUSULA VIGÉSIMA.',
    ),
]

# Step 2 — clause headings shift by one from the tenth onwards. The full title
# is part of every anchor, so no rename can be re-matched by another pair.
HEADING_PAIRS = [
    (
        '## CLÁUSULA DÉCIMA — CONFIDENCIALIDAD',
        '## CLÁUSULA DÉCIMA PRIMERA — CONFIDENCIALIDAD',
    ),
    (
        '## CLÁUSULA DÉCIMA PRIMERA — PROTECCIÓN Y TRATAMIENTO DE DATOS PERSONALES',
        '## CLÁUSULA DÉCIMA SEGUNDA — PROTECCIÓN Y TRATAMIENTO DE DATOS PERSONALES',
    ),
    (
        '## CLÁUSULA DÉCIMA SEGUNDA — MODIFICACIONES',
        '## CLÁUSULA DÉCIMA TERCERA — MODIFICACIONES',
    ),
    (
        '## CLÁUSULA DÉCIMA TERCERA — ACUERDO',
        '## CLÁUSULA DÉCIMA CUARTA — ACUERDO',
    ),
    (
        '## CLÁUSULA DÉCIMA CUARTA — NOTIFICACIÓN',
        '## CLÁUSULA DÉCIMA QUINTA — NOTIFICACIÓN',
    ),
    (
        '## CLÁUSULA DÉCIMA QUINTA — TERMINACIÓN ANTICIPADA',
        '## CLÁUSULA DÉCIMA SEXTA — TERMINACIÓN ANTICIPADA',
    ),
    (
        '## CLÁUSULA DÉCIMA SEXTA — INCUMPLIMIENTO',
        '## CLÁUSULA DÉCIMA SÉPTIMA — INCUMPLIMIENTO',
    ),
    (
        '## CLÁUSULA DÉCIMA SÉPTIMA — RESOLUCIÓN DE CONFLICTOS',
        '## CLÁUSULA DÉCIMA OCTAVA — RESOLUCIÓN DE CONFLICTOS',
    ),
    (
        '## CLÁUSULA DÉCIMA OCTAVA — MÉRITO EJECUTIVO',
        '## CLÁUSULA DÉCIMA NOVENA — MÉRITO EJECUTIVO',
    ),
    (
        '## CLÁUSULA DÉCIMA NOVENA — LIMITACIÓN DE RESPONSABILIDAD',
        '## CLÁUSULA VIGÉSIMA — LIMITACIÓN DE RESPONSABILIDAD',
    ),
]

# Step 3 — insert the new blocks and harmonize the provisions that promised an
# unconditional source-code delivery. The inserted text already uses the final
# clause numbers, which is why it runs after steps 1 and 2.
INSERTION_PAIRS = [
    # Scope paragraph, appended to Cláusula Segunda right before Cláusula Tercera.
    (
        '3. Una vez confirmado el pago correspondiente, se dará inicio al siguiente '
        'periodo de desarrollo conforme al cronograma definido en el Documento '
        'Propuesta Comercial.\n\n---\n\n## CLÁUSULA TERCERA — PRECIO Y FORMA DE PAGO',
        '3. Una vez confirmado el pago correspondiente, se dará inicio al siguiente '
        'periodo de desarrollo conforme al cronograma definido en el Documento '
        'Propuesta Comercial.\n\n' + SCOPE_PARAGRAPH
        + '\n\n---\n\n## CLÁUSULA TERCERA — PRECIO Y FORMA DE PAGO',
    ),
    # New Cláusula Novena, inserted just before the intellectual property clause,
    # which shifts to Cláusula Décima in the same move.
    (
        '## CLÁUSULA NOVENA — DERECHOS PATRIMONIALES Y DERECHOS DE EXPLOTACIÓN',
        SOURCE_CODE_CLAUSE
        + '\n\n---\n\n## CLÁUSULA DÉCIMA — DERECHOS PATRIMONIALES Y DERECHOS DE EXPLOTACIÓN',
    ),
    # The assignment of rights becomes conditional on full payment.
    (
        'En virtud del presente contrato, EL CONTRATANTE adquiere,',
        'En virtud del presente contrato, y sujeto al cumplimiento de la condición '
        'suspensiva establecida en la CLÁUSULA NOVENA, EL CONTRATANTE adquiere,',
    ),
    (
        'Estos derechos se transfieren de manera permanente desde el momento de la '
        'entrega y aceptación del software, con excepción',
        'Estos derechos se transfieren de manera permanente y de pleno derecho a partir '
        'del momento en que EL CONTRATANTE acredite el pago del cien por ciento (100%) '
        'del valor total del presente contrato, conforme a la condición suspensiva '
        'establecida en la CLÁUSULA NOVENA, con excepción',
    ),
    (
        'sin que ello genere derecho a contraprestación adicional, siempre que se encuentre al día',
        'sin que ello genere derecho a contraprestación adicional, una vez cumplida la '
        'condición suspensiva establecida en la CLÁUSULA NOVENA y siempre que se encuentre al día',
    ),
    # Temporary use licence, appended at the end of the intellectual property clause.
    (
        'sin que esta licencia se extienda a su comercialización como productos '
        'independientes.\n\n---\n\n## CLÁUSULA DÉCIMA PRIMERA — CONFIDENCIALIDAD',
        'sin que esta licencia se extienda a su comercialización como productos '
        'independientes.\n\n' + TEMPORARY_LICENSE_PARAGRAPH
        + '\n\n---\n\n## CLÁUSULA DÉCIMA PRIMERA — CONFIDENCIALIDAD',
    ),
    # Provisions that previously promised delivery without any condition.
    (
        '6. **Entrega:** Entrega formal del código fuente, documentación técnica y '
        'demás entregables definidos en el Documento Propuesta Comercial.',
        '6. **Entrega:** Entrega formal del código fuente, documentación técnica y '
        'demás entregables definidos en el Documento Propuesta Comercial, sujeta a '
        'la condición establecida en la CLÁUSULA NOVENA.',
    ),
    (
        'c) Entregar el código fuente, la documentación técnica y los demás entregables '
        'conforme a lo establecido en el Documento Propuesta Comercial.',
        'c) Entregar el código fuente, la documentación técnica y los demás entregables '
        'conforme a lo establecido en el Documento Propuesta Comercial, en los términos '
        'y bajo la condición establecida en la CLÁUSULA NOVENA.',
    ),
]

FORWARD_PAIRS = CROSS_REFERENCE_PAIRS + HEADING_PAIRS + INSERTION_PAIRS


def apply_pairs(markdown, pairs):
    """Apply (old, new) replacements in order.

    A missing anchor is skipped rather than raising, so a manually edited
    template does not block the deploy — but it is logged, because a silent
    skip is exactly how a half-applied renumbering would slip through.
    """
    for old, new in pairs:
        if old in markdown:
            markdown = markdown.replace(old, new)
        else:
            logger.warning('Contract template v5: anchor not found, skipped: %r', old[:80])
    return markdown


def _update_default_template(apps, pairs):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    template = ContractTemplate.objects.filter(is_default=True).first()
    if not template:
        return
    updated = apply_pairs(template.content_markdown, pairs)
    if updated != template.content_markdown:
        template.content_markdown = updated
        template.save(update_fields=['content_markdown'])


def update_default_template(apps, schema_editor):
    _update_default_template(apps, FORWARD_PAIRS)


def revert_default_template(apps, schema_editor):
    _update_default_template(apps, [(new, old) for old, new in reversed(FORWARD_PAIRS)])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0164_pocket_draws_to_company_ledger'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
