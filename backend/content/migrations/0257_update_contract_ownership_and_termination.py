"""Refine software ownership, unilateral termination and hosting access terms.

Only the default template is patched. Coupled provisions change as a group,
so customized anchors cannot leave source delivery contradicting termination.
Existing PDFs, proposal-specific contracts and other templates are preserved.
"""

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


NEW_IP_OPENING = """\
En virtud del presente contrato y una vez cumplida la condición suspensiva establecida en la CLÁUSULA NOVENA, EL CONTRATANTE adquiere, de manera exclusiva, los derechos patrimoniales y de explotación sobre los desarrollos originales realizados específicamente para su proyecto dentro del alcance contratado, con las excepciones y reservas del PARÁGRAFO SEGUNDO de la presente cláusula. La cesión comprende los derechos de uso, reproducción, modificación, transformación, adaptación, distribución, comercialización, traducción, disposición, exportación, edición y comunicación pública de dichos desarrollos, por cualquier medio, sin restricción territorial y por todo el tiempo de protección legal conforme a la normatividad colombiana vigente. La incorporación de herramientas generales o de componentes propios reutilizables o de terceros no amplía el objeto de esta cesión."""

NEW_IP_RESERVATIONS = """\
### Parágrafo Segundo — Excepciones a la Cesión de Derechos

La cesión recae sobre la expresión original de los desarrollos específicos del proyecto y no confiere exclusividad sobre ideas, métodos, funcionalidades o soluciones técnicas generales. Quedan excluidos de la cesión:

a) Los activos preexistentes y los elementos propios de carácter general y reutilizable de EL CONTRATISTA que no hayan sido desarrollados exclusivamente para EL CONTRATANTE, incluidos plantillas, fragmentos de código (snippets), módulos generales, herramientas, librerías propias y marcos de trabajo.
b) Los componentes genéricos y reutilizables de autenticación, registros de actividad (logs), formularios, operaciones de creación, consulta, actualización y eliminación (CRUD), paginación y demás utilidades de aplicación general. Esta reserva no excluye de la cesión las implementaciones originales desarrolladas específicamente para el proyecto por el solo hecho de emplear dichos recursos o realizar esas funciones.
c) El conocimiento técnico (know-how), la experiencia acumulada, las habilidades y los conocimientos generales de EL CONTRATISTA y de su equipo, incluidos los adquiridos o perfeccionados durante la ejecución del contrato. Este acervo forma parte de su activo intelectual y podrá continuar utilizándose en otros proyectos, respetando la confidencialidad y los derechos sobre los desarrollos específicos de EL CONTRATANTE.
d) Los patrones de diseño, las arquitecturas estándar, las metodologías Agile/Scrum, las prácticas DevOps, las estructuras comunes de bases de datos y los algoritmos o procesos estándar de búsqueda, checkout, almacenamiento en caché (caching), colas y validaciones. Su utilización no otorga a ninguna de las partes exclusividad sobre tales ideas, métodos o conocimientos generales, sin perjuicio de los derechos que correspondan sobre implementaciones originales concretas.
e) Las librerías de código abierto (open source), los frameworks y los demás componentes de terceros, cuya titularidad permanecerá en cabeza de sus respectivos titulares y cuyo uso, modificación y distribución se regirán por las licencias aplicables. Su incorporación al producto no transfiere su propiedad a ninguna de las partes ni permite imponer restricciones contrarias a dichas licencias.

EL CONTRATISTA conservará los derechos que le correspondan sobre sus activos propios excluidos de la cesión. Una vez cumplida la condición suspensiva de la CLÁUSULA NOVENA, EL CONTRATANTE recibirá sobre los componentes propios descritos en los literales a) y b) que se incorporen al producto una licencia de uso perpetua, irrevocable, no exclusiva y sin costo adicional, que le permitirá utilizarlos, modificarlos e integrarlos dentro del producto software entregado y sus derivados, sin que esta licencia se extienda a su comercialización como productos independientes. Los componentes de terceros conservarán el régimen de sus propias licencias.

En consecuencia, EL CONTRATANTE adquirirá los derechos patrimoniales pactados sobre lo desarrollado específicamente para su proyecto, mientras EL CONTRATISTA conservará sus herramientas y activos reutilizables y no renunciará al conocimiento y experiencia de su equipo. Esta reserva no autoriza la divulgación de información confidencial, la reutilización de desarrollos específicos cedidos al cliente ni la apropiación de elementos que pertenezcan a terceros o sean de uso general."""

