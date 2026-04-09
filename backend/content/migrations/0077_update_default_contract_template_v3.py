# Generated 2026-04-08 — update default contract template v3

from django.db import migrations


NEW_CONTRACT_MARKDOWN = """\
Entre las partes, por un lado **{client_full_name}** identificado con número de cédula {client_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATANTE**, y por el otro, **{contractor_full_name}** identificado con número de cédula {contractor_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATISTA**, ambos mayores de edad, identificados como aparece al pie de las firmas, hemos acordado suscribir este contrato de prestación de servicios, el cual se regirá por las siguientes cláusulas:

---

## CLÁUSULA PRIMERA — OBJETO DEL CONTRATO

EL CONTRATISTA se obliga a prestar, por sus propios medios y con plena autonomía técnica y administrativa, los servicios de desarrollo de software cuyo alcance, actividades, productos y cronograma se detallan en la CLÁUSULA SEGUNDA del presente contrato. Como contraprestación, EL CONTRATANTE pagará a EL CONTRATISTA los honorarios establecidos en la CLÁUSULA TERCERA, conforme a la forma de pago allí definida. El inicio de cada fase de ejecución estará sujeto al cumplimiento de los pagos correspondientes.

---

## CLÁUSULA SEGUNDA — EJECUCIÓN DEL CONTRATO

Para la adecuada ejecución del presente contrato, EL CONTRATISTA deberá realizar las actividades descritas en los parágrafos siguientes, conforme al plan, los requerimientos y el cronograma señalados por EL CONTRATANTE. Los plazos de ejecución se contarán a partir de la fecha de firma del presente contrato, salvo que se indique lo contrario en el respectivo parágrafo.

El presente contrato tiene por objeto exclusivo el desarrollo de un producto software. Los servicios de hosting, soporte técnico continuo, mantenimiento correctivo y evolutivo posteriores al periodo de garantía, administración de servidores y cualquier otro servicio de operación no forman parte del presente contrato. La prestación de dichos servicios, en caso de ser requerida por EL CONTRATANTE, deberá ser objeto de un acuerdo independiente entre las partes.

### Parágrafo Primero — Actividades

EL CONTRATISTA ejecutará las siguientes actividades dentro del marco del presente contrato. Las especificaciones técnicas, tecnologías, herramientas y arquitectura se detallan en el Documento Propuesta de Negocio anexo al presente contrato.

1. **Diseño:** Definición de objetivos, diseño de la arquitectura del software y modelado de la solución conforme a los requerimientos de EL CONTRATANTE.
2. **Desarrollo:** Programación e implementación de los componentes del producto software.
3. **Control de calidad:** Ejecución de pruebas para verificar el correcto funcionamiento del software conforme al alcance definido.
4. **Despliegue:** Instalación y puesta en marcha del producto software en el ambiente de producción, sujeto a lo establecido en el PARÁGRAFO SÉPTIMO del presente contrato.
5. **Capacitación:** Orientación a EL CONTRATANTE sobre el uso y operación del producto software entregado.
6. **Entrega:** Entrega formal del código fuente, documentación técnica y demás entregables definidos en el Documento Propuesta de Negocio.

### Parágrafo Segundo — Productos

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Tercero — Cronograma, Roles y Entregables

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Cuarto — Notificación de Entrega

EL CONTRATISTA notificará a EL CONTRATANTE cada entrega, adjuntando la documentación, código y enlaces necesarios, al correo electrónico definido en la CLÁUSULA DÉCIMA CUARTA.

### Parágrafo Quinto — Entrega a Satisfacción

Una vez realizada la notificación de entrega indicada en el PARÁGRAFO CUARTO, se seguirá el siguiente procedimiento de aceptación:

1. **Revisión:** EL CONTRATANTE dispondrá de cuatro (4) días hábiles, contados a partir del día siguiente a la notificación, para revisar el entregable y comunicar sus observaciones o solicitudes de ajuste a través del medio definido en la CLÁUSULA DÉCIMA CUARTA. Las observaciones deberán limitarse al alcance definido en el PARÁGRAFO SEGUNDO.
2. **Corrección:** Una vez recibidas las observaciones, EL CONTRATISTA dispondrá de ocho (8) días hábiles, contados a partir del día siguiente a su recepción, para atender los ajustes solicitados y notificar nuevamente a EL CONTRATANTE.
3. **Rondas de revisión:** El procedimiento descrito en los numerales 1 y 2 podrá repetirse hasta un máximo de tres (3) rondas de revisión por cada entregable.
4. **Aceptación tácita:** Si EL CONTRATANTE no comunica observaciones dentro de los cuatro (4) días hábiles siguientes a cualquier notificación de entrega, se entenderá que el entregable ha sido recibido a satisfacción.
5. **Agotamiento de rondas:** Una vez agotadas las tres (3) rondas de revisión, las partes acordarán por escrito las condiciones para resolver las observaciones pendientes, lo cual podrá formalizarse mediante un OTROSÍ al presente contrato.

### Parágrafo Sexto — Garantía y Soporte

1. Los productos software entregados bajo el presente contrato tendrán una garantía por un periodo de un (1) año, contado a partir de la fecha de aceptación del entregable final. Se entiende por garantía la corrección sin costo de funcionalidades que no operen o no se visualicen conforme a lo definido dentro del alcance del proyecto en el Documento Propuesta de Negocio.
2. Para efectos de la garantía, se considerará un error o defecto (bug) toda falla, comportamiento inesperado o resultado incorrecto del producto software respecto de las funcionalidades y especificaciones expresamente definidas en el alcance del proyecto. No se considerarán errores o defectos cubiertos por la garantía:
   a) Nuevas funcionalidades, módulos o características no contempladas en el alcance original del proyecto.
   b) Cambios en el comportamiento del software solicitados por EL CONTRATANTE que impliquen modificaciones al alcance definido.
   c) Ajustes derivados de cambios en las reglas de negocio, procesos operativos o necesidades de EL CONTRATANTE posteriores a la aceptación del entregable.
   d) Problemas originados por el uso inadecuado del producto software, por datos incorrectos ingresados por EL CONTRATANTE o sus usuarios, o por factores externos al código desarrollado.
   Los requerimientos que no califiquen como errores o defectos podrán ser atendidos mediante un nuevo acuerdo OTROSÍ o un contrato independiente entre las partes.
3. EL CONTRATANTE deberá reportar los problemas detectados a través del medio de notificación definido en la CLÁUSULA DÉCIMA CUARTA, incluyendo los detalles necesarios para reproducir el problema: capturas de pantalla, descripción del error, pasos para replicarlo y cualquier información adicional que facilite su diagnóstico.
4. A partir del día hábil siguiente a la recepción del reporte, EL CONTRATISTA dispondrá de un plazo máximo de ocho (8) días hábiles para: replicar el problema reportado, analizar su causa y brindar una respuesta indicando si el origen está relacionado con el código desarrollado, los datos proporcionados u otro factor. Si la información suministrada resulta insuficiente, EL CONTRATISTA solicitará a EL CONTRATANTE los detalles adicionales necesarios.
5. Dentro del mismo plazo, EL CONTRATISTA informará a EL CONTRATANTE el tiempo estimado de resolución o las acciones necesarias para solucionar el inconveniente.
6. La garantía definida en el presente parágrafo estará sujeta al cumplimiento de las siguientes condiciones:
   a) EL CONTRATISTA deberá contar con acceso al servidor y al código fuente desplegado en el ambiente de producción.
   b) El código fuente en producción deberá corresponder íntegramente al entregado por EL CONTRATISTA, sin modificaciones realizadas por terceros ajenos al equipo de desarrollo.
   c) El ambiente de producción no deberá haber sido alterado en su configuración por personas distintas a EL CONTRATISTA.
7. La garantía quedará sin efecto si EL CONTRATANTE o terceros autorizados por este modifican el código fuente, la configuración del servidor o cualquier componente del producto software sin autorización escrita de EL CONTRATISTA. En este caso, la restitución de la garantía podrá acordarse mediante un OTROSÍ, previa auditoría técnica por parte de EL CONTRATISTA.

### Parágrafo Séptimo — Hosting y Despliegue

1. EL CONTRATANTE tendrá el derecho de alojar el producto software en el proveedor de hosting de su preferencia.
2. El ambiente de producción en el que se aloje el producto software deberá cumplir, como mínimo, con los requerimientos técnicos definidos en el Documento Propuesta de Negocio anexo al presente contrato. Lo anterior es condición necesaria para garantizar el correcto funcionamiento del producto software y el cumplimiento de los atributos de calidad esperados, tales como disponibilidad, rendimiento, escalabilidad, seguridad y certificados SSL.
3. La garantía y el soporte definidos en el PARÁGRAFO SEXTO aplicarán siempre que se cumplan las condiciones establecidas en los numerales 6 y 7 de dicho parágrafo, independientemente del proveedor de hosting utilizado.
4. Dado que el alcance del presente contrato comprende el desarrollo del producto software y no su despliegue, no es obligación de EL CONTRATISTA realizar instalaciones en dominios operativos diferentes a los de Project App.
5. En caso de que EL CONTRATANTE solicite la instalación y despliegue del producto en un ambiente diferente a los dominios de Project App, dicho ambiente deberá cumplir con las condiciones descritas en el numeral 2 del presente parágrafo. Este servicio tendrá un costo adicional equivalente al dieciocho por ciento (18%) del valor total del presente contrato. Dicho valor responde al trabajo adicional que implica realizar el despliegue en un entorno distinto al contemplado inicialmente, incluyendo configuración de infraestructura, adaptación de scripts, variables de entorno, validaciones técnicas, endurecimiento de seguridad y puesta en marcha en un ambiente nuevo.
6. Además de las condiciones generales establecidas en el PARÁGRAFO SEXTO, para que la garantía se mantenga vigente en ambientes de hosting externos a Project App, deberán cumplirse las siguientes condiciones:
   a) EL CONTRATANTE deberá garantizar el acceso permanente e ininterrumpido de EL CONTRATISTA al servidor y al código fuente desplegado en producción. La pérdida, revocación o restricción de dicho acceso, por cualquier causa atribuible a EL CONTRATANTE, causará la suspensión inmediata de la garantía hasta que el acceso sea restablecido en su totalidad.
   b) El servicio de hosting deberá ser contratado y pagado por anticipado por EL CONTRATANTE por un periodo mínimo de seis (6) meses continuos. Esta condición es necesaria para garantizar la continuidad operativa del ambiente de producción durante el periodo de garantía de un (1) año establecido en el PARÁGRAFO SEXTO, permitiendo a EL CONTRATISTA acceder al ambiente, diagnosticar y corregir los defectos reportados sin interrupciones derivadas de la caducidad del servicio. El vencimiento del servicio de hosting sin renovación oportuna suspenderá la garantía hasta que EL CONTRATANTE restablezca el servicio y EL CONTRATISTA verifique la integridad del ambiente de producción.
7. Por razones de seguridad, integridad del código fuente y trazabilidad de las operaciones realizadas en el ambiente de producción, EL CONTRATISTA implementará un mecanismo de notificación que registre y comunique todo acceso al servidor. Este mecanismo tiene como finalidad proteger el producto software contra modificaciones no autorizadas, garantizar la cadena de custodia del código desplegado y facilitar el diagnóstico ante eventuales incidentes de seguridad o funcionamiento. Ambas partes recibirán las notificaciones correspondientes.
8. EL CONTRATANTE y el personal que este designe tendrán acceso al servidor en modalidad de solo lectura, exclusivamente para efectos de consulta, verificación y auditoría del producto software desplegado. Cualquier acción que exceda la modalidad de solo lectura, incluyendo pero sin limitarse a modificaciones del código fuente, configuración del servidor, instalación de componentes o alteración de variables de entorno, deberá contar con autorización escrita previa de EL CONTRATISTA. La ejecución de acciones no autorizadas activará lo dispuesto en el numeral 7 del PARÁGRAFO SEXTO respecto a la pérdida de la garantía.

### Parágrafo Octavo — Exclusiones

Salvo que se pacte expresamente lo contrario en el Documento Propuesta de Negocio, los productos software desarrollados bajo el presente contrato no incluyen:

1. Costos derivados por ambientes de producción, cómputo, hosting, servidores, herramientas de monitoreo y gestión.
2. Costos asociados con la obtención de licencias, permisos y cumplimiento normativo.
3. Costos de desarrollo para actualizaciones, mejoras continuas o nuevas funcionalidades posteriores a la entrega.
4. Gastos relacionados con soporte técnico y atención al usuario final de EL CONTRATANTE, una vez finalizado el periodo de garantía definido en el PARÁGRAFO SEXTO.
5. Costos de seguros relacionados con la propiedad intelectual y responsabilidad civil.
6. Costos derivados por herramientas, plataformas, soluciones o servicios de terceros, incluyendo pero sin limitarse a: dominios, pasarelas de pago y sus comisiones, correos corporativos y certificados SSL.
7. Migración de datos existentes de EL CONTRATANTE hacia el producto software.
8. Integración con sistemas o plataformas de terceros no definidos explícitamente en el alcance del proyecto.
9. Creación de contenidos tales como textos, copywriting, traducciones, imágenes, videos, audios y/o recursos audiovisuales.
10. Capacitación adicional más allá de la contemplada en la actividad de entrega definida en el PARÁGRAFO PRIMERO.
11. Compatibilidad con navegadores, dispositivos o sistemas operativos no definidos en el alcance del proyecto.
12. Reportes, informes, notificaciones, estadísticas y visualizaciones de datos, a menos que sean definidos explícitamente dentro del alcance del producto software.
13. Inventario y/o manejo de inventarios, dejando claro que el portal administrativo no es un gestor de inventario, ni un inventario.

### Parágrafo Noveno — Condiciones de Pago y Entrega

1. La entrega de cada producto está sujeta al pago oportuno por parte de EL CONTRATANTE. Un retraso en los pagos causará un aplazamiento equivalente en los plazos de entrega del siguiente entregable.
2. Cada pago se documentará mediante un acta de entrega y un comprobante de transferencia con la fecha de la transacción.
3. Una vez confirmado el pago correspondiente, se dará inicio al siguiente periodo de desarrollo conforme al cronograma definido en el Documento Propuesta de Negocio.

---

## CLÁUSULA TERCERA — PRECIO Y FORMA DE PAGO

El valor total del presente contrato, el calendario de pagos y los entregables asociados a cada pago se encuentran definidos en el Documento Propuesta de Negocio anexo al presente contrato. Todos los valores se expresan en pesos colombianos (COP).

### Parágrafo Primero

Los pagos se realizarán mediante transferencia bancaria a la cuenta {bank_name} {bank_account_type} No. {bank_account_number} a nombre de EL CONTRATISTA identificado con número de cédula {contractor_cedula}.

### Parágrafo Segundo

En caso de mora en los pagos por parte de EL CONTRATANTE, se causarán intereses de mora a la tasa máxima legal vigente, sin perjuicio del aplazamiento de los plazos de entrega conforme a lo establecido en el PARÁGRAFO NOVENO de la CLÁUSULA SEGUNDA.

### Parágrafo Tercero

Los pagos correspondientes a fases entregadas y aceptadas conforme al procedimiento del PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA no serán reembolsables.

---

## CLÁUSULA CUARTA — SUBCONTRATACIÓN

EL CONTRATISTA podrá subcontratar total o parcialmente la ejecución del objeto contractual sin necesidad de autorización previa de EL CONTRATANTE. En todo caso, EL CONTRATISTA será el único responsable ante EL CONTRATANTE por el cumplimiento de las obligaciones derivadas del presente contrato, así como por las cargas contractuales, laborales y de seguridad social que se generen respecto del personal que vincule para tal fin.

---

## CLÁUSULA QUINTA — SUPERVISIÓN

EL CONTRATANTE podrá supervisar la ejecución del presente contrato. Para ello, las partes definirán de común acuerdo un medio y una periodicidad de comunicación para la actualización del estado del proyecto. EL CONTRATANTE podrá formular observaciones, las cuales serán analizadas conjuntamente con EL CONTRATISTA. La supervisión por parte de EL CONTRATANTE no implicará subordinación ni afectará la autonomía técnica y administrativa de EL CONTRATISTA.

---

## CLÁUSULA SEXTA — EXCLUSIÓN DE LA RELACIÓN LABORAL

Dada la naturaleza del presente contrato, no existirá relación laboral alguna entre EL CONTRATANTE y EL CONTRATISTA, ni con el personal que este vincule para apoyar la ejecución del objeto contractual. EL CONTRATISTA ejecutará el contrato de forma independiente y con plena autonomía técnica y administrativa. EL CONTRATISTA será responsable del pago de sus propias obligaciones en materia de seguridad social integral (salud, pensión y riesgos laborales), así como de las correspondientes al personal que subcontrate.

---

## CLÁUSULA SÉPTIMA — OBLIGACIONES DEL CONTRATISTA

a) Cumplir oportunamente el objeto y las actividades definidas en la CLÁUSULA SEGUNDA del presente contrato.
b) Aportar su experiencia y conocimientos para la adecuada ejecución del contrato.
c) Entregar el código fuente, la documentación técnica y los demás entregables conforme a lo establecido en el Documento Propuesta de Negocio.
d) Cumplir con la garantía y soporte en los términos del PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA.
e) Absolver las consultas de EL CONTRATANTE relacionadas con el objeto del contrato.
f) Asistir a las reuniones en los días y horas previamente acordados entre las partes.
g) Informar oportunamente a EL CONTRATANTE sobre cualquier circunstancia que pueda afectar el cumplimiento de los plazos o el alcance del proyecto.

---

## CLÁUSULA OCTAVA — OBLIGACIONES DEL CONTRATANTE

a) Pagar los honorarios en los términos establecidos en la CLÁUSULA TERCERA del presente contrato.
b) Facilitar a EL CONTRATISTA, de manera oportuna, el acceso a la información, insumos, contenidos y recursos necesarios para la ejecución del contrato.
c) Designar una persona de contacto con capacidad de decisión para la comunicación con EL CONTRATISTA durante la ejecución del proyecto.
d) Dar respuesta a las entregas dentro de los plazos establecidos en el PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA.
e) Cumplir con las demás obligaciones y condiciones previstas en el presente contrato y sus anexos.

---

## CLÁUSULA NOVENA — DERECHOS PATRIMONIALES Y DERECHOS DE EXPLOTACIÓN

En virtud del presente contrato, EL CONTRATANTE adquiere, de manera exclusiva y sin limitación alguna, todos los derechos patrimoniales y de explotación sobre el producto software desarrollado a la medida bajo el presente contrato, incluyendo, pero sin limitarse a, derechos de uso, reproducción, modificación, transformación, adaptación, distribución, comercialización, traducción, disposición, exportación, edición, comunicación pública y cualquier otra forma de explotación o uso por cualquier medio, para cualquier fin y sin restricción territorial, por todo el tiempo de protección legal conforme a la normatividad colombiana vigente.

Estos derechos se transfieren de manera permanente desde el momento de la entrega y aceptación del software, con excepción de los elementos descritos en el PARÁGRAFO SEGUNDO de la presente cláusula, y sin que haya lugar a pago adicional a favor de EL CONTRATISTA, más allá de los montos establecidos en la CLÁUSULA TERCERA.

### Parágrafo Primero — Uso por el Contratante

EL CONTRATANTE podrá utilizar los resultados parciales y finales del proyecto para adaptarlos, modificarlos o integrarlos en cualquier tipo de producto, proyecto o aplicación que considere necesario, sin requerir autorización adicional de EL CONTRATISTA y sin que ello genere derecho a contraprestación adicional, siempre que se encuentre al día en el cumplimiento de sus obligaciones de pago conforme a la CLÁUSULA TERCERA.

### Parágrafo Segundo — Excepciones a la Cesión de Derechos

Quedan excluidos de la cesión de derechos prevista en la presente cláusula los siguientes elementos, cuya propiedad intelectual permanecerá en cabeza de EL CONTRATISTA:

a) Componentes, módulos, librerías y frameworks desarrollados por EL CONTRATISTA con anterioridad al presente contrato o de forma independiente a este.
b) Herramientas genéricas, utilidades y código base reutilizable que formen parte del acervo tecnológico de EL CONTRATISTA y que no hayan sido desarrollados exclusivamente para el presente proyecto.
c) Metodologías, procesos, flujos de trabajo y prácticas de desarrollo empleadas por EL CONTRATISTA en la ejecución del contrato.
d) Conocimiento técnico (know-how), experiencia profesional, habilidades y competencias adquiridas o perfeccionadas por EL CONTRATISTA durante la ejecución del contrato.
e) Diseños de arquitectura, patrones de diseño y soluciones técnicas de carácter genérico que no sean exclusivas del producto desarrollado para EL CONTRATANTE.

Sobre los componentes descritos en los literales a) y b), EL CONTRATANTE recibirá una licencia de uso perpetua, irrevocable, no exclusiva y sin costo adicional, que le permitirá utilizar, modificar e integrar dichos elementos dentro del producto software entregado y sus derivados, sin que esta licencia se extienda a su comercialización como productos independientes.

---

## CLÁUSULA DÉCIMA — CONFIDENCIALIDAD

Ambas partes se obligan a mantener la confidencialidad sobre toda la información que conozcan o a la que tengan acceso con ocasión del presente contrato, con independencia del medio en el cual se encuentre soportada. En adelante, la parte que revela información se denominará PARTE REVELADORA y la que la recibe, PARTE RECEPTORA.

Se tendrá como información confidencial cualquier información no divulgada que posea legítimamente la PARTE REVELADORA y que pueda usarse en alguna actividad académica, productiva, industrial o comercial y que sea susceptible de comunicarse a un tercero. Sin fines restrictivos, la información confidencial podrá versar sobre invenciones, modelos de utilidad, programas de software, fórmulas, métodos, know-how, procesos, diseños, metodologías, arquitecturas técnicas, nuevos productos, trabajos en desarrollo, requisitos de comercialización, planes de mercadeo, estrategias comerciales, información financiera, nombres de clientes y proveedores existentes y potenciales, así como toda otra información que cualquiera de las partes identifique como confidencial.

La información confidencial incluye también toda información recibida de terceros que la PARTE RECEPTORA esté obligada a tratar como confidencial.

La obligación de confidencialidad no aplica sobre aquella información que:

a) Sea o llegue a ser del dominio público sin que medie acto u omisión de la PARTE RECEPTORA.
b) Estuviese en posesión legítima de la PARTE RECEPTORA con anterioridad a su divulgación y no hubiese sido obtenida de forma directa o indirecta de la PARTE REVELADORA.
c) Sea legalmente divulgada por un tercero que no esté sujeto a restricciones en cuanto a su divulgación y la haya obtenido de buena fe.
d) Deba ser divulgada por orden judicial o requerimiento de autoridad competente, en cuyo caso la PARTE RECEPTORA notificará a la PARTE REVELADORA con la mayor antelación posible.

La obligación de confidencialidad permanecerá vigente durante la ejecución del contrato y por un periodo de dos (2) años contados a partir de su terminación por cualquier causa.

---

## CLÁUSULA DÉCIMA PRIMERA — PROTECCIÓN Y TRATAMIENTO DE DATOS PERSONALES

EL CONTRATISTA asume la obligación de proteger los datos personales a los que acceda con ocasión del presente contrato, en cumplimiento de la Ley 1581 de 2012 y sus decretos reglamentarios. Para tal efecto, EL CONTRATISTA deberá:

a) Adoptar las medidas técnicas, administrativas y humanas necesarias para garantizar la seguridad de los datos personales y evitar su adulteración, pérdida, consulta, uso o acceso no autorizado.
b) Limitar el tratamiento de los datos personales de terceros entregados por EL CONTRATANTE exclusivamente a la finalidad propia de sus obligaciones contractuales.
c) Garantizar los derechos de privacidad, intimidad y buen nombre de los titulares de los datos personales.
d) Informar a EL CONTRATANTE de manera inmediata cualquier sospecha de pérdida, fuga, acceso no autorizado o incidente de seguridad que afecte los datos personales a los que haya tenido acceso.
e) Una vez finalizado el contrato, devolver o eliminar los datos personales que le hayan sido entregados, salvo que exista obligación legal de conservarlos.

---

## CLÁUSULA DÉCIMA SEGUNDA — MODIFICACIONES

Cualquier modificación a los términos y condiciones del presente contrato deberá ser acordada entre las partes y requerirá de un "OTROSÍ" firmado por ellas.

---

## CLÁUSULA DÉCIMA TERCERA — ACUERDO

El presente contrato, junto con el Documento Propuesta de Negocio y demás anexos que se suscriban, constituye el acuerdo total entre las partes sobre su objeto. Este acuerdo reemplaza en su integridad y deja sin efecto cualquier otro acuerdo verbal o escrito celebrado con anterioridad entre las partes sobre el mismo objeto.

---

## CLÁUSULA DÉCIMA CUARTA — NOTIFICACIÓN

Para todos los efectos legales y de notificación derivados del presente contrato, las partes establecen los siguientes medios de contacto:

- **EL CONTRATANTE:** correo electrónico {client_email}
- **EL CONTRATISTA:** correo electrónico {contractor_email}

Toda notificación enviada a las direcciones de correo electrónico aquí indicadas se entenderá válidamente surtida al día hábil siguiente a su envío. Cualquier cambio en los datos de notificación deberá ser comunicado por escrito a la otra parte con al menos cinco (5) días hábiles de antelación.

---

## CLÁUSULA DÉCIMA QUINTA — TERMINACIÓN ANTICIPADA

El presente contrato podrá darse por terminado anticipadamente en los siguientes casos:

### Parágrafo Primero — Terminación por Mutuo Acuerdo

Las partes podrán dar por terminado el contrato en cualquier momento mediante acuerdo escrito, en el cual se definirán las condiciones de entrega parcial, liquidación de pagos y demás aspectos pendientes.

### Parágrafo Segundo — Terminación Unilateral por EL CONTRATANTE

EL CONTRATANTE podrá dar por terminado el contrato de forma unilateral, sin necesidad de invocar justa causa, mediante notificación escrita con al menos quince (15) días hábiles de antelación. En este caso:

a) EL CONTRATANTE deberá pagar la totalidad de las fases entregadas y aceptadas, el valor total de la fase en curso al momento de la notificación, y una compensación equivalente al veinte por ciento (20%) del valor de las fases restantes del contrato, a título de lucro cesante.
b) EL CONTRATISTA entregará a EL CONTRATANTE el código fuente y la documentación correspondiente al trabajo efectivamente pagado.
c) Los pagos realizados por fases entregadas y aceptadas no serán reembolsables.
d) La entrega del código fuente y documentación estará condicionada al cumplimiento total de las obligaciones de pago por parte de EL CONTRATANTE.

### Parágrafo Tercero — Terminación Unilateral por EL CONTRATISTA

EL CONTRATISTA podrá dar por terminado el contrato de forma unilateral, mediante notificación escrita con al menos quince (15) días hábiles de antelación, en los siguientes casos:

a) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario.
b) Cuando EL CONTRATANTE incumpla reiteradamente sus obligaciones contractuales, afectando de manera sustancial la ejecución del proyecto.
c) Cuando EL CONTRATANTE no suministre la información, insumos o recursos necesarios para la ejecución del contrato dentro de un plazo razonable, causando una paralización efectiva del proyecto por más de veinte (20) días hábiles.

En caso de terminación por cualquiera de estas causas, EL CONTRATISTA conservará la totalidad de los pagos recibidos hasta la fecha y tendrá derecho al pago del trabajo ejecutado en la fase en curso. La entrega del trabajo realizado estará sujeta al cumplimiento de las obligaciones de pago pendientes.

### Parágrafo Cuarto — Suspensión por Mora

Sin perjuicio de lo anterior, EL CONTRATISTA podrá suspender la ejecución del contrato cuando EL CONTRATANTE presente mora en los pagos por un periodo superior a quince (15) días calendario, sin que dicha suspensión constituya incumplimiento contractual. La ejecución se reanudará una vez EL CONTRATANTE se ponga al día en sus obligaciones de pago, y los plazos de entrega se ajustarán en un periodo equivalente al de la suspensión.

---

## CLÁUSULA DÉCIMA SEXTA — INCUMPLIMIENTO

En caso de que cualquiera de las partes incumpla una o varias de las obligaciones derivadas del presente contrato, la parte afectada deberá notificar por escrito a la parte incumplida, describiendo el incumplimiento de manera detallada.

### Parágrafo Primero — Plazo para Subsanar

La parte incumplida dispondrá de un plazo de quince (15) días hábiles, contados a partir del día siguiente a la recepción de la notificación, para subsanar el incumplimiento. Tratándose de obligaciones de pago, el plazo para subsanar será de diez (10) días hábiles.

### Parágrafo Segundo — Consecuencias del Incumplimiento No Subsanado

Si transcurrido el plazo correspondiente el incumplimiento no ha sido subsanado, la parte afectada podrá:

a) Dar por terminado el contrato conforme a lo establecido en la CLÁUSULA DÉCIMA QUINTA, sin perjuicio de las acciones legales a que haya lugar.
b) Exigir el cumplimiento de las obligaciones pendientes junto con la indemnización de los perjuicios causados, incluyendo el daño emergente y el lucro cesante, conforme a la legislación civil colombiana y sujeto a los límites establecidos en la CLÁUSULA DÉCIMA NOVENA.

### Parágrafo Tercero — Derecho de Retención

EL CONTRATISTA podrá retener el código fuente, la documentación técnica y los demás entregables pendientes de entrega cuando EL CONTRATANTE se encuentre en mora en el cumplimiento de sus obligaciones de pago. Esta retención no constituirá incumplimiento contractual por parte de EL CONTRATISTA y se mantendrá hasta que EL CONTRATANTE cumpla la totalidad de sus obligaciones de pago, incluyendo los intereses de mora a que haya lugar conforme a la CLÁUSULA TERCERA.

---

## CLÁUSULA DÉCIMA SÉPTIMA — RESOLUCIÓN DE CONFLICTOS

Toda controversia o diferencia que surja entre las partes con ocasión del presente contrato, su interpretación, ejecución o terminación, se resolverá conforme al siguiente procedimiento:

1. **Negociación directa:** Las partes intentarán resolver la controversia de manera directa y de buena fe dentro de un plazo de quince (15) días hábiles contados a partir de la notificación escrita de la controversia.
2. **Conciliación:** Si la negociación directa no resuelve la controversia, las partes acudirán a un centro de conciliación legalmente establecido en la ciudad de {contract_city}, Colombia. Los costos de la conciliación serán asumidos por partes iguales.
3. **Jurisdicción ordinaria:** Si la conciliación no prospera dentro de los treinta (30) días calendario siguientes a la solicitud, las partes someterán la controversia a la jurisdicción civil ordinaria de la ciudad de {contract_city}, Colombia, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.

Las costas y gastos judiciales del proceso serán asumidos por la parte vencida, salvo decisión diferente del juez competente.

Durante el trámite de cualquier controversia, las obligaciones de confidencialidad y protección de datos personales previstas en el presente contrato continuarán plenamente vigentes.

---

## CLÁUSULA DÉCIMA OCTAVA — MÉRITO EJECUTIVO

El presente contrato, junto con sus anexos, las actas de entrega y los comprobantes de pago, prestará mérito ejecutivo para el cobro de las obligaciones claras, expresas y exigibles que de él se deriven, sin necesidad de requerimiento judicial previo ni constitución en mora, de conformidad con lo establecido en el artículo 422 del Código General del Proceso colombiano.

Para todos los efectos legales, las partes reconocen que las obligaciones de pago contenidas en el presente contrato y en el Documento Propuesta de Negocio anexo constituyen títulos ejecutivos suficientes para iniciar las acciones de cobro correspondientes.

---

## CLÁUSULA DÉCIMA NOVENA — LIMITACIÓN DE RESPONSABILIDAD

La responsabilidad total de EL CONTRATISTA frente a EL CONTRATANTE, por cualquier concepto derivado del presente contrato, incluyendo pero sin limitarse a incumplimiento, daños, perjuicios, indemnizaciones o reclamaciones de cualquier naturaleza, no podrá exceder en ningún caso el valor total efectivamente pagado por EL CONTRATANTE bajo el presente contrato al momento en que se configure la causa de la reclamación.

### Parágrafo Primero — Exclusión de Daños Indirectos

EL CONTRATISTA no será responsable por daños indirectos, consecuenciales, lucro cesante derivado de la operación del negocio de EL CONTRATANTE, pérdida de datos no ocasionada por negligencia directa de EL CONTRATISTA, ni por daños derivados de la interrupción del negocio de EL CONTRATANTE, salvo en casos de dolo o culpa grave debidamente comprobada.

### Parágrafo Segundo — Exclusión de Responsabilidad por Terceros

EL CONTRATISTA no será responsable por fallas, interrupciones o daños causados por servicios, plataformas o herramientas de terceros, incluyendo pero sin limitarse a proveedores de hosting, pasarelas de pago, servicios de correo electrónico, certificados SSL y cualquier otro componente externo al producto software desarrollado.

### Parágrafo Tercero — Derecho de Reparación

Antes de iniciar cualquier reclamación, acción legal o proceso derivado del presente contrato, EL CONTRATANTE deberá notificar por escrito a EL CONTRATISTA el daño o perjuicio identificado, describiendo con suficiente detalle la situación y la evidencia disponible. A partir del día hábil siguiente a la recepción de dicha notificación, EL CONTRATISTA dispondrá de un plazo de veinte (20) días hábiles para evaluar, proponer y ejecutar las acciones correctivas necesarias para reparar el daño causado.

EL CONTRATISTA tendrá derecho a reparar el daño de manera oportuna y a su costo, siempre que la reparación sea técnicamente viable. Si EL CONTRATISTA repara satisfactoriamente el daño dentro del plazo otorgado, no habrá lugar a indemnización por el concepto reparado.

Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones legales correspondientes en caso de que la reparación no sea satisfactoria o no se realice dentro del plazo establecido.\
"""


