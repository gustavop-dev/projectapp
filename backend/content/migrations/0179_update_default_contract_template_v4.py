# Generated 2026-08-10 — update default contract template v4:
#   - Source-code delivery conditioned on paid balances (cl. 9 + new paragraph)
#   - Hosting, maintenance & support service clauses (cl. 20)
#   - Incident SLA levels, report protocol and continuity (cl. 21)
#   - Infrastructure capacity & escalation (cl. 22)
#   - Late-payment protocol with 90-day cure period (cl. 23)
# NOTE: for deals with financed balances, a cumulative hosting penalty per
# unpaid installment (see Vastago Otrosi No. 1, cl. 4) may be added per-deal
# via custom contract or otrosi — intentionally NOT part of this default.

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
3. EL CONTRATANTE deberá reportar los problemas detectados a través del medio de notificación definido en la CLÁUSULA DÉCIMA CUARTA, cumpliendo el protocolo de reporte de incidentes definido en el PARÁGRAFO PRIMERO de la CLÁUSULA VIGÉSIMA PRIMERA. El reporte que no reúna la información allí señalada no dará inicio al cómputo de los plazos del presente parágrafo sino desde el momento en que sea completado.
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
9. Cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte, dicho servicio se regirá por las CLÁUSULAS VIGÉSIMA a VIGÉSIMA TERCERA del presente contrato y por las condiciones económicas definidas en el Documento Propuesta de Negocio.

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

Estos derechos se transfieren de manera permanente desde el momento de la entrega y aceptación del software y el pago íntegro del valor total del presente contrato, con excepción de los elementos descritos en el PARÁGRAFO SEGUNDO de la presente cláusula, y sin que haya lugar a pago adicional a favor de EL CONTRATISTA, más allá de los montos establecidos en la CLÁUSULA TERCERA.

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

### Parágrafo Tercero — Custodia del Código Fuente y Entrega al Pago Total

La entrega material del código fuente, de los repositorios y de la documentación técnica del producto software está condicionada, como condición suspensiva, al pago del cien por ciento (100%) del valor total del presente contrato, incluida la totalidad de sus fases, entregables y demás valores causados y exigibles. Cuando el contrato se estructure en fases o entregables, la entrega, la aceptación o el pago de una fase no habilita, por sí sola, la entrega del código fuente correspondiente a esa fase: la custodia del código permanece en cabeza de EL CONTRATISTA hasta el pago íntegro del contrato, en concordancia con el PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SEXTA y con los literales b) y d) del PARÁGRAFO SEGUNDO de la CLÁUSULA DÉCIMA QUINTA. Esta regla aplica igualmente cuando el esquema de pago contemple financiación, pagos diferidos o saldos exigibles con posterioridad a la entrega.

Mientras dicha condición no se cumpla, EL CONTRATANTE contará con una licencia de uso no exclusiva e intransferible sobre el producto software desplegado, limitada a su operación para los fines propios de su negocio, la cual será irrevocable mientras EL CONTRATANTE se encuentre al día en sus obligaciones de pago. La custodia del código fuente por parte de EL CONTRATISTA durante este periodo constituye una garantía de pago y de integridad técnica, no un título de explotación: no le confiere derecho de uso comercial propio sobre el producto, y no constituirá incumplimiento contractual ni causará mora o indemnización a su cargo.

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

Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones legales correspondientes en caso de que la reparación no sea satisfactoria o no se realice dentro del plazo establecido.

---

## CLÁUSULA VIGÉSIMA — SERVICIO DE HOSTING, MANTENIMIENTO Y SOPORTE

Las CLÁUSULAS VIGÉSIMA a VIGÉSIMA TERCERA aplican únicamente cuando EL CONTRATANTE contrate con EL CONTRATISTA el servicio de hosting, mantenimiento y soporte del producto software, cuyo valor, periodicidad y condiciones económicas se definen en el Documento Propuesta de Negocio o en el documento que las partes suscriban para el efecto. Este servicio comprende la operación de la plataforma en el ambiente de producción, su mantenimiento técnico y el soporte ante incidentes, dentro de la capacidad de infraestructura descrita en la CLÁUSULA VIGÉSIMA SEGUNDA.