NEW_TERMINATION = """\
### Parágrafo Segundo — Terminación Unilateral por EL CONTRATANTE

EL CONTRATANTE podrá dar por terminado el contrato de forma unilateral, sin necesidad de invocar justa causa, mediante notificación escrita con al menos quince (15) días hábiles de antelación. En este caso:

a) EL CONTRATANTE deberá pagar la totalidad de las fases entregadas y aceptadas, el valor total de la fase en curso al momento de la notificación, y una penalidad por terminación unilateral equivalente al treinta por ciento (30%) del valor de las fases restantes del contrato. Esta penalidad se causa exclusivamente por el ejercicio de la terminación unilateral aquí prevista, no por una postergación o suspensión del proyecto, y es independiente del precio del desarrollo.
b) Los pagos realizados por fases entregadas y aceptadas no serán reembolsables.
c) El pago de la penalidad y de las demás sumas correspondientes a la liquidación de esta terminación unilateral no confiere a EL CONTRATANTE derecho a recibir el código fuente, la documentación técnica asociada ni acceso a los repositorios, ni produce la cesión de derechos patrimoniales. Si EL CONTRATANTE solicita dichos elementos, deberá acreditar el pago del cien por ciento (100%) del valor total del contrato y haber satisfecho la penalidad y las demás obligaciones de pago derivadas de la terminación. Para completar el valor contractual se imputarán únicamente los pagos efectuados por concepto del precio del desarrollo; la penalidad es independiente y no constituye abono a dicho precio. La entrega se regirá por el PARÁGRAFO SEXTO de la CLÁUSULA NOVENA y comprenderá exclusivamente el código fuente íntegro y la documentación técnica existentes respecto del trabajo efectivamente desarrollado hasta la fecha de terminación. El pago posterior no reactivará el contrato ni generará obligación de ejecutar las fases pendientes, cuya eventual realización requerirá un nuevo acuerdo escrito.

Las partes reconocen que EL CONTRATISTA organiza su operación conforme al alcance y duración acordados, reservando capacidad de trabajo, asignando personal y comprometiendo recursos para atender el proyecto. Así como EL CONTRATANTE planifica los recursos necesarios para cumplir sus pagos, EL CONTRATISTA realiza una planeación económica y operativa para ejecutar sus obligaciones. La terminación unilateral anticipada altera esa planeación, genera costos de desmovilización y reasignación y afecta la capacidad comprometida y los ingresos previstos, sin que los recursos reservados puedan destinarse inmediatamente a otros proyectos. Esta es la justificación comercial de la penalidad pactada, cuyo pago permite liquidar la salida unilateral en los términos aquí previstos y no sustituye el precio exigido para obtener el código fuente."""

NEW_SOURCE_DELIVERY = """\
### Parágrafo Sexto — Terminación Anticipada

En caso de terminación unilateral por EL CONTRATANTE conforme al PARÁGRAFO SEGUNDO de la CLÁUSULA DÉCIMA SEXTA, el pago de las fases liquidadas y de la penalidad del treinta por ciento (30%) del valor de las fases restantes no equivale al pago del precio total del contrato, no satisface por sí solo la condición suspensiva y no habilita la entrega del código fuente, la documentación técnica asociada, el acceso a repositorios ni la cesión de derechos patrimoniales.

Si EL CONTRATANTE solicita dichos elementos, deberá completar el pago del cien por ciento (100%) del valor total del contrato, descontando únicamente los pagos ya efectuados por concepto del precio del desarrollo, y haber satisfecho la penalidad y las demás obligaciones de pago derivadas de la terminación. La penalidad es independiente, se suma al precio contractual y no constituye abono a este. Acreditado el cumplimiento de estas condiciones, EL CONTRATISTA entregará el código fuente íntegro y la documentación técnica existentes respecto del trabajo efectivamente desarrollado hasta la fecha de terminación, y otorgará el acceso a los repositorios correspondientes, dentro de los cinco (5) días hábiles previstos en el PARÁGRAFO QUINTO, contados desde el día siguiente a la confirmación del pago que complete dichas condiciones. La entrega y la cesión respetarán las excepciones y licencias previstas en la CLÁUSULA DÉCIMA.

En este supuesto, el pago posterior no reactivará el contrato ni obligará a EL CONTRATISTA a ejecutar o completar las fases pendientes; su eventual realización requerirá un nuevo acuerdo escrito. Por ello, la entrega se limita al estado del desarrollo al cierre y no implica que el producto originalmente previsto se encuentre terminado.

Para los demás supuestos de terminación anticipada conforme a la CLÁUSULA DÉCIMA SEXTA, la condición prevista en la presente cláusula se entenderá cumplida cuando EL CONTRATANTE haya pagado la totalidad de las sumas liquidadas a su cargo conforme al parágrafo aplicable de dicha cláusula. Acreditado dicho pago, EL CONTRATISTA entregará el código fuente y otorgará el acceso a los repositorios respecto del trabajo efectivamente pagado, dentro del plazo establecido en el PARÁGRAFO QUINTO de la presente cláusula."""

