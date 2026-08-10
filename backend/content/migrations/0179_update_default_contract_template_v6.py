# Generated 2026-08-10 — update default contract template v6:
#   1. Hosting, maintenance & support service terms (new cl. 21).
#   2. Incident levels, report protocol and continuity commitments (new cl. 22),
#      including the service liability cap tied to the subscription period.
#   3. Infrastructure capacity, consumption monitoring and escalation (new cl. 23).
#   4. Staged 90-day late-payment protocol with ordered exit (new cl. 24).
#   5. Warranty reports now follow the structured incident report protocol.
#   6. Source-code custody also covers financed balances and deferred payments.
#
# This is a PATCH migration, in the style of 0165 (v5), and deliberately not a
# full-template replacement: v5 introduced the CLÁUSULA NOVENA source-code
# custody clause, the "Parágrafo Décimo — Alcance del Trabajo Contratado" and
# the 9-19 -> 10-20 renumbering by patching the stored markdown. Rewriting the
# whole template here would silently revert all of it.
#
# Because v5 shifted every clause from the tenth onwards, the four new clauses
# are numbered 21-24 (not 20-23) and their cross-references target the post-v5
# numbering: notificación = DÉCIMA QUINTA, terminación anticipada = DÉCIMA
# SEXTA, incumplimiento = DÉCIMA SÉPTIMA, limitación de responsabilidad =
# VIGÉSIMA, datos personales = DÉCIMA SEGUNDA.
#
# NOTE: for deals with financed balances, a cumulative hosting penalty per
# unpaid installment (see Vastago Otrosi No. 1, cl. 4) may be added per-deal
# via custom contract or otrosi — intentionally NOT part of this default.

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# New text blocks
# ---------------------------------------------------------------------------