# ---------------------------------------------------------------------------
# Previous template (v2, after migration 0065 + 0067 dash normalization)
# ---------------------------------------------------------------------------
OLD_CONTRACT_MARKDOWN = """\
Entre las partes, por un lado **{client_full_name}** identificado con número de cédula {client_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATANTE**, y por el otro, **{contractor_full_name}** identificado con número de cédula {contractor_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATISTA**, ambos mayores de edad, identificados como aparece al pie de las firmas, hemos acordado suscribir este contrato de prestación de servicios, el cual se regirá por las siguientes cláusulas:

---

## CLÁUSULA PRIMERA - OBJETO DEL CONTRATO

EL CONTRATISTA se obliga a prestar, por sus propios medios y con plena autonomía técnica y administrativa, los servicios de desarrollo de software cuyo alcance, actividades, productos y cronograma se detallan en la CLÁUSULA SEGUNDA del presente contrato. Como contraprestación, EL CONTRATANTE pagará a EL CONTRATISTA los honorarios establecidos en la CLÁUSULA TERCERA, conforme a la forma de pago allí definida. El inicio de cada fase de ejecución estará sujeto al cumplimiento de los pagos correspondientes.

---

## CLÁUSULA SEGUNDA - EJECUCIÓN DEL CONTRATO

Para la adecuada ejecución del presente contrato, EL CONTRATISTA deberá realizar las actividades descritas en los parágrafos siguientes, conforme al plan, los requerimientos y el cronograma señalados por EL CONTRATANTE. Los plazos de ejecución se contarán a partir de la fecha de firma del presente contrato, salvo que se indique lo contrario en el respectivo parágrafo.

El presente contrato tiene por objeto exclusivo el desarrollo de un producto software. Los servicios de hosting, soporte técnico continuo, mantenimiento correctivo y evolutivo posteriores al periodo de garantía, administración de servidores y cualquier otro servicio de operación no forman parte del presente contrato. La prestación de dichos servicios, en caso de ser requerida por EL CONTRATANTE, deberá ser objeto de un acuerdo independiente entre las partes.

### Parágrafo Primero - Actividades

EL CONTRATISTA ejecutará las siguientes actividades dentro del marco del presente contrato. Las especificaciones técnicas, tecnologías, herramientas y arquitectura se detallan en el Documento Propuesta de Negocio anexo al presente contrato.

1. **Diseño:** Definición de objetivos, diseño de la arquitectura del software y modelado de la solución conforme a los requerimientos de EL CONTRATANTE.
2. **Desarrollo:** Programación e implementación de los componentes del producto software.
3. **Control de calidad:** Ejecución de pruebas para verificar el correcto funcionamiento del software conforme al alcance definido.
4. **Despliegue:** Instalación y puesta en marcha del producto software en el ambiente de producción, sujeto a lo establecido en el PARÁGRAFO SÉPTIMO del presente contrato.
5. **Capacitación:** Orientación a EL CONTRATANTE sobre el uso y operación del producto software entregado.
6. **Entrega:** Entrega formal del código fuente, documentación técnica y demás entregables definidos en el Documento Propuesta de Negocio.

### Parágrafo Segundo - Productos

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Tercero - Cronograma, Roles y Entregables

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Cuarto - Notificación de Entrega

EL CONTRATISTA notificará a EL CONTRATANTE cada entrega, adjuntando la documentación, código y enlaces necesarios, al correo electrónico definido en la CLÁUSULA DÉCIMA CUARTA.

### Parágrafo Quinto - Entrega a Satisfacción

Una vez realizada la notificación de entrega indicada en el PARÁGRAFO CUARTO, se seguirá el siguiente procedimiento de aceptación:

1. **Revisión:** EL CONTRATANTE dispondrá de cuatro (4) días hábiles, contados a partir del día siguiente a la notificación, para revisar el entregable y comunicar sus observaciones o solicitudes de ajuste a través del medio definido en la CLÁUSULA DÉCIMA CUARTA. Las observaciones deberán limitarse al alcance definido en el PARÁGRAFO SEGUNDO.
2. **Corrección:** Una vez recibidas las observaciones, EL CONTRATISTA dispondrá de ocho (8) días hábiles, contados a partir del día siguiente a su recepción, para atender los ajustes solicitados y notificar nuevamente a EL CONTRATANTE.
3. **Rondas de revisión:** El procedimiento descrito en los numerales 1 y 2 podrá repetirse hasta un máximo de tres (3) rondas de revisión por cada entregable.
4. **Aceptación tácita:** Si EL CONTRATANTE no comunica observaciones dentro de los cuatro (4) días hábiles siguientes a cualquier notificación de entrega, se entenderá que el entregable ha sido recibido a satisfacción.
5. **Agotamiento de rondas:** Una vez agotadas las tres (3) rondas de revisión, las partes acordarán por escrito las condiciones para resolver las observaciones pendientes, lo cual podrá formalizarse mediante un OTROSÍ al presente contrato.

### Parágrafo Sexto - Garantía y Soporte

1. Los productos software entregados bajo el presente contrato tendrán una garantía por un periodo de un (1) año, contado a partir de la fecha de aceptación del entregable final. Se entiende por garantía la corrección sin costo de funcionalidades que no operen o no se visualicen conforme a lo definido dentro del alcance del proyecto en el Documento Propuesta de Negocio.
2. Para efectos de la garantía, se considerará un error o defecto (bug) toda falla, comportamiento inesperado o resultado incorrecto del producto software respecto de las funcionalidades y especificaciones expresamente definidas en el alcance del proyecto. No se considerarán errores o defectos cubiertos por la garantía:
   a) Nuevas funcionalidades, módulos o características no contempladas en el alcance original del proyecto.
   b) Cambios en el comportamiento del software solicitados por EL CONTRATANTE que impliquen modificaciones al alcance definido.
   c) Ajustes derivados de cambios en las reglas de negocio, procesos operativos o necesidades de EL CONTRATANTE posteriores a la aceptación del entregable.
   d) Problemas originados por el uso inadecuado del producto software, por datos incorrectos ingresados por EL CONTRATANTE o sus usuarios, o por factores externos al código desarrollado.
   Los requerimientos que no califiquen como errores o defectos podrán ser atendidos mediante un nuevo acuerdo OTROSÍ o un contrato independiente entre las partes.
3. EL CONTRATANTE deberá reportar los problemas detectados a través del medio de notificación definido en la CLÁUSULA DÉCIMA CUARTA, incluyendo los detalles necesarios para reproducir el problema: capturas de pantalla, descripción del error, pasos para replicarlo y cualquier información adicional que facilite su diagnóstico.
4. A partir del día hábil siguiente a la recepción del reporte, EL CONTRATISTA dispondrá de un plazo máximo de ocho (8) días hábiles para: replicar el problema reportado, analizar su causa y brindar una respuesta indicando si el origen está relacionado con el código desarrollado, los datos proporcionados u otro factor. Si la información suministrada resulta insuficiente, EL CONTRATISTA solicitará a EL CONTRATANTE los detalles adicionales necesarios.
5. Dentro del mismo plazo, EL CONTRATISTA informará a EL CONTRATANTE el tiempo estimado de resolución o las acciones necesarias para solucionar el inconveniente.
6. La garantía definida en el presente parágrafo estará sujeta al cumplimiento de las siguientes condiciones:
   a) EL CONTRATISTA deberá contar con acceso al servidor y al código fuente desplegado en el ambiente de producción.
   b) El código fuente en producción deberá corresponder íntegramente al entregado por EL CONTRATISTA, sin modificaciones realizadas por terceros ajenos al equipo de desarrollo.
   c) El ambiente de producción no deberá haber sido alterado en su configuración por personas distintas a EL CONTRATISTA.
7. La garantía quedará sin efecto si EL CONTRATANTE o terceros autorizados por este modifican el código fuente, la configuración del servidor o cualquier componente del producto software sin autorización escrita de EL CONTRATISTA. En este caso, la restitución de la garantía podrá acordarse mediante un OTROSÍ, previa auditoría técnica por parte de EL CONTRATISTA.

### Parágrafo Séptimo - Hosting y Despliegue

1. EL CONTRATANTE tendrá el derecho de alojar el producto software en el proveedor de hosting de su preferencia.
2. Se recomienda que el producto software sea alojado en ambientes que garanticen su correcta operación y cumplan con estándares de calidad tales como disponibilidad, rendimiento, escalabilidad, seguridad y certificados SSL.
3. La garantía y el soporte definidos en el PARÁGRAFO SEXTO aplicarán siempre que se cumplan las condiciones establecidas en los numerales 6 y 7 de dicho parágrafo, independientemente del proveedor de hosting utilizado.
4. Dado que el alcance del presente contrato comprende el desarrollo del producto software y no su despliegue, no es obligación de EL CONTRATISTA realizar instalaciones en dominios operativos diferentes a los de Project App.
5. En caso de que EL CONTRATANTE solicite la instalación y despliegue del producto en un ambiente diferente a los dominios de Project App, dicho ambiente deberá cumplir con los requerimientos técnicos definidos en el Documento Propuesta de Negocio. Este servicio tendrá un costo adicional equivalente al doce por ciento (12%) del valor total del presente contrato.

### Parágrafo Octavo - Exclusiones

Salvo que se pacte expresamente lo contrario en el Documento Propuesta de Negocio, los productos software desarrollados bajo el presente contrato no incluyen:

1. Costos derivados por ambientes de producción, cómputo, hosting, servidores, herramientas de monitoreo y gestión.
2. Costos asociados con la obtención de licencias, permisos y cumplimiento normativo.
3. Costos de desarrollo para actualizaciones, mejoras continuas o nuevas funcionalidades posteriores a la entrega.
4. Gastos relacionados con soporte técnico y atención al usuario final de EL CONTRATANTE, una vez finalizado el periodo de garantía definido en el PARÁGRAFO SEXTO.
5. Costos de seguros relacionados con la propiedad intelectual y responsabilidad civil.
6. Costos derivados por herramientas, plataformas, soluciones o servicios de terceros, incluyendo pero sin limitarse a: dominios, pasarelas de pago y sus comisiones, correos corporativos y certificados SSL.
7. Migración de datos existentes de EL CONTRATANTE hacia el producto software.
8. Integración con sistemas o plataformas de terceros no definidos explícitamente en el alcance del proyecto.
9. Creación de contenidos tales como textos, copywriting, traducciones, imágenes, videos, audios y/o recursos audiovisuales.
10. Capacitación adicional más allá de la contemplada en la actividad de entrega definida en el PARÁGRAFO PRIMERO.
11. Compatibilidad con navegadores, dispositivos o sistemas operativos no definidos en el alcance del proyecto.
12. Reportes, informes, notificaciones, estadísticas y visualizaciones de datos, a menos que sean definidos explícitamente dentro del alcance del producto software.
13. Inventario y/o manejo de inventarios, dejando claro que el portal administrativo no es un gestor de inventario, ni un inventario.

### Parágrafo Noveno - Condiciones de Pago y Entrega

1. La entrega de cada producto está sujeta al pago oportuno por parte de EL CONTRATANTE. Un retraso en los pagos causará un aplazamiento equivalente en los plazos de entrega del siguiente entregable.
2. Cada pago se documentará mediante un acta de entrega y un comprobante de transferencia con la fecha de la transacción.
3. Una vez confirmado el pago correspondiente, se dará inicio al siguiente periodo de desarrollo conforme al cronograma definido en el Documento Propuesta de Negocio.

---

## CLÁUSULA TERCERA - PRECIO Y FORMA DE PAGO

El valor total del presente contrato, el calendario de pagos y los entregables asociados a cada pago se encuentran definidos en el Documento Propuesta de Negocio anexo al presente contrato. Todos los valores se expresan en pesos colombianos (COP).

### Parágrafo Primero

Los pagos se realizarán mediante transferencia bancaria a la cuenta {bank_name} {bank_account_type} No. {bank_account_number} a nombre de EL CONTRATISTA identificado con número de cédula {contractor_cedula}.

### Parágrafo Segundo

En caso de mora en los pagos por parte de EL CONTRATANTE, se causarán intereses de mora a la tasa máxima legal vigente, sin perjuicio del aplazamiento de los plazos de entrega conforme a lo establecido en el PARÁGRAFO NOVENO de la CLÁUSULA SEGUNDA.

### Parágrafo Tercero

Los pagos correspondientes a fases entregadas y aceptadas conforme al procedimiento del PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA no serán reembolsables.

---

## CLÁUSULA CUARTA - SUBCONTRATACIÓN

EL CONTRATISTA podrá subcontratar total o parcialmente la ejecución del objeto contractual sin necesidad de autorización previa de EL CONTRATANTE. En todo caso, EL CONTRATISTA será el único responsable ante EL CONTRATANTE por el cumplimiento de las obligaciones derivadas del presente contrato, así como por las cargas contractuales, laborales y de seguridad social que se generen respecto del personal que vincule para tal fin.

---

## CLÁUSULA QUINTA - SUPERVISIÓN

EL CONTRATANTE podrá supervisar la ejecución del presente contrato. Para ello, las partes definirán de común acuerdo un medio y una periodicidad de comunicación para la actualización del estado del proyecto. EL CONTRATANTE podrá formular observaciones, las cuales serán analizadas conjuntamente con EL CONTRATISTA. La supervisión por parte de EL CONTRATANTE no implicará subordinación ni afectará la autonomía técnica y administrativa de EL CONTRATISTA.

---

## CLÁUSULA SEXTA - EXCLUSIÓN DE LA RELACIÓN LABORAL

Dada la naturaleza del presente contrato, no existirá relación laboral alguna entre EL CONTRATANTE y EL CONTRATISTA, ni con el personal que este vincule para apoyar la ejecución del objeto contractual. EL CONTRATISTA ejecutará el contrato de forma independiente y con plena autonomía técnica y administrativa. EL CONTRATISTA será responsable del pago de sus propias obligaciones en materia de seguridad social integral (salud, pensión y riesgos laborales), así como de las correspondientes al personal que subcontrate.

---

## CLÁUSULA SÉPTIMA - OBLIGACIONES DEL CONTRATISTA

a) Cumplir oportunamente el objeto y las actividades definidas en la CLÁUSULA SEGUNDA del presente contrato.
b) Aportar su experiencia y conocimientos para la adecuada ejecución del contrato.
c) Entregar el código fuente, la documentación técnica y los demás entregables conforme a lo establecido en el Documento Propuesta de Negocio.
d) Cumplir con la garantía y soporte en los términos del PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA.
e) Absolver las consultas de EL CONTRATANTE relacionadas con el objeto del contrato.
f) Asistir a las reuniones en los días y horas previamente acordados entre las partes.
g) Informar oportunamente a EL CONTRATANTE sobre cualquier circunstancia que pueda afectar el cumplimiento de los plazos o el alcance del proyecto.

---

## CLÁUSULA OCTAVA - OBLIGACIONES DEL CONTRATANTE

a) Pagar los honorarios en los términos establecidos en la CLÁUSULA TERCERA del presente contrato.
b) Facilitar a EL CONTRATISTA, de manera oportuna, el acceso a la información, insumos, contenidos y recursos necesarios para la ejecución del contrato.
c) Designar una persona de contacto con capacidad de decisión para la comunicación con EL CONTRATISTA durante la ejecución del proyecto.
d) Dar respuesta a las entregas dentro de los plazos establecidos en el PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA.
e) Cumplir con las demás obligaciones y condiciones previstas en el presente contrato y sus anexos.

---

## CLÁUSULA NOVENA - DERECHOS PATRIMONIALES Y DERECHOS DE EXPLOTACIÓN

En virtud del presente contrato, EL CONTRATANTE adquiere, de manera exclusiva y sin limitación alguna, todos los derechos patrimoniales y de explotación sobre el producto software desarrollado a la medida bajo el presente contrato, incluyendo, pero sin limitarse a, derechos de uso, reproducción, modificación, transformación, adaptación, distribución, comercialización, traducción, disposición, exportación, edición, comunicación pública y cualquier otra forma de explotación o uso por cualquier medio, para cualquier fin y sin restricción territorial, por todo el tiempo de protección legal conforme a la normatividad colombiana vigente.

Estos derechos se transfieren de manera permanente desde el momento de la entrega y aceptación del software, con excepción de los elementos descritos en el PARÁGRAFO SEGUNDO de la presente cláusula, y sin que haya lugar a pago adicional a favor de EL CONTRATISTA, más allá de los montos establecidos en la CLÁUSULA TERCERA.

### Parágrafo Primero - Uso por el Contratante

EL CONTRATANTE podrá utilizar los resultados parciales y finales del proyecto para adaptarlos, modificarlos o integrarlos en cualquier tipo de producto, proyecto o aplicación que considere necesario, sin requerir autorización adicional de EL CONTRATISTA y sin que ello genere derecho a contraprestación adicional, siempre que se encuentre al día en el cumplimiento de sus obligaciones de pago conforme a la CLÁUSULA TERCERA.

### Parágrafo Segundo - Excepciones a la Cesión de Derechos

Quedan excluidos de la cesión de derechos prevista en la presente cláusula los siguientes elementos, cuya propiedad intelectual permanecerá en cabeza de EL CONTRATISTA:

a) Componentes, módulos, librerías y frameworks desarrollados por EL CONTRATISTA con anterioridad al presente contrato o de forma independiente a este.
b) Herramientas genéricas, utilidades y código base reutilizable que formen parte del acervo tecnológico de EL CONTRATISTA y que no hayan sido desarrollados exclusivamente para el presente proyecto.
c) Metodologías, procesos, flujos de trabajo y prácticas de desarrollo empleadas por EL CONTRATISTA en la ejecución del contrato.
d) Conocimiento técnico (know-how), experiencia profesional, habilidades y competencias adquiridas o perfeccionadas por EL CONTRATISTA durante la ejecución del contrato.
e) Diseños de arquitectura, patrones de diseño y soluciones técnicas de carácter genérico que no sean exclusivas del producto desarrollado para EL CONTRATANTE.

Sobre los componentes descritos en los literales a) y b), EL CONTRATANTE recibirá una licencia de uso perpetua, irrevocable, no exclusiva y sin costo adicional, que le permitirá utilizar, modificar e integrar dichos elementos dentro del producto software entregado y sus derivados, sin que esta licencia se extienda a su comercialización como productos independientes.

---

## CLÁUSULA DÉCIMA - CONFIDENCIALIDAD

Ambas partes se obligan a mantener la confidencialidad sobre toda la información que conozcan o a la que tengan acceso con ocasión del presente contrato, con independencia del medio en el cual se encuentre soportada. En adelante, la parte que revela información se denominará PARTE REVELADORA y la que la recibe, PARTE RECEPTORA.

Se tendrá como información confidencial cualquier información no divulgada que posea legítimamente la PARTE REVELADORA y que pueda usarse en alguna actividad académica, productiva, industrial o comercial y que sea susceptible de comunicarse a un tercero. Sin fines restrictivos, la información confidencial podrá versar sobre invenciones, modelos de utilidad, programas de software, fórmulas, métodos, know-how, procesos, diseños, metodologías, arquitecturas técnicas, nuevos productos, trabajos en desarrollo, requisitos de comercialización, planes de mercadeo, estrategias comerciales, información financiera, nombres de clientes y proveedores existentes y potenciales, así como toda otra información que cualquiera de las partes identifique como confidencial.

La información confidencial incluye también toda información recibida de terceros que la PARTE RECEPTORA esté obligada a tratar como confidencial.

La obligación de confidencialidad no aplica sobre aquella información que:

a) Sea o llegue a ser del dominio público sin que medie acto u omisión de la PARTE RECEPTORA.
b) Estuviese en posesión legítima de la PARTE RECEPTORA con anterioridad a su divulgación y no hubiese sido obtenida de forma directa o indirecta de la PARTE REVELADORA.
c) Sea legalmente divulgada por un tercero que no esté sujeto a restricciones en cuanto a su divulgación y la haya obtenido de buena fe.
d) Deba ser divulgada por orden judicial o requerimiento de autoridad competente, en cuyo caso la PARTE RECEPTORA notificará a la PARTE REVELADORA con la mayor antelación posible.

La obligación de confidencialidad permanecerá vigente durante la ejecución del contrato y por un periodo de dos (2) años contados a partir de su terminación por cualquier causa.

---

## CLÁUSULA DÉCIMA PRIMERA - PROTECCIÓN Y TRATAMIENTO DE DATOS PERSONALES

EL CONTRATISTA asume la obligación de proteger los datos personales a los que acceda con ocasión del presente contrato, en cumplimiento de la Ley 1581 de 2012 y sus decretos reglamentarios. Para tal efecto, EL CONTRATISTA deberá:

a) Adoptar las medidas técnicas, administrativas y humanas necesarias para garantizar la seguridad de los datos personales y evitar su adulteración, pérdida, consulta, uso o acceso no autorizado.
b) Limitar el tratamiento de los datos personales de terceros entregados por EL CONTRATANTE exclusivamente a la finalidad propia de sus obligaciones contractuales.
c) Garantizar los derechos de privacidad, intimidad y buen nombre de los titulares de los datos personales.
d) Informar a EL CONTRATANTE de manera inmediata cualquier sospecha de pérdida, fuga, acceso no autorizado o incidente de seguridad que afecte los datos personales a los que haya tenido acceso.
e) Una vez finalizado el contrato, devolver o eliminar los datos personales que le hayan sido entregados, salvo que exista obligación legal de conservarlos.

---

## CLÁUSULA DÉCIMA SEGUNDA - MODIFICACIONES

Cualquier modificación a los términos y condiciones del presente contrato deberá ser acordada entre las partes y requerirá de un "OTROSÍ" firmado por ellas.

---

## CLÁUSULA DÉCIMA TERCERA - ACUERDO

El presente contrato, junto con el Documento Propuesta de Negocio y demás anexos que se suscriban, constituye el acuerdo total entre las partes sobre su objeto. Este acuerdo reemplaza en su integridad y deja sin efecto cualquier otro acuerdo verbal o escrito celebrado con anterioridad entre las partes sobre el mismo objeto.

---

## CLÁUSULA DÉCIMA CUARTA - NOTIFICACIÓN

Para todos los efectos legales y de notificación derivados del presente contrato, las partes establecen los siguientes medios de contacto:

- **EL CONTRATANTE:** correo electrónico {client_email}
- **EL CONTRATISTA:** correo electrónico {contractor_email}

Toda notificación enviada a las direcciones de correo electrónico aquí indicadas se entenderá válidamente surtida al día hábil siguiente a su envío. Cualquier cambio en los datos de notificación deberá ser comunicado por escrito a la otra parte con al menos cinco (5) días hábiles de antelación.

---

## CLÁUSULA DÉCIMA QUINTA - TERMINACIÓN ANTICIPADA

El presente contrato podrá darse por terminado anticipadamente en los siguientes casos:

### Parágrafo Primero - Terminación por Mutuo Acuerdo

Las partes podrán dar por terminado el contrato en cualquier momento mediante acuerdo escrito, en el cual se definirán las condiciones de entrega parcial, liquidación de pagos y demás aspectos pendientes.

### Parágrafo Segundo - Terminación Unilateral por EL CONTRATANTE

EL CONTRATANTE podrá dar por terminado el contrato de forma unilateral, sin necesidad de invocar justa causa, mediante notificación escrita con al menos quince (15) días hábiles de antelación. En este caso:

a) EL CONTRATANTE deberá pagar la totalidad de las fases entregadas y aceptadas, el valor total de la fase en curso al momento de la notificación, y una compensación equivalente al veinte por ciento (20%) del valor de las fases restantes del contrato, a título de lucro cesante.
b) EL CONTRATISTA entregará a EL CONTRATANTE el código fuente y la documentación correspondiente al trabajo efectivamente pagado.
c) Los pagos realizados por fases entregadas y aceptadas no serán reembolsables.
d) La entrega del código fuente y documentación estará condicionada al cumplimiento total de las obligaciones de pago por parte de EL CONTRATANTE.

### Parágrafo Tercero - Terminación Unilateral por EL CONTRATISTA

EL CONTRATISTA podrá dar por terminado el contrato de forma unilateral, mediante notificación escrita con al menos quince (15) días hábiles de antelación, en los siguientes casos:

a) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario.
b) Cuando EL CONTRATANTE incumpla reiteradamente sus obligaciones contractuales, afectando de manera sustancial la ejecución del proyecto.
c) Cuando EL CONTRATANTE no suministre la información, insumos o recursos necesarios para la ejecución del contrato dentro de un plazo razonable, causando una paralización efectiva del proyecto por más de veinte (20) días hábiles.

En caso de terminación por cualquiera de estas causas, EL CONTRATISTA conservará la totalidad de los pagos recibidos hasta la fecha y tendrá derecho al pago del trabajo ejecutado en la fase en curso. La entrega del trabajo realizado estará sujeta al cumplimiento de las obligaciones de pago pendientes.

### Parágrafo Cuarto - Suspensión por Mora

Sin perjuicio de lo anterior, EL CONTRATISTA podrá suspender la ejecución del contrato cuando EL CONTRATANTE presente mora en los pagos por un periodo superior a quince (15) días calendario, sin que dicha suspensión constituya incumplimiento contractual. La ejecución se reanudará una vez EL CONTRATANTE se ponga al día en sus obligaciones de pago, y los plazos de entrega se ajustarán en un periodo equivalente al de la suspensión.

---

## CLÁUSULA DÉCIMA SEXTA - INCUMPLIMIENTO

En caso de que cualquiera de las partes incumpla una o varias de las obligaciones derivadas del presente contrato, la parte afectada deberá notificar por escrito a la parte incumplida, describiendo el incumplimiento de manera detallada.

### Parágrafo Primero - Plazo para Subsanar

La parte incumplida dispondrá de un plazo de quince (15) días hábiles, contados a partir del día siguiente a la recepción de la notificación, para subsanar el incumplimiento. Tratándose de obligaciones de pago, el plazo para subsanar será de diez (10) días hábiles.

### Parágrafo Segundo - Consecuencias del Incumplimiento No Subsanado

Si transcurrido el plazo correspondiente el incumplimiento no ha sido subsanado, la parte afectada podrá:

a) Dar por terminado el contrato conforme a lo establecido en la CLÁUSULA DÉCIMA QUINTA, sin perjuicio de las acciones legales a que haya lugar.
b) Exigir el cumplimiento de las obligaciones pendientes junto con la indemnización de los perjuicios causados, incluyendo el daño emergente y el lucro cesante, conforme a la legislación civil colombiana y sujeto a los límites establecidos en la CLÁUSULA DÉCIMA NOVENA.

### Parágrafo Tercero - Derecho de Retención

EL CONTRATISTA podrá retener el código fuente, la documentación técnica y los demás entregables pendientes de entrega cuando EL CONTRATANTE se encuentre en mora en el cumplimiento de sus obligaciones de pago. Esta retención no constituirá incumplimiento contractual por parte de EL CONTRATISTA y se mantendrá hasta que EL CONTRATANTE cumpla la totalidad de sus obligaciones de pago, incluyendo los intereses de mora a que haya lugar conforme a la CLÁUSULA TERCERA.

---

## CLÁUSULA DÉCIMA SÉPTIMA - RESOLUCIÓN DE CONFLICTOS

Toda controversia o diferencia que surja entre las partes con ocasión del presente contrato, su interpretación, ejecución o terminación, se resolverá conforme al siguiente procedimiento:

1. **Negociación directa:** Las partes intentarán resolver la controversia de manera directa y de buena fe dentro de un plazo de quince (15) días hábiles contados a partir de la notificación escrita de la controversia.
2. **Conciliación:** Si la negociación directa no resuelve la controversia, las partes acudirán a un centro de conciliación legalmente establecido en la ciudad de {contract_city}, Colombia. Los costos de la conciliación serán asumidos por partes iguales.
3. **Jurisdicción ordinaria:** Si la conciliación no prospera dentro de los treinta (30) días calendario siguientes a la solicitud, las partes someterán la controversia a la jurisdicción civil ordinaria de la ciudad de {contract_city}, Colombia, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.

Las costas y gastos judiciales del proceso serán asumidos por la parte vencida, salvo decisión diferente del juez competente.

Durante el trámite de cualquier controversia, las obligaciones de confidencialidad y protección de datos personales previstas en el presente contrato continuarán plenamente vigentes.

---

## CLÁUSULA DÉCIMA OCTAVA - MÉRITO EJECUTIVO

El presente contrato, junto con sus anexos, las actas de entrega y los comprobantes de pago, prestará mérito ejecutivo para el cobro de las obligaciones claras, expresas y exigibles que de él se deriven, sin necesidad de requerimiento judicial previo ni constitución en mora, de conformidad con lo establecido en el artículo 422 del Código General del Proceso colombiano.

Para todos los efectos legales, las partes reconocen que las obligaciones de pago contenidas en el presente contrato y en el Documento Propuesta de Negocio anexo constituyen títulos ejecutivos suficientes para iniciar las acciones de cobro correspondientes.

---

## CLÁUSULA DÉCIMA NOVENA - LIMITACIÓN DE RESPONSABILIDAD

La responsabilidad total de EL CONTRATISTA frente a EL CONTRATANTE, por cualquier concepto derivado del presente contrato, incluyendo pero sin limitarse a incumplimiento, daños, perjuicios, indemnizaciones o reclamaciones de cualquier naturaleza, no podrá exceder en ningún caso el valor total efectivamente pagado por EL CONTRATANTE bajo el presente contrato al momento en que se configure la causa de la reclamación.

### Parágrafo Primero - Exclusión de Daños Indirectos

EL CONTRATISTA no será responsable por daños indirectos, consecuenciales, lucro cesante derivado de la operación del negocio de EL CONTRATANTE, pérdida de datos no ocasionada por negligencia directa de EL CONTRATISTA, ni por daños derivados de la interrupción del negocio de EL CONTRATANTE, salvo en casos de dolo o culpa grave debidamente comprobada.

### Parágrafo Segundo - Exclusión de Responsabilidad por Terceros

EL CONTRATISTA no será responsable por fallas, interrupciones o daños causados por servicios, plataformas o herramientas de terceros, incluyendo pero sin limitarse a proveedores de hosting, pasarelas de pago, servicios de correo electrónico, certificados SSL y cualquier otro componente externo al producto software desarrollado.

### Parágrafo Tercero - Derecho de Reparación

Antes de iniciar cualquier reclamación, acción legal o proceso derivado del presente contrato, EL CONTRATANTE deberá notificar por escrito a EL CONTRATISTA el daño o perjuicio identificado, describiendo con suficiente detalle la situación y la evidencia disponible. A partir del día hábil siguiente a la recepción de dicha notificación, EL CONTRATISTA dispondrá de un plazo de veinte (20) días hábiles para evaluar, proponer y ejecutar las acciones correctivas necesarias para reparar el daño causado.

EL CONTRATISTA tendrá derecho a reparar el daño de manera oportuna y a su costo, siempre que la reparación sea técnicamente viable. Si EL CONTRATISTA repara satisfactoriamente el daño dentro del plazo otorgado, no habrá lugar a indemnización por el concepto reparado.

Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones legales correspondientes en caso de que la reparación no sea satisfactoria o no se realice dentro del plazo establecido.\
"""


def update_default_template(apps, schema_editor):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    template = ContractTemplate.objects.filter(is_default=True).first()
    if template:
        template.content_markdown = NEW_CONTRACT_MARKDOWN
        template.save(update_fields=['content_markdown'])


def revert_default_template(apps, schema_editor):
    ContractTemplate = apps.get_model('content', 'ContractTemplate')
    template = ContractTemplate.objects.filter(is_default=True).first()
    if template:
        template.content_markdown = OLD_CONTRACT_MARKDOWN
        template.save(update_fields=['content_markdown'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0076_add_platform_onboarding_status'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