NEW_IP_TRANSFER = """\
Estos derechos se transfieren de manera permanente y de pleno derecho una vez cumplidas las condiciones establecidas en la CLÁUSULA NOVENA, incluidas las aplicables a la terminación unilateral por EL CONTRATANTE, con las excepciones del PARÁGRAFO SEGUNDO de la presente cláusula. No se causará una contraprestación adicional por la cesión, sin perjuicio del pago del precio contractual y de la penalidad y demás obligaciones económicas que resulten exigibles por la terminación unilateral."""


OLD_HOSTING = """\
### Parágrafo Séptimo — Hosting y Despliegue

1. EL CONTRATANTE tendrá el derecho de alojar el producto software en el proveedor de hosting de su preferencia.
2. El ambiente de producción en el que se aloje el producto software deberá cumplir, como mínimo, con los requerimientos técnicos definidos en el Documento Propuesta Comercial anexo al presente contrato. Lo anterior es condición necesaria para garantizar el correcto funcionamiento del producto software y el cumplimiento de los atributos de calidad esperados, tales como disponibilidad, rendimiento, escalabilidad, seguridad y certificados SSL.
3. La garantía y el soporte definidos en el PARÁGRAFO SEXTO aplicarán siempre que se cumplan las condiciones establecidas en los numerales 6 y 7 de dicho parágrafo, independientemente del proveedor de hosting utilizado.
4. Dado que el alcance del presente contrato comprende el desarrollo del producto software y no su despliegue, no es obligación de EL CONTRATISTA realizar instalaciones en dominios operativos diferentes a los de Project App.
5. En caso de que EL CONTRATANTE solicite la instalación y despliegue del producto en un ambiente diferente a los dominios de Project App, dicho ambiente deberá cumplir con las condiciones descritas en el numeral 2 del presente parágrafo. Este servicio tendrá un costo adicional equivalente al dieciocho por ciento (18%) del valor total del presente contrato. Dicho valor responde al trabajo adicional que implica realizar el despliegue en un entorno distinto al contemplado inicialmente, incluyendo configuración de infraestructura, adaptación de scripts, variables de entorno, validaciones técnicas, endurecimiento de seguridad y puesta en marcha en un ambiente nuevo.
6. Además de las condiciones generales establecidas en el PARÁGRAFO SEXTO, para que la garantía se mantenga vigente en ambientes de hosting externos a Project App, deberán cumplirse las siguientes condiciones:
   a) EL CONTRATANTE deberá garantizar el acceso permanente e ininterrumpido de EL CONTRATISTA al servidor y al código fuente desplegado en producción. La pérdida, revocación o restricción de dicho acceso, por cualquier causa atribuible a EL CONTRATANTE, causará la suspensión inmediata de la garantía hasta que el acceso sea restablecido en su totalidad.
   b) El servicio de hosting deberá ser contratado y pagado por anticipado por EL CONTRATANTE por un periodo mínimo de seis (6) meses continuos. Esta condición es necesaria para garantizar la continuidad operativa del ambiente de producción durante el periodo de garantía de un (1) año establecido en el PARÁGRAFO SEXTO, permitiendo a EL CONTRATISTA acceder al ambiente, diagnosticar y corregir los defectos reportados sin interrupciones derivadas de la caducidad del servicio. El vencimiento del servicio de hosting sin renovación oportuna suspenderá la garantía hasta que EL CONTRATANTE restablezca el servicio y EL CONTRATISTA verifique la integridad del ambiente de producción.
7. Por razones de seguridad, integridad del código fuente y trazabilidad de las operaciones realizadas en el ambiente de producción, EL CONTRATISTA implementará un mecanismo de notificación que registre y comunique todo acceso al servidor. Este mecanismo tiene como finalidad proteger el producto software contra modificaciones no autorizadas, garantizar la cadena de custodia del código desplegado y facilitar el diagnóstico ante eventuales incidentes de seguridad o funcionamiento. Ambas partes recibirán las notificaciones correspondientes.
8. EL CONTRATANTE y el personal que este designe tendrán acceso al servidor en modalidad de solo lectura, exclusivamente para efectos de consulta, verificación y auditoría del producto software desplegado. Cualquier acción que exceda la modalidad de solo lectura, incluyendo pero sin limitarse a modificaciones del código fuente, configuración del servidor, instalación de componentes o alteración de variables de entorno, deberá contar con autorización escrita previa de EL CONTRATISTA. La ejecución de acciones no autorizadas activará lo dispuesto en el numeral 7 del PARÁGRAFO SEXTO respecto a la pérdida de la garantía.
9. Cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte, dicho servicio se regirá por las CLÁUSULAS VIGÉSIMA PRIMERA a VIGÉSIMA CUARTA del presente contrato y por las condiciones económicas definidas en el Documento Propuesta Comercial."""