HOSTING_SERVICE_CLAUSES = """\
## CLÁUSULA VIGÉSIMA PRIMERA — SERVICIO DE HOSTING, MANTENIMIENTO Y SOPORTE

Las CLÁUSULAS VIGÉSIMA PRIMERA a VIGÉSIMA CUARTA aplican únicamente cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte del producto software, cuyo valor, periodicidad y condiciones económicas se definen en el Documento Propuesta Comercial o en el documento que las partes suscriban para el efecto. Este servicio comprende la operación de la plataforma en el ambiente de producción, su mantenimiento técnico y el soporte ante incidentes, dentro de la capacidad de infraestructura descrita en la CLÁUSULA VIGÉSIMA TERCERA.

### Parágrafo Primero — Inicio del Cobro

El cobro del servicio se causa únicamente a partir de la fecha de puesta en producción del producto software, entendida como el momento en que este queda desplegado y disponible en vivo para la operación de EL CONTRATANTE, fecha que las partes harán constar por escrito. Antes de esa fecha no se causará cobro alguno por este concepto, y el primer periodo del servicio se contará a partir de ella.

### Parágrafo Segundo — Forma y Fecha de Pago

El servicio se paga por periodos anticipados, conforme a la periodicidad definida en el Documento Propuesta Comercial. EL CONTRATISTA remitirá la cuenta de cobro o factura con una antelación no inferior a diez (10) días calendario al inicio de cada periodo, y EL CONTRATANTE la pagará dentro de los cinco (5) primeros días calendario del periodo que se inicia. El pago se entenderá realizado únicamente cuando los recursos hayan sido recibidos efectivamente por EL CONTRATISTA. La mora en el pago del servicio activa el protocolo previsto en la CLÁUSULA VIGÉSIMA CUARTA.

### Parágrafo Tercero — Reajuste Anual del Valor del Servicio

El valor del servicio se reajustará automáticamente cada primero (1.º) de enero, aplicando al valor vigente del año inmediatamente anterior el porcentaje en que el Gobierno Nacional haya incrementado el salario mínimo mensual legal vigente (SMMLV) para ese año. Si para un año determinado no se decretare incremento del SMMLV, el reajuste se calculará con la variación anual del Índice de Precios al Consumidor (IPC) certificada por el DANE para el año inmediatamente anterior. El valor así reajustado constituye el valor vigente del servicio para todos los efectos del presente contrato. Las partes reconocen que este reajuste no constituye un incremento del precio ni un cobro adicional, sino un mecanismo de corrección monetaria destinado a conservar el valor real de la contraprestación, dado que los costos que sostienen la operación del servicio se incrementan anualmente cuando menos en la misma proporción.

### Parágrafo Cuarto — Responsabilidad Operativa

Durante la vigencia del servicio, EL CONTRATISTA tendrá la responsabilidad de mantener la plataforma operativa dentro de las condiciones técnicas contratadas, siempre que se cumplan todas las siguientes condiciones: (i) EL CONTRATANTE se encuentre al día en sus pagos; (ii) el servicio se encuentre activo y vigente; (iii) no existan intervenciones de terceros no autorizados sobre el código, la infraestructura o los ambientes del producto; (iv) EL CONTRATANTE entregue oportunamente la información, accesos, aprobaciones y recursos necesarios; (v) la operación se desarrolle dentro de la capacidad de infraestructura prevista en la CLÁUSULA VIGÉSIMA TERCERA; y (vi) no se presenten los eventos descritos en el PARÁGRAFO SÉPTIMO de la CLÁUSULA VIGÉSIMA SEGUNDA.

---

## CLÁUSULA VIGÉSIMA SEGUNDA — ATENCIÓN DE INCIDENTES, NIVELES DE SERVICIO Y CONTINUIDAD OPERATIVA

### Parágrafo Primero — Definiciones Operativas

Para todos los efectos del presente contrato, las partes adoptan las siguientes definiciones:

1. **Día hábil:** el comprendido de lunes a viernes, con exclusión de sábados, domingos y días festivos de la República de Colombia conforme a la Ley 51 de 1983 y las normas que la modifiquen.
2. **Hora hábil:** la comprendida entre las nueve (9:00) y las dieciséis (16:00) horas, hora de Bogotá D.C., de un día hábil. Los plazos expresados en horas hábiles corren únicamente dentro de esa franja y se reanudan al inicio de la franja hábil siguiente.
3. **Protocolo de reporte de incidentes:** todo reporte se remitirá por el medio de notificación de la CLÁUSULA DÉCIMA QUINTA e incluirá, en el cuerpo del mensaje o en documento adjunto: a) título corto que identifique el problema; b) dirección (URL) de la página en la que inició la operación; c) dirección (URL) de la página en la que se presentó el problema, si es distinta de la anterior; d) pasos realizados, enumerados en orden; e) lo que ocurrió, con el mensaje de error exacto o una captura de pantalla; f) lo que se esperaba que ocurriera; g) dispositivo y navegador utilizados; y h) fecha y hora aproximada del suceso. Para el cómputo de los plazos, y en concordancia con la CLÁUSULA DÉCIMA QUINTA, el reporte se entenderá recibido al inicio de la franja hábil del día hábil siguiente al de su envío; el reporte que no reúna la información señalada no dará inicio al cómputo sino desde el momento en que sea completado.
4. **Restablecimiento:** se entenderá restablecido el servicio cuando la operación se reanude, aun mediante solución temporal, alternativa o parcial que permita continuar la operación de EL CONTRATANTE. La corrección definitiva de la causa raíz podrá adelantarse con posterioridad, sin que por ello subsista el incidente ni se entienda incumplido el plazo de resolución.
5. **Ventana de mantenimiento programado:** la interrupción planificada del servicio para actualizaciones, parches o labores de mantenimiento, informada a EL CONTRATANTE con una antelación no inferior a veinticuatro (24) horas. No constituye indisponibilidad, incidente ni incumplimiento.

### Parágrafo Segundo — Compromisos Permanentes de Operación

Mientras el servicio de hosting, mantenimiento y soporte se encuentre vigente, EL CONTRATISTA mantendrá sobre la plataforma: (i) monitoreo automatizado y permanente de su disponibilidad, con alertamiento independiente ante la falta de respuesta del servidor; (ii) copias de seguridad periódicas de la base de datos y copia integral del sistema, con retención no inferior a treinta (30) días y pruebas periódicas de restauración; (iii) aplicación de actualizaciones de seguridad y parches del sistema operativo y de los componentes de la plataforma; (iv) vigencia de los certificados de seguridad (SSL/TLS) del dominio de operación; y (v) notificación de los incidentes de seguridad conforme a la CLÁUSULA DÉCIMA SEGUNDA, dentro de las veinticuatro (24) horas siguientes a su conocimiento. Estos mecanismos corresponden a las prácticas operativas vigentes de EL CONTRATISTA, quien podrá sustituirlos o actualizarlos por otros de alcance equivalente o superior sin que ello requiera modificación del presente contrato.

### Parágrafo Tercero — Naturaleza de la Obligación

Las obligaciones de EL CONTRATISTA en materia de operación, atención de incidentes y soporte son obligaciones de medio y no de resultado: comprometen la diligencia debida, los medios técnicos descritos y los tiempos de atención pactados, y no un porcentaje de disponibilidad garantizado ni la ausencia de fallas. Las partes reconocen que ningún sistema informático opera libre de interrupciones, y que el valor del servicio retribuye la operación diligente dentro de ese marco y no el aseguramiento de resultados económicos de EL CONTRATANTE o de terceros.

### Parágrafo Cuarto — Niveles de Atención

Durante la vigencia del servicio de hosting, mantenimiento y soporte, los incidentes se atenderán conforme a los siguientes niveles de prioridad:

| Nivel | Descripción del incidente | Respuesta | Resolución |
|---|---|---|---|
| CRÍTICO | Sistema caído, pérdida de datos o acceso completamente bloqueado | 4 horas hábiles | 1 día hábil |
| MEDIO | Funcionalidad importante degradada o con comportamiento incorrecto, pero el sistema sigue operando | 1 día hábil | 5 días hábiles |
| BAJO | Error menor, visual o de usabilidad, sin impacto operativo significativo | 3 días hábiles | 9 días hábiles |

Para el cómputo de estos plazos: (i) el plazo de respuesta se cuenta desde que el reporte completo se entiende recibido conforme al numeral 3 del PARÁGRAFO PRIMERO; (ii) el plazo de resolución se cuenta desde el momento en que se surte la respuesta; (iii) ambos corren exclusivamente en horas y días hábiles; y (iv) la clasificación inicial del nivel corresponde a EL CONTRATISTA conforme a la descripción de la tabla, y podrá ser reclasificada de forma motivada cuando el diagnóstico así lo determine. Fuera de la franja hábil, EL CONTRATISTA atenderá los incidentes de nivel CRÍTICO en la medida de la disponibilidad de su equipo técnico, sin que ello constituya compromiso de tiempo ni genere obligación exigible; el monitoreo automatizado del PARÁGRAFO SEGUNDO opera de manera permanente. En ausencia del servicio de hosting, mantenimiento y soporte, la atención de defectos se rige exclusivamente por los plazos de la garantía previstos en el PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA.

### Parágrafo Quinto — Protocolo de Atención de Incidentes Críticos

Reportado un incidente de nivel CRÍTICO, EL CONTRATISTA aplicará el siguiente protocolo: 1) **Recepción y clasificación**, dentro del plazo de respuesta: acuse de recibo, clasificación del nivel de prioridad y asignación del responsable técnico; 2) **Diagnóstico y contención**, durante el curso de la atención: identificación de la causa probable, medidas de contención y estimación del restablecimiento, con informe de estado por escrito a EL CONTRATANTE; 3) **Restablecimiento**, dentro del plazo de resolución o de su prórroga, en los términos del numeral 4 del PARÁGRAFO PRIMERO; y 4) **Informe de cierre**, dentro de los cinco (5) días hábiles siguientes al restablecimiento, con la causa raíz, las acciones ejecutadas y las medidas preventivas adoptadas. El informe de cierre constituye para EL CONTRATANTE la constancia escrita de la atención prestada y para EL CONTRATISTA la acreditación del cumplimiento de sus obligaciones respecto de ese incidente.

### Parágrafo Sexto — Prórroga y Suspensión de los Plazos

Cuando por la naturaleza, la complejidad o el origen del incidente la resolución no resulte alcanzable dentro del plazo previsto, EL CONTRATISTA lo informará por escrito a EL CONTRATANTE antes de su vencimiento, señalando la causa y la nueva fecha estimada de restablecimiento, y el plazo se entenderá prorrogado por el término allí indicado, el cual deberá ser razonable y proporcional a la causa invocada; comunicada la prórroga en estos términos, no habrá incumplimiento del plazo original. Asimismo, los plazos de respuesta y de resolución se suspenden, y se reanudan al cesar la causa, mientras subsista: (i) la espera de información, accesos, credenciales, aprobaciones o decisiones a cargo de EL CONTRATANTE; (ii) la ocurrencia de cualquiera de los eventos del PARÁGRAFO SÉPTIMO; (iii) la imposibilidad de reproducir el incidente por insuficiencia de la información reportada; o (iv) la vigencia de las etapas del protocolo previsto en la CLÁUSULA VIGÉSIMA CUARTA, en cuanto a los servicios allí suspendidos.

### Parágrafo Séptimo — Exclusiones, Fuerza Mayor y Caso Fortuito

EL CONTRATISTA no responderá, y no se entenderán incumplidos los compromisos de esta cláusula, cuando la indisponibilidad, la degradación, la demora o el daño obedezcan a fuerza mayor o caso fortuito en los términos del artículo 64 del Código Civil, subrogado por el artículo 1.º de la Ley 95 de 1890, o a circunstancias ajenas a su control razonable, quedando comprendidos, de manera enunciativa y no taxativa: (i) fallas, interrupciones, degradación o suspensión del servicio del proveedor de infraestructura, del centro de datos, de la red o del suministro de energía; (ii) interrupciones de conectividad ajenas a la infraestructura administrada por EL CONTRATISTA, incluidas las de los equipos, redes o dispositivos de EL CONTRATANTE; (iii) ataques informáticos, accesos no autorizados o actos maliciosos de terceros, pese a la adopción de medidas de seguridad razonables; (iv) indisponibilidad, cambios o fallas de servicios de terceros integrados a la plataforma, incluidos los de autoridades tributarias, proveedores de facturación electrónica, pasarelas de pago y proveedores de correo electrónico; (v) actos de autoridad, cambios normativos, desastres naturales, conmoción interna, huelgas o paros ajenos a EL CONTRATISTA; (vi) intervención de terceros no autorizados sobre el código, la infraestructura o los ambientes del producto; (vii) uso de la plataforma fuera de las condiciones contratadas, o datos, cargas o configuraciones provistos por EL CONTRATANTE; y (viii) insuficiencia de los recursos de infraestructura en los términos de la CLÁUSULA VIGÉSIMA TERCERA. Durante la ocurrencia de estos eventos se suspenden los plazos y la responsabilidad operativa de EL CONTRATISTA, quien informará la situación a EL CONTRATANTE y desplegará los esfuerzos razonables a su alcance para mitigar sus efectos. Cuando la normalización del servicio dependa de un tercero, los tiempos y las fechas estimadas de restablecimiento quedarán sujetos a los de dicho tercero; EL CONTRATISTA lo informará así a EL CONTRATANTE, hará el seguimiento correspondiente y documentará la causa raíz, las fechas y la solución aplicada en el informe de cierre previsto en el PARÁGRAFO QUINTO. Lo anterior es concordante y acumulativo con las condiciones y exclusiones de la garantía y con la CLÁUSULA VIGÉSIMA.

### Parágrafo Octavo — Responsabilidad frente a Clientes y Usuarios Finales

EL CONTRATISTA no tiene relación contractual alguna con los clientes, usuarios o terceros de EL CONTRATANTE: es EL CONTRATANTE quien contrata con ellos, define sus condiciones comerciales, asume sus compromisos de servicio y responde frente a ellos. En consecuencia, EL CONTRATANTE es el único responsable frente a sus clientes y usuarios finales por la prestación de sus propios servicios, y mantendrá indemne a EL CONTRATISTA de cualquier reclamación, demanda, sanción o requerimiento que aquellos formulen, así como de los costos de defensa que ello le irrogue, salvo en los casos de dolo o culpa grave de EL CONTRATISTA.

### Parágrafo Noveno — Límite de Responsabilidad del Servicio

En ningún caso EL CONTRATISTA responderá por lucro cesante, pérdida de ingresos, de ventas, de negocio o de clientela, daño reputacional, ni por daños indirectos, imprevisibles o consecuenciales de EL CONTRATANTE o de terceros, derivados de la prestación o de la interrupción del servicio de hosting, mantenimiento y soporte, en concordancia con el artículo 1616 del Código Civil. La responsabilidad total y agregada de EL CONTRATISTA por toda reclamación derivada de dicho servicio no excederá el valor efectivamente pagado por EL CONTRATANTE por el último periodo de suscripción del servicio contratado —conforme a la periodicidad definida en el Documento Propuesta Comercial, sea esta mensual, trimestral, semestral, anual u otra— inmediatamente anterior al hecho que la origine; cuando aún no se hubiere pagado un periodo completo del servicio, el límite será el valor vigente de un (1) periodo de suscripción del servicio. Este límite no aplica en los casos de dolo o culpa grave de EL CONTRATISTA, ni respecto de las obligaciones de confidencialidad y de protección de datos personales, conforme a los artículos 63 y 1522 del Código Civil. En lo no previsto en este parágrafo, rige la CLÁUSULA VIGÉSIMA.

---

## CLÁUSULA VIGÉSIMA TERCERA — RECURSOS DE INFRAESTRUCTURA, CAPACIDAD OPERATIVA Y ESCALAMIENTO

El servicio de hosting se presta sobre la infraestructura cuya capacidad técnica se describe en el Documento Propuesta Comercial. El valor del servicio retribuye la operación, el mantenimiento y el soporte de la plataforma dentro de dicha capacidad; toda operación que la exceda requiere infraestructura de capacidad superior y no se encuentra comprendida en el valor pactado.

### Parágrafo Primero — Monitoreo y Reporte de Consumo

EL CONTRATISTA monitoreará de forma continua el consumo efectivo de procesamiento, memoria, almacenamiento y transferencia de datos, y entregará a EL CONTRATANTE un reporte de consumo con cada periodo de facturación del servicio, así como cada vez que este lo solicite por escrito.

### Parágrafo Segundo — Alerta Temprana

Cuando el consumo de cualquiera de los recursos supere el ochenta por ciento (80%) de su capacidad de forma sostenida durante siete (7) días calendario, EL CONTRATISTA lo notificará a EL CONTRATANTE de manera formal y por escrito, acompañando la evidencia técnica de la medición y una propuesta de escalamiento de la infraestructura, con su especificación técnica y su costo.

### Parágrafo Tercero — Decisión y Costo del Escalamiento

EL CONTRATANTE dispondrá de quince (15) días hábiles, contados desde la notificación anterior, para aprobar por escrito el escalamiento propuesto. La provisión oportuna de los recursos que la operación de su negocio demande es una obligación de EL CONTRATANTE. Aprobado el escalamiento, EL CONTRATISTA contratará y administrará la infraestructura ampliada; el mayor costo se trasladará a EL CONTRATANTE y se facturará de manera separada, sin perjuicio del ajuste del valor del servicio que las partes acuerden por escrito por el mayor esfuerzo operativo.

### Parágrafo Cuarto — Exoneración por Insuficiencia de Recursos

Vencido el plazo del parágrafo anterior sin que EL CONTRATANTE haya aprobado el escalamiento, EL CONTRATISTA quedará exonerado de toda responsabilidad por la degradación del rendimiento, la lentitud, la indisponibilidad, la interrupción del servicio o la pérdida de datos atribuibles a la insuficiencia de los recursos de infraestructura, y quedarán suspendidos los niveles de atención de la CLÁUSULA VIGÉSIMA SEGUNDA mientras persista dicha condición, sin que ello constituya incumplimiento imputable a EL CONTRATISTA ni dé lugar a indemnización, descuento o reclamación en su contra. Esta exoneración opera únicamente si EL CONTRATISTA ha cumplido los deberes de monitoreo, reporte y notificación oportuna de los PARÁGRAFOS PRIMERO y SEGUNDO: EL CONTRATISTA responde por medir, advertir y proponer a tiempo; EL CONTRATANTE, por proveer los recursos que su operación demande.

### Parágrafo Quinto — Crecimiento por Nuevos Desarrollos

La incorporación de nuevas fases, módulos o funcionalidades al producto puede incrementar el consumo de recursos. El dimensionamiento de la infraestructura necesaria para soportarlos se evaluará dentro del alcance de cada nuevo desarrollo, conforme al procedimiento de esta cláusula.

---

## CLÁUSULA VIGÉSIMA CUARTA — PROTOCOLO DE MORA Y SUSPENSIÓN DEL SERVICIO

En caso de mora en las obligaciones de pago del servicio de hosting, mantenimiento y soporte, EL CONTRATISTA aplicará el siguiente protocolo escalonado, que constituye el único procedimiento por el cual puede suspenderse la operación de la plataforma por causa de dicha mora. Los plazos se cuentan en días calendario de mora, desde el día siguiente al vencimiento del plazo de pago:

| Etapa | Día de mora | Actuación de EL CONTRATISTA | Efecto sobre la operación |
|---|---|---|---|
| 1 — Aviso | Día 1 | Aviso formal de mora al medio de notificación de EL CONTRATANTE, con el detalle de la obligación vencida y los intereses causados | Ninguno. Todos los servicios continúan con normalidad |
| 2 — Suspensión de evolución | Día 30 | Suspensión del desarrollo de nuevas funcionalidades, de los desarrollos evolutivos, de las actualizaciones y del soporte no crítico | La plataforma sigue operando. Se conservan disponibilidad, copias de seguridad y atención de incidentes CRÍTICOS |
| 3 — Suspensión de servicios | Día 60 | Suspensión del mantenimiento y del soporte, conservando únicamente la disponibilidad de la plataforma y las copias de seguridad. Remisión del preaviso formal de suspensión de la operación | La plataforma sigue operando |
| 4 — Vencimiento del plazo de cura | Día 90 | EL CONTRATISTA queda facultado para suspender la operación de la plataforma, previo aviso escrito con quince (15) días calendario de antelación, y para dar por terminado el servicio o el contrato conforme a la CLÁUSULA DÉCIMA SEXTA | Agotado el preaviso, cesa la operación |

### Parágrafo Primero — Continuidad Durante el Periodo de Cura

Durante las etapas 1, 2 y 3 del protocolo —los primeros noventa (90) días calendario de mora— lo que se suspende es la evolución, el soporte y el mantenimiento, y nunca el uso operativo del producto ya desplegado. EL CONTRATISTA reconoce que la operación de EL CONTRATANTE, y la de los clientes de este cuando los tenga, dependen de la continuidad de la plataforma, y asume el compromiso de no interrumpirla dentro del periodo de cura.

### Parágrafo Segundo — Plazo Máximo de Cura y Obligaciones Durante la Mora

El plazo máximo para normalizar los pagos es de noventa (90) días calendario contados desde el primer día de mora; la mora en varias obligaciones simultáneas no lo amplía, y el plazo se cuenta desde la primera obligación impagada que permanezca sin pago. El transcurso del protocolo no suspende la causación de las obligaciones económicas: los periodos del servicio que se inicien durante el protocolo se causan y se facturan íntegramente, por cuanto el servicio continúa prestándose, y los intereses de mora se causan de manera independiente sobre cada obligación incumplida. El periodo de cura es un término de tolerancia operativa y no constituye condonación, aplazamiento ni novación de las obligaciones de EL CONTRATANTE.

### Parágrafo Tercero — Reanudación

Pagada la totalidad de las obligaciones vencidas junto con sus intereses, EL CONTRATISTA reanudará los servicios suspendidos dentro de los cinco (5) días hábiles siguientes a la verificación del pago, y el protocolo se entenderá agotado sin efectos ulteriores.

### Parágrafo Cuarto — Salida Ordenada

Si se llegare a la suspensión de la operación prevista en la etapa 4, EL CONTRATISTA entregará a EL CONTRATANTE, dentro del preaviso de quince (15) días calendario, una exportación completa de sus datos operativos alojados en la plataforma, en formato estándar de intercambio, y los conservará por treinta (30) días calendario adicionales antes de su eliminación definitiva. Esta salida ordenada no habilita la entrega del código fuente cuando existan saldos pendientes, conforme a la CLÁUSULA NOVENA y al PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SÉPTIMA, ni extingue las obligaciones económicas pendientes de EL CONTRATANTE.

### Parágrafo Quinto — Concordancia

Este protocolo rige la suspensión de la operación de la plataforma por mora en las obligaciones del servicio. Los intereses de mora previstos en la CLÁUSULA TERCERA, la suspensión y la terminación previstas en la CLÁUSULA DÉCIMA SEXTA para las obligaciones del desarrollo, y el derecho de retención de la CLÁUSULA DÉCIMA SÉPTIMA conservan su aplicación en sus propios ámbitos."""