### Parágrafo Primero — Inicio del Cobro

El cobro del servicio se causa únicamente a partir de la fecha de puesta en producción del producto software, entendida como el momento en que este queda desplegado y disponible en vivo para la operación de EL CONTRATANTE, fecha que las partes harán constar por escrito. Antes de esa fecha no se causará cobro alguno por este concepto, y el primer periodo del servicio se contará a partir de ella.

### Parágrafo Segundo — Forma y Fecha de Pago

El servicio se paga por periodos anticipados, conforme a la periodicidad definida en el Documento Propuesta de Negocio. EL CONTRATISTA remitirá la cuenta de cobro o factura con una antelación no inferior a diez (10) días calendario al inicio de cada periodo, y EL CONTRATANTE la pagará dentro de los cinco (5) primeros días calendario del periodo que se inicia. El pago se entenderá realizado únicamente cuando los recursos hayan sido recibidos efectivamente por EL CONTRATISTA. La mora en el pago del servicio activa el protocolo previsto en la CLÁUSULA VIGÉSIMA TERCERA.

### Parágrafo Tercero — Reajuste Anual del Valor del Servicio

El valor del servicio se reajustará automáticamente cada primero (1.º) de enero, aplicando al valor vigente del año inmediatamente anterior el porcentaje en que el Gobierno Nacional haya incrementado el salario mínimo mensual legal vigente (SMMLV) para ese año. Si para un año determinado no se decretare incremento del SMMLV, el reajuste se calculará con la variación anual del Índice de Precios al Consumidor (IPC) certificada por el DANE para el año inmediatamente anterior. El valor así reajustado constituye el valor vigente del servicio para todos los efectos del presente contrato. Las partes reconocen que este reajuste no constituye un incremento del precio ni un cobro adicional, sino un mecanismo de corrección monetaria destinado a conservar el valor real de la contraprestación, dado que los costos que sostienen la operación del servicio se incrementan anualmente cuando menos en la misma proporción.

### Parágrafo Cuarto — Responsabilidad Operativa

Durante la vigencia del servicio, EL CONTRATISTA tendrá la responsabilidad de mantener la plataforma operativa dentro de las condiciones técnicas contratadas, siempre que se cumplan todas las siguientes condiciones: (i) EL CONTRATANTE se encuentre al día en sus pagos; (ii) el servicio se encuentre activo y vigente; (iii) no existan intervenciones de terceros no autorizados sobre el código, la infraestructura o los ambientes del producto; (iv) EL CONTRATANTE entregue oportunamente la información, accesos, aprobaciones y recursos necesarios; (v) la operación se desarrolle dentro de la capacidad de infraestructura prevista en la CLÁUSULA VIGÉSIMA SEGUNDA; y (vi) no se presenten los eventos descritos en el PARÁGRAFO SÉPTIMO de la CLÁUSULA VIGÉSIMA PRIMERA.

---

## CLÁUSULA VIGÉSIMA PRIMERA — ATENCIÓN DE INCIDENTES, NIVELES DE SERVICIO Y CONTINUIDAD OPERATIVA

### Parágrafo Primero — Definiciones Operativas

Para todos los efectos del presente contrato, las partes adoptan las siguientes definiciones:

1. **Día hábil:** el comprendido de lunes a viernes, con exclusión de sábados, domingos y días festivos de la República de Colombia conforme a la Ley 51 de 1983 y las normas que la modifiquen.
2. **Hora hábil:** la comprendida entre las nueve (9:00) y las dieciséis (16:00) horas, hora de Bogotá D.C., de un día hábil. Los plazos expresados en horas hábiles corren únicamente dentro de esa franja y se reanudan al inicio de la franja hábil siguiente.
3. **Protocolo de reporte de incidentes:** todo reporte se remitirá por el medio de notificación de la CLÁUSULA DÉCIMA CUARTA e incluirá, en el cuerpo del mensaje o en documento adjunto: a) título corto que identifique el problema; b) dirección (URL) de la página en la que inició la operación; c) dirección (URL) de la página en la que se presentó el problema, si es distinta de la anterior; d) pasos realizados, enumerados en orden; e) lo que ocurrió, con el mensaje de error exacto o una captura de pantalla; f) lo que se esperaba que ocurriera; g) dispositivo y navegador utilizados; y h) fecha y hora aproximada del suceso. Para el cómputo de los plazos, y en concordancia con la CLÁUSULA DÉCIMA CUARTA, el reporte se entenderá recibido al inicio de la franja hábil del día hábil siguiente al de su envío; el reporte que no reúna la información señalada no dará inicio al cómputo sino desde el momento en que sea completado.
4. **Restablecimiento:** se entenderá restablecido el servicio cuando la operación se reanude, aun mediante solución temporal, alternativa o parcial que permita continuar la operación de EL CONTRATANTE. La corrección definitiva de la causa raíz podrá adelantarse con posterioridad, sin que por ello subsista el incidente ni se entienda incumplido el plazo de resolución.
5. **Ventana de mantenimiento programado:** la interrupción planificada del servicio para actualizaciones, parches o labores de mantenimiento, informada a EL CONTRATANTE con una antelación no inferior a veinticuatro (24) horas. No constituye indisponibilidad, incidente ni incumplimiento.

### Parágrafo Segundo — Compromisos Permanentes de Operación

Mientras el servicio de hosting, mantenimiento y soporte se encuentre vigente, EL CONTRATISTA mantendrá sobre la plataforma: (i) monitoreo automatizado y permanente de su disponibilidad, con alertamiento independiente ante la falta de respuesta del servidor; (ii) copias de seguridad periódicas de la base de datos y copia integral del sistema, con retención no inferior a treinta (30) días y pruebas periódicas de restauración; (iii) aplicación de actualizaciones de seguridad y parches del sistema operativo y de los componentes de la plataforma; (iv) vigencia de los certificados de seguridad (SSL/TLS) del dominio de operación; y (v) notificación de los incidentes de seguridad conforme a la CLÁUSULA DÉCIMA PRIMERA, dentro de las veinticuatro (24) horas siguientes a su conocimiento. Estos mecanismos corresponden a las prácticas operativas vigentes de EL CONTRATISTA, quien podrá sustituirlos o actualizarlos por otros de alcance equivalente o superior sin que ello requiera modificación del presente contrato.

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

Cuando por la naturaleza, la complejidad o el origen del incidente la resolución no resulte alcanzable dentro del plazo previsto, EL CONTRATISTA lo informará por escrito a EL CONTRATANTE antes de su vencimiento, señalando la causa y la nueva fecha estimada de restablecimiento, y el plazo se entenderá prorrogado por el término allí indicado, el cual deberá ser razonable y proporcional a la causa invocada; comunicada la prórroga en estos términos, no habrá incumplimiento del plazo original. Asimismo, los plazos de respuesta y de resolución se suspenden, y se reanudan al cesar la causa, mientras subsista: (i) la espera de información, accesos, credenciales, aprobaciones o decisiones a cargo de EL CONTRATANTE; (ii) la ocurrencia de cualquiera de los eventos del PARÁGRAFO SÉPTIMO; (iii) la imposibilidad de reproducir el incidente por insuficiencia de la información reportada; o (iv) la vigencia de las etapas del protocolo previsto en la CLÁUSULA VIGÉSIMA TERCERA, en cuanto a los servicios allí suspendidos.

### Parágrafo Séptimo — Exclusiones, Fuerza Mayor y Caso Fortuito