OLD_EXECUTION = """\
### Parágrafo Cuarto — Efectos sobre la Ejecución y la Aceptación

La condición establecida en la presente cláusula no afecta las demás obligaciones de EL CONTRATISTA. En particular:

1. El producto software permanecerá desplegado y operativo en el ambiente de producción, de modo que EL CONTRATANTE pueda usarlo conforme a la licencia temporal prevista en el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA.
2. La revisión y aceptación de los entregables conforme al PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA se realizará sobre el producto software desplegado y en funcionamiento, sin que ello requiera la entrega del código fuente ni el acceso a los repositorios.
3. Se mantiene el acceso de solo lectura al servidor previsto en el numeral 8 del PARÁGRAFO SÉPTIMO de la CLÁUSULA SEGUNDA, para efectos de consulta, verificación y auditoría.
4. La garantía prevista en el PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA se causa desde la aceptación del entregable final, con independencia del momento en que se produzca la entrega del código fuente.
5. La retención prevista en la presente cláusula no constituye incumplimiento contractual por parte de EL CONTRATISTA, en concordancia con el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SÉPTIMA, ni causa mora ni genera indemnización alguna a favor de EL CONTRATANTE."""


OLD_IP_OPENING = """\
En virtud del presente contrato, y sujeto al cumplimiento de la condición suspensiva establecida en la CLÁUSULA NOVENA, EL CONTRATANTE adquiere, de manera exclusiva y sin limitación alguna, todos los derechos patrimoniales y de explotación sobre el producto software desarrollado a la medida bajo el presente contrato, incluyendo, pero sin limitarse a, derechos de uso, reproducción, modificación, transformación, adaptación, distribución, comercialización, traducción, disposición, exportación, edición, comunicación pública y cualquier otra forma de explotación o uso por cualquier medio, para cualquier fin y sin restricción territorial, por todo el tiempo de protección legal conforme a la normatividad colombiana vigente."""