HOSTING_SERVICE_POINTER = """\
9. Cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte, dicho servicio se regirá por las CLÁUSULAS VIGÉSIMA PRIMERA a VIGÉSIMA CUARTA del presente contrato y por las condiciones económicas definidas en el Documento Propuesta Comercial."""


# ---------------------------------------------------------------------------
# Replacement pairs, in the order they must be applied
# ---------------------------------------------------------------------------

# Every anchor below is the POST-v5 text: 0165 already rewrote the notification
# cross-reference in the warranty numeral (DÉCIMA CUARTA -> DÉCIMA QUINTA), so
# anchoring on the pre-v5 wording would silently skip the edit.
FORWARD_PAIRS = [
    # Warranty defect reports adopt the structured incident report protocol.
    (
        '3. EL CONTRATANTE deberá reportar los problemas detectados a través del '
        'medio de notificación definido en la CLÁUSULA DÉCIMA QUINTA, incluyendo '
        'los detalles necesarios para reproducir el problema: capturas de pantalla, '
        'descripción del error, pasos para replicarlo y cualquier información '
        'adicional que facilite su diagnóstico.',
        '3. EL CONTRATANTE deberá reportar los problemas detectados a través del '
        'medio de notificación definido en la CLÁUSULA DÉCIMA QUINTA, cumpliendo el '
        'protocolo de reporte de incidentes definido en el PARÁGRAFO PRIMERO de la '
        'CLÁUSULA VIGÉSIMA SEGUNDA. El reporte que no reúna la información allí '
        'señalada no dará inicio al cómputo de los plazos del presente parágrafo '
        'sino desde el momento en que sea completado.',
    ),
    # Pointer to the service clauses, appended to the hosting numerals of
    # Cláusula Segunda right before the exclusions paragraph.
    (
        'La ejecución de acciones no autorizadas activará lo dispuesto en el numeral '
        '7 del PARÁGRAFO SEXTO respecto a la pérdida de la garantía.\n\n'
        '### Parágrafo Octavo — Exclusiones',
        'La ejecución de acciones no autorizadas activará lo dispuesto en el numeral '
        '7 del PARÁGRAFO SEXTO respecto a la pérdida de la garantía.\n'
        + HOSTING_SERVICE_POINTER + '\n\n'
        '### Parágrafo Octavo — Exclusiones',
    ),
    # Source-code custody also covers financed balances and deferred payments.
    # Appended to the phased-projects paragraph of the v5 Cláusula Novena.
    (
        'el pago de esa fase no generan, por sí solos, derecho a la entrega del '
        'código fuente ni al acceso a los repositorios correspondientes a esa fase '
        'ni a las fases anteriores.',
        'el pago de esa fase no generan, por sí solos, derecho a la entrega del '
        'código fuente ni al acceso a los repositorios correspondientes a esa fase '
        'ni a las fases anteriores. Esta regla aplica igualmente cuando el esquema '
        'de pago contemple financiación, pagos diferidos o saldos exigibles con '
        'posterioridad a la entrega.',
    ),
    # The four service clauses, appended after the last clause of the contract.
    (
        'Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, '
        'sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones '
        'legales correspondientes en caso de que la reparación no sea satisfactoria '
        'o no se realice dentro del plazo establecido.',
        'Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, '
        'sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones '
        'legales correspondientes en caso de que la reparación no sea satisfactoria '
        'o no se realice dentro del plazo establecido.\n\n---\n\n'
        + HOSTING_SERVICE_CLAUSES,
    ),
]


def apply_pairs(markdown, pairs):
    """Apply (old, new) replacements in order.

    A missing anchor is skipped rather than raising, so a manually edited
    template does not block the deploy — but it is logged, because a silent
    skip is exactly how a half-applied change would slip through.
    """
    for old, new in pairs:
        if old in markdown:
            markdown = markdown.replace(old, new)
        else:
            logger.warning('Contract template v6: anchor not found, skipped: %r', old[:80])
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
        ('content', '0178_recurringpayment_custom_months_and_more'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