EL CONTRATISTA no responderá, y no se entenderán incumplidos los compromisos de esta cláusula, cuando la indisponibilidad, la degradación, la demora o el daño obedezcan a fuerza mayor o caso fortuito en los términos del artículo 64 del Código Civil, subrogado por el artículo 1.º de la Ley 95 de 1890, o a circunstancias ajenas a su control razonable, quedando comprendidos, de manera enunciativa y no taxativa: (i) fallas, interrupciones, degradación o suspensión del servicio del proveedor de infraestructura, del centro de datos, de la red o del suministro de energía; (ii) interrupciones de conectividad ajenas a la infraestructura administrada por EL CONTRATISTA, incluidas las de los equipos, redes o dispositivos de EL CONTRATANTE; (iii) ataques informáticos, accesos no autorizados o actos maliciosos de terceros, pese a la adopción de medidas de seguridad razonables; (iv) indisponibilidad, cambios o fallas de servicios de terceros integrados a la plataforma, incluidos los de autoridades tributarias, proveedores de facturación electrónica, pasarelas de pago y proveedores de correo electrónico; (v) actos de autoridad, cambios normativos, desastres naturales, conmoción interna, huelgas o paros ajenos a EL CONTRATISTA; (vi) intervención de terceros no autorizados sobre el código, la infraestructura o los ambientes del producto; (vii) uso de la plataforma fuera de las condiciones contratadas, o datos, cargas o configuraciones provistos por EL CONTRATANTE; y (viii) insuficiencia de los recursos de infraestructura en los términos de la CLÁUSULA VIGÉSIMA SEGUNDA. Durante la ocurrencia de estos eventos se suspenden los plazos y la responsabilidad operativa de EL CONTRATISTA, quien informará la situación a EL CONTRATANTE y desplegará los esfuerzos razonables a su alcance para mitigar sus efectos. Cuando la normalización del servicio dependa de un tercero, los tiempos y las fechas estimadas de restablecimiento quedarán sujetos a los de dicho tercero; EL CONTRATISTA lo informará así a EL CONTRATANTE, hará el seguimiento correspondiente y documentará la causa raíz, las fechas y la solución aplicada en el informe de cierre previsto en el PARÁGRAFO QUINTO. Lo anterior es concordante y acumulativo con las condiciones y exclusiones de la garantía y con la CLÁUSULA DÉCIMA NOVENA.

### Parágrafo Octavo — Responsabilidad frente a Clientes y Usuarios Finales

EL CONTRATISTA no tiene relación contractual alguna con los clientes, usuarios o terceros de EL CONTRATANTE: es EL CONTRATANTE quien contrata con ellos, define sus condiciones comerciales, asume sus compromisos de servicio y responde frente a ellos. En consecuencia, EL CONTRATANTE es el único responsable frente a sus clientes y usuarios finales por la prestación de sus propios servicios, y mantendrá indemne a EL CONTRATISTA de cualquier reclamación, demanda, sanción o requerimiento que aquellos formulen, así como de los costos de defensa que ello le irrogue, salvo en los casos de dolo o culpa grave de EL CONTRATISTA.

### Parágrafo Noveno — Límite de Responsabilidad del Servicio

En ningún caso EL CONTRATISTA responderá por lucro cesante, pérdida de ingresos, de ventas, de negocio o de clientela, daño reputacional, ni por daños indirectos, imprevisibles o consecuenciales de EL CONTRATANTE o de terceros, derivados de la prestación o de la interrupción del servicio de hosting, mantenimiento y soporte, en concordancia con el artículo 1616 del Código Civil. La responsabilidad total y agregada de EL CONTRATISTA por toda reclamación derivada de dicho servicio no excederá el valor efectivamente pagado por EL CONTRATANTE por el último periodo de suscripción del servicio contratado —conforme a la periodicidad definida en el Documento Propuesta de Negocio, sea esta mensual, trimestral, semestral, anual u otra— inmediatamente anterior al hecho que la origine; cuando aún no se hubiere pagado un periodo completo del servicio, el límite será el valor vigente de un (1) periodo de suscripción del servicio. Este límite no aplica en los casos de dolo o culpa grave de EL CONTRATISTA, ni respecto de las obligaciones de confidencialidad y de protección de datos personales, conforme a los artículos 63 y 1522 del Código Civil. En lo no previsto en este parágrafo, rige la CLÁUSULA DÉCIMA NOVENA.

---