OLD_IP_RESERVATIONS = """\
### Parágrafo Segundo — Excepciones a la Cesión de Derechos

Quedan excluidos de la cesión de derechos prevista en la presente cláusula los siguientes elementos, cuya propiedad intelectual permanecerá en cabeza de EL CONTRATISTA:

a) Componentes, módulos, librerías y frameworks desarrollados por EL CONTRATISTA con anterioridad al presente contrato o de forma independiente a este.
b) Herramientas genéricas, utilidades y código base reutilizable que formen parte del acervo tecnológico de EL CONTRATISTA y que no hayan sido desarrollados exclusivamente para el presente proyecto.
c) Metodologías, procesos, flujos de trabajo y prácticas de desarrollo empleadas por EL CONTRATISTA en la ejecución del contrato.
d) Conocimiento técnico (know-how), experiencia profesional, habilidades y competencias adquiridas o perfeccionadas por EL CONTRATISTA durante la ejecución del contrato.
e) Diseños de arquitectura, patrones de diseño y soluciones técnicas de carácter genérico que no sean exclusivas del producto desarrollado para EL CONTRATANTE.

Sobre los componentes descritos en los literales a) y b), EL CONTRATANTE recibirá una licencia de uso perpetua, irrevocable, no exclusiva y sin costo adicional, que le permitirá utilizar, modificar e integrar dichos elementos dentro del producto software entregado y sus derivados, sin que esta licencia se extienda a su comercialización como productos independientes."""


OLD_SOURCE_DELIVERY = """\
### Parágrafo Sexto — Terminación Anticipada

En caso de terminación anticipada del contrato conforme a la CLÁUSULA DÉCIMA SEXTA, la condición prevista en la presente cláusula se entenderá cumplida cuando EL CONTRATANTE haya pagado la totalidad de las sumas liquidadas a su cargo conforme al parágrafo aplicable de dicha cláusula. Acreditado dicho pago, EL CONTRATISTA entregará el código fuente y otorgará el acceso a los repositorios respecto del trabajo efectivamente pagado, dentro del plazo establecido en el PARÁGRAFO QUINTO de la presente cláusula."""


OLD_TERMINATION = """\
### Parágrafo Segundo — Terminación Unilateral por EL CONTRATANTE

EL CONTRATANTE podrá dar por terminado el contrato de forma unilateral, sin necesidad de invocar justa causa, mediante notificación escrita con al menos quince (15) días hábiles de antelación. En este caso:

a) EL CONTRATANTE deberá pagar la totalidad de las fases entregadas y aceptadas, el valor total de la fase en curso al momento de la notificación, y una compensación equivalente al veinte por ciento (20%) del valor de las fases restantes del contrato, a título de lucro cesante.
b) EL CONTRATISTA entregará a EL CONTRATANTE el código fuente y la documentación correspondiente al trabajo efectivamente pagado.
c) Los pagos realizados por fases entregadas y aceptadas no serán reembolsables.
d) La entrega del código fuente y documentación estará condicionada al cumplimiento total de las obligaciones de pago por parte de EL CONTRATANTE."""


OLD_TEMPORARY_LICENSE = """\
### Parágrafo Tercero — Licencia Temporal de Uso

Mientras no se cumpla la condición suspensiva establecida en la CLÁUSULA NOVENA, y siempre que EL CONTRATANTE se encuentre al día en sus obligaciones de pago conforme a la CLÁUSULA TERCERA, EL CONTRATISTA otorga a EL CONTRATANTE una licencia de uso temporal, revocable, no exclusiva e intransferible sobre el producto software desplegado, limitada a su uso y operación en el ambiente de producción para los fines propios del negocio de EL CONTRATANTE.

Esta licencia temporal no comprende, y EL CONTRATANTE se abstendrá de ejercer, los derechos de reproducción, modificación, transformación, adaptación, distribución, comercialización, sublicenciamiento o cesión a terceros, ni el encargo a terceros de desarrollos derivados del producto software.

La licencia temporal se extinguirá automáticamente en cualquiera de los siguientes eventos:

a) Al cumplirse la condición suspensiva establecida en la CLÁUSULA NOVENA, momento en el cual operará la cesión plena de derechos prevista en la presente cláusula.
b) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario, conforme al literal a) del PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SEXTA.
c) Por terminación del contrato sin que EL CONTRATANTE haya cumplido la totalidad de sus obligaciones de pago."""


OLD_IP_TRANSFER = """\
Estos derechos se transfieren de manera permanente y de pleno derecho a partir del momento en que EL CONTRATANTE acredite el pago del cien por ciento (100%) del valor total del presente contrato, conforme a la condición suspensiva establecida en la CLÁUSULA NOVENA, con excepción de los elementos descritos en el PARÁGRAFO SEGUNDO de la presente cláusula, y sin que haya lugar a pago adicional a favor de EL CONTRATISTA, más allá de los montos establecidos en la CLÁUSULA TERCERA."""


NEW_HOSTING = """\
### Parágrafo Séptimo — Hosting y Despliegue

1. EL CONTRATANTE tendrá el derecho de alojar el producto software en el proveedor de hosting de su preferencia.
2. El ambiente de producción en el que se aloje el producto software deberá cumplir, como mínimo, con los requerimientos técnicos definidos en el Documento Propuesta Comercial anexo al presente contrato. Lo anterior es condición necesaria para garantizar el correcto funcionamiento del producto software y el cumplimiento de los atributos de calidad esperados, tales como disponibilidad, rendimiento, escalabilidad, seguridad y certificados SSL.
3. La garantía y el soporte definidos en el PARÁGRAFO SEXTO aplicarán siempre que se cumplan las condiciones establecidas en los numerales 6 y 7 de dicho parágrafo, independientemente del proveedor de hosting utilizado.
4. Dado que el alcance del presente contrato comprende el desarrollo del producto software y no su despliegue, no es obligación de EL CONTRATISTA realizar instalaciones en dominios operativos diferentes a los de Project App.
5. En caso de que EL CONTRATANTE solicite la instalación y despliegue del producto en un ambiente diferente a los dominios de Project App, dicho ambiente deberá cumplir con las condiciones descritas en el numeral 2 del presente parágrafo. Este servicio tendrá un costo adicional equivalente al dieciocho por ciento (18%) del valor total del presente contrato. Dicho valor responde al trabajo adicional que implica realizar el despliegue en un entorno distinto al contemplado inicialmente, incluyendo configuración de infraestructura, adaptación de scripts, variables de entorno, validaciones técnicas, endurecimiento de seguridad y puesta en marcha en un ambiente nuevo.
6. Además de las condiciones generales establecidas en el PARÁGRAFO SEXTO, para que la garantía se mantenga vigente en ambientes de hosting externos a Project App, deberán cumplirse las siguientes condiciones:
   a) EL CONTRATANTE deberá garantizar el acceso permanente e ininterrumpido de EL CONTRATISTA al servidor y al código fuente desplegado en producción. La pérdida, revocación o restricción de dicho acceso, por cualquier causa atribuible a EL CONTRATANTE, causará la suspensión inmediata de la garantía hasta que el acceso sea restablecido en su totalidad.
   b) El servicio de hosting deberá ser contratado y pagado por anticipado por EL CONTRATANTE por un periodo mínimo de seis (6) meses continuos. Esta condición es necesaria para garantizar la continuidad operativa del ambiente de producción durante el periodo de garantía de un (1) año establecido en el PARÁGRAFO SEXTO, permitiendo a EL CONTRATISTA acceder al ambiente, diagnosticar y corregir los defectos reportados sin interrupciones derivadas de la caducidad del servicio. El vencimiento del servicio de hosting sin renovación oportuna suspenderá la garantía hasta que EL CONTRATANTE restablezca el servicio y EL CONTRATISTA verifique la integridad del ambiente de producción.
7. Por razones de seguridad, integridad del código fuente y trazabilidad de las operaciones realizadas en el ambiente de producción, EL CONTRATISTA implementará un mecanismo de notificación que registre y comunique todo acceso al servidor. Este mecanismo tiene como finalidad proteger el producto software contra modificaciones no autorizadas, garantizar la cadena de custodia del código desplegado y facilitar el diagnóstico ante eventuales incidentes de seguridad o funcionamiento. Ambas partes recibirán las notificaciones correspondientes.
8. Cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte, dicho servicio se regirá por las CLÁUSULAS VIGÉSIMA PRIMERA a VIGÉSIMA CUARTA del presente contrato y por las condiciones económicas definidas en el Documento Propuesta Comercial."""