## CLÁUSULA VIGÉSIMA SEGUNDA — RECURSOS DE INFRAESTRUCTURA, CAPACIDAD OPERATIVA Y ESCALAMIENTO

El servicio de hosting se presta sobre la infraestructura cuya capacidad técnica se describe en el Documento Propuesta de Negocio. El valor del servicio retribuye la operación, el mantenimiento y el soporte de la plataforma dentro de dicha capacidad; toda operación que la exceda requiere infraestructura de capacidad superior y no se encuentra comprendida en el valor pactado.

### Parágrafo Primero — Monitoreo y Reporte de Consumo

EL CONTRATISTA monitoreará de forma continua el consumo efectivo de procesamiento, memoria, almacenamiento y transferencia de datos, y entregará a EL CONTRATANTE un reporte de consumo con cada periodo de facturación del servicio, así como cada vez que este lo solicite por escrito.

### Parágrafo Segundo — Alerta Temprana

Cuando el consumo de cualquiera de los recursos supere el ochenta por ciento (80%) de su capacidad de forma sostenida durante siete (7) días calendario, EL CONTRATISTA lo notificará a EL CONTRATANTE de manera formal y por escrito, acompañando la evidencia técnica de la medición y una propuesta de escalamiento de la infraestructura, con su especificación técnica y su costo.

### Parágrafo Tercero — Decisión y Costo del Escalamiento

EL CONTRATANTE dispondrá de quince (15) días hábiles, contados desde la notificación anterior, para aprobar por escrito el escalamiento propuesto. La provisión oportuna de los recursos que la operación de su negocio demande es una obligación de EL CONTRATANTE. Aprobado el escalamiento, EL CONTRATISTA contratará y administrará la infraestructura ampliada; el mayor costo se trasladará a EL CONTRATANTE y se facturará de manera separada, sin perjuicio del ajuste del valor del servicio que las partes acuerden por escrito por el mayor esfuerzo operativo.

### Parágrafo Cuarto — Exoneración por Insuficiencia de Recursos

Vencido el plazo del parágrafo anterior sin que EL CONTRATANTE haya aprobado el escalamiento, EL CONTRATISTA quedará exonerado de toda responsabilidad por la degradación del rendimiento, la lentitud, la indisponibilidad, la interrupción del servicio o la pérdida de datos atribuibles a la insuficiencia de los recursos de infraestructura, y quedarán suspendidos los niveles de atención de la CLÁUSULA VIGÉSIMA PRIMERA mientras persista dicha condición, sin que ello constituya incumplimiento imputable a EL CONTRATISTA ni dé lugar a indemnización, descuento o reclamación en su contra. Esta exoneración opera únicamente si EL CONTRATISTA ha cumplido los deberes de monitoreo, reporte y notificación oportuna de los PARÁGRAFOS PRIMERO y SEGUNDO: EL CONTRATISTA responde por medir, advertir y proponer a tiempo; EL CONTRATANTE, por proveer los recursos que su operación demande.

### Parágrafo Quinto — Crecimiento por Nuevos Desarrollos

La incorporación de nuevas fases, módulos o funcionalidades al producto puede incrementar el consumo de recursos. El dimensionamiento de la infraestructura necesaria para soportarlos se evaluará dentro del alcance de cada nuevo desarrollo, conforme al procedimiento de esta cláusula.

---

## CLÁUSULA VIGÉSIMA TERCERA — PROTOCOLO DE MORA Y SUSPENSIÓN DEL SERVICIO

En caso de mora en las obligaciones de pago del servicio de hosting, mantenimiento y soporte, EL CONTRATISTA aplicará el siguiente protocolo escalonado, que constituye el único procedimiento por el cual puede suspenderse la operación de la plataforma por causa de dicha mora. Los plazos se cuentan en días calendario de mora, desde el día siguiente al vencimiento del plazo de pago:

| Etapa | Día de mora | Actuación de EL CONTRATISTA | Efecto sobre la operación |
|---|---|---|---|
| 1 — Aviso | Día 1 | Aviso formal de mora al medio de notificación de EL CONTRATANTE, con el detalle de la obligación vencida y los intereses causados | Ninguno. Todos los servicios continúan con normalidad |
| 2 — Suspensión de evolución | Día 30 | Suspensión del desarrollo de nuevas funcionalidades, de los desarrollos evolutivos, de las actualizaciones y del soporte no crítico | La plataforma sigue operando. Se conservan disponibilidad, copias de seguridad y atención de incidentes CRÍTICOS |
| 3 — Suspensión de servicios | Día 60 | Suspensión del mantenimiento y del soporte, conservando únicamente la disponibilidad de la plataforma y las copias de seguridad. Remisión del preaviso formal de suspensión de la operación | La plataforma sigue operando |
| 4 — Vencimiento del plazo de cura | Día 90 | EL CONTRATISTA queda facultado para suspender la operación de la plataforma, previo aviso escrito con quince (15) días calendario de antelación, y para dar por terminado el servicio o el contrato conforme a la CLÁUSULA DÉCIMA QUINTA | Agotado el preaviso, cesa la operación |

### Parágrafo Primero — Continuidad Durante el Periodo de Cura

Durante las etapas 1, 2 y 3 del protocolo —los primeros noventa (90) días calendario de mora— lo que se suspende es la evolución, el soporte y el mantenimiento, y nunca el uso operativo del producto ya desplegado. EL CONTRATISTA reconoce que la operación de EL CONTRATANTE, y la de los clientes de este cuando los tenga, dependen de la continuidad de la plataforma, y asume el compromiso de no interrumpirla dentro del periodo de cura.

### Parágrafo Segundo — Plazo Máximo de Cura y Obligaciones Durante la Mora

El plazo máximo para normalizar los pagos es de noventa (90) días calendario contados desde el primer día de mora; la mora en varias obligaciones simultáneas no lo amplía, y el plazo se cuenta desde la primera obligación impagada que permanezca sin pago. El transcurso del protocolo no suspende la causación de las obligaciones económicas: los periodos del servicio que se inicien durante el protocolo se causan y se facturan íntegramente, por cuanto el servicio continúa prestándose, y los intereses de mora se causan de manera independiente sobre cada obligación incumplida. El periodo de cura es un término de tolerancia operativa y no constituye condonación, aplazamiento ni novación de las obligaciones de EL CONTRATANTE.

### Parágrafo Tercero — Reanudación

Pagada la totalidad de las obligaciones vencidas junto con sus intereses, EL CONTRATISTA reanudará los servicios suspendidos dentro de los cinco (5) días hábiles siguientes a la verificación del pago, y el protocolo se entenderá agotado sin efectos ulteriores.

### Parágrafo Cuarto — Salida Ordenada

Si se llegare a la suspensión de la operación prevista en la etapa 4, EL CONTRATISTA entregará a EL CONTRATANTE, dentro del preaviso de quince (15) días calendario, una exportación completa de sus datos operativos alojados en la plataforma, en formato estándar de intercambio, y los conservará por treinta (30) días calendario adicionales antes de su eliminación definitiva. Esta salida ordenada no habilita la entrega del código fuente cuando existan saldos pendientes, conforme al PARÁGRAFO TERCERO de la CLÁUSULA NOVENA y al PARÁGRAFO TERCERO de la CLÁUSULA DÉCIMA SEXTA, ni extingue las obligaciones económicas pendientes de EL CONTRATANTE.

### Parágrafo Quinto — Concordancia

Este protocolo rige la suspensión de la operación de la plataforma por mora en las obligaciones del servicio. Los intereses de mora previstos en la CLÁUSULA TERCERA, la suspensión y la terminación previstas en la CLÁUSULA DÉCIMA QUINTA para las obligaciones del desarrollo, y el derecho de retención de la CLÁUSULA DÉCIMA SEXTA conservan su aplicación en sus propios ámbitos.\
"""


# ---------------------------------------------------------------------------
# Previous template (v3, from migration 0077)
# ---------------------------------------------------------------------------
OLD_CONTRACT_MARKDOWN = """\
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
        ('content', '0178_recurringpayment_custom_months_and_more'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