NEW_EXECUTION = """\
### Parágrafo Cuarto — Efectos sobre la Ejecución y la Aceptación

La condición establecida en la presente cláusula no afecta las demás obligaciones de EL CONTRATISTA. En particular:

1. El producto software permanecerá desplegado y operativo en el ambiente de producción, de modo que EL CONTRATANTE pueda usarlo conforme a la licencia temporal prevista en el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA.
2. La revisión y aceptación de los entregables conforme al PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA se realizará sobre el producto software desplegado y en funcionamiento, sin que ello requiera la entrega del código fuente ni el acceso a los repositorios.
3. La garantía prevista en el PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA se causa desde la aceptación del entregable final, con independencia del momento en que se produzca la entrega del código fuente.
4. La retención prevista en la presente cláusula no constituye incumplimiento contractual por parte de EL CONTRATISTA, en concordancia con el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SÉPTIMA, ni causa mora ni genera indemnización alguna a favor de EL CONTRATANTE."""


NEW_TEMPORARY_LICENSE = """\
### Parágrafo Tercero — Licencia Temporal de Uso

Mientras no se cumpla la condición suspensiva establecida en la CLÁUSULA NOVENA, y siempre que EL CONTRATANTE se encuentre al día en sus obligaciones de pago conforme a la CLÁUSULA TERCERA, EL CONTRATISTA otorga a EL CONTRATANTE una licencia de uso temporal, revocable, no exclusiva e intransferible sobre el producto software desplegado, limitada a su uso y operación en el ambiente de producción para los fines propios del negocio de EL CONTRATANTE.

Esta licencia temporal no comprende, y EL CONTRATANTE se abstendrá de ejercer, los derechos de reproducción, modificación, transformación, adaptación, distribución, comercialización, sublicenciamiento o cesión a terceros, ni el encargo a terceros de desarrollos derivados del producto software.

La licencia temporal se extinguirá automáticamente en cualquiera de los siguientes eventos:

a) Al cumplirse la condición suspensiva establecida en la CLÁUSULA NOVENA, momento en el cual operará la cesión plena de derechos prevista en la presente cláusula.
b) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario, conforme al literal a) del PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SEXTA.
c) Por terminación del contrato sin que se haya cumplido la condición suspensiva de la CLÁUSULA NOVENA. En caso de terminación unilateral por EL CONTRATANTE, el pago de la liquidación y de la penalidad no mantiene vigente esta licencia ni habilita la cesión de derechos."""


# Keep every condition for source delivery and rights assignment in one group.
PATCH_GROUPS = (
    ('hosting access', (
        (OLD_HOSTING, NEW_HOSTING),
        (OLD_EXECUTION, NEW_EXECUTION),
    )),
    ('ownership and unilateral termination', (
        (OLD_IP_OPENING, NEW_IP_OPENING),
        (OLD_IP_RESERVATIONS, NEW_IP_RESERVATIONS),
        (OLD_IP_TRANSFER, NEW_IP_TRANSFER),
        (OLD_SOURCE_DELIVERY, NEW_SOURCE_DELIVERY),
        (OLD_TERMINATION, NEW_TERMINATION),
        (OLD_TEMPORARY_LICENSE, NEW_TEMPORARY_LICENSE),
    )),
)


def _apply_group(markdown, pairs, label):
    """Preserve the complete group if any anchor has custom or ambiguous text."""
    updated = markdown
    for old, new in pairs:
        if updated.count(new) == 1 and old not in updated:
            continue
        if updated.count(old) != 1 or new in updated:
            logger.warning(
                'Contract ownership update: preserving custom or ambiguous '
                '%s provisions; review this group manually.', label,
            )
            return markdown
        updated = updated.replace(old, new, 1)
    return updated


def _patch_default_template(apps, schema_editor, reverse=False):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    database = schema_editor.connection.alias
    template = (
        ContractTemplate.objects.using(database).select_for_update()
        .filter(is_default=True).first()
    )
    if template is None:
        return
    updated = template.content_markdown
    for label, pairs in PATCH_GROUPS:
        replacements = [(new, old) for old, new in reversed(pairs)] if reverse else pairs
        updated = _apply_group(updated, replacements, label)
    if updated != template.content_markdown:
        template.content_markdown = updated
        template.save(using=database, update_fields=['content_markdown', 'updated_at'])


def update_default_template(apps, schema_editor):
    _patch_default_template(apps, schema_editor)


def revert_default_template(apps, schema_editor):
    _patch_default_template(apps, schema_editor, reverse=True)


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0256_merge_formal_documents_contract_adjustment'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
