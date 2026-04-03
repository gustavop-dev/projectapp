# Generated data migration — update default contract template

from django.db import migrations


NEW_CONTRACT_MARKDOWN = """\
Entre las partes, por un lado **{client_full_name}** identificado con número de cédula {client_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATANTE**, y por el otro, **{contractor_full_name}** identificado con número de cédula {contractor_cedula}, quien en adelante y para los efectos del presente contrato se denomina como **EL CONTRATISTA**, ambos mayores de edad, identificados como aparece al pie de las firmas, hemos acordado suscribir este contrato de prestación de servicios, el cual se regirá por las siguientes cláusulas:

---

## CLÁUSULA PRIMERA -- OBJETO DEL CONTRATO

EL CONTRATISTA se obliga a prestar, por sus propios medios y con plena autonomía técnica y administrativa, los servicios de desarrollo de software cuyo alcance, actividades, productos y cronograma se detallan en la CLÁUSULA SEGUNDA del presente contrato. Como contraprestación, EL CONTRATANTE pagará a EL CONTRATISTA los honorarios establecidos en la CLÁUSULA TERCERA, conforme a la forma de pago allí definida. El inicio de cada fase de ejecución estará sujeto al cumplimiento de los pagos correspondientes.

---

## CLÁUSULA SEGUNDA -- EJECUCIÓN DEL CONTRATO

Para la adecuada ejecución del presente contrato, EL CONTRATISTA deberá realizar las actividades descritas en los parágrafos siguientes, conforme al plan, los requerimientos y el cronograma señalados por EL CONTRATANTE. Los plazos de ejecución se contarán a partir de la fecha de firma del presente contrato, salvo que se indique lo contrario en el respectivo parágrafo.

El presente contrato tiene por objeto exclusivo el desarrollo de un producto software. Los servicios de hosting, soporte técnico continuo, mantenimiento correctivo y evolutivo posteriores al periodo de garantía, administración de servidores y cualquier otro servicio de operación no forman parte del presente contrato. La prestación de dichos servicios, en caso de ser requerida por EL CONTRATANTE, deberá ser objeto de un acuerdo independiente entre las partes.

### Parágrafo Primero -- Actividades

EL CONTRATISTA ejecutará las siguientes actividades dentro del marco del presente contrato. Las especificaciones técnicas, tecnologías, herramientas y arquitectura se detallan en el Documento Propuesta de Negocio anexo al presente contrato.

1. **Diseño:** Definición de objetivos, diseño de la arquitectura del software y modelado de la solución conforme a los requerimientos de EL CONTRATANTE.
2. **Desarrollo:** Programación e implementación de los componentes del producto software.
3. **Control de calidad:** Ejecución de pruebas para verificar el correcto funcionamiento del software conforme al alcance definido.
4. **Despliegue:** Instalación y puesta en marcha del producto software en el ambiente de producción, sujeto a lo establecido en el PARÁGRAFO SÉPTIMO del presente contrato.
5. **Capacitación:** Orientación a EL CONTRATANTE sobre el uso y operación del producto software entregado.
6. **Entrega:** Entrega formal del código fuente, documentación técnica y demás entregables definidos en el Documento Propuesta de Negocio.

### Parágrafo Segundo -- Productos

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Tercero -- Cronograma, Roles y Entregables

ANEXO ADJUNTO: Documento Propuesta de Negocio

### Parágrafo Cuarto -- Notificación de Entrega

EL CONTRATISTA notificará a EL CONTRATANTE cada entrega, adjuntando la documentación, código y enlaces necesarios, al correo electrónico definido en la CLÁUSULA DÉCIMA CUARTA.

### Parágrafo Quinto -- Entrega a Satisfacción

Una vez realizada la notificación de entrega indicada en el PARÁGRAFO CUARTO, se seguirá el siguiente procedimiento de aceptación:

1. **Revisión:** EL CONTRATANTE dispondrá de cuatro (4) días hábiles, contados a partir del día siguiente a la notificación, para revisar el entregable y comunicar sus observaciones o solicitudes de ajuste a través del medio definido en la CLÁUSULA DÉCIMA CUARTA. Las observaciones deberán limitarse al alcance definido en el PARÁGRAFO SEGUNDO.
2. **Corrección:** Una vez recibidas las observaciones, EL CONTRATISTA dispondrá de ocho (8) días hábiles, contados a partir del día siguiente a su recepción, para atender los ajustes solicitados y notificar nuevamente a EL CONTRATANTE.
3. **Rondas de revisión:** El procedimiento descrito en los numerales 1 y 2 podrá repetirse hasta un máximo de tres (3) rondas de revisión por cada entregable.
4. **Aceptación tácita:** Si EL CONTRATANTE no comunica observaciones dentro de los cuatro (4) días hábiles siguientes a cualquier notificación de entrega, se entenderá que el entregable ha sido recibido a satisfacción.
5. **Agotamiento de rondas:** Una vez agotadas las tres (3) rondas de revisión, las partes acordarán por escrito las condiciones para resolver las observaciones pendientes, lo cual podrá formalizarse mediante un OTROSÍ al presente contrato.

### Parágrafo Sexto -- Garantía y Soporte

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

### Parágrafo Séptimo -- Hosting y Despliegue

1. EL CONTRATANTE tendrá el derecho de alojar el producto software en el proveedor de hosting de su preferencia.
2. Se recomienda que el producto software sea alojado en ambientes que garanticen su correcta operación y cumplan con estándares de calidad tales como disponibilidad, rendimiento, escalabilidad, seguridad y certificados SSL.
3. La garantía y el soporte definidos en el PARÁGRAFO SEXTO aplicarán siempre que se cumplan las condiciones establecidas en los numerales 6 y 7 de dicho parágrafo, independientemente del proveedor de hosting utilizado.
4. Dado que el alcance del presente contrato comprende el desarrollo del producto software y no su despliegue, no es obligación de EL CONTRATISTA realizar instalaciones en dominios operativos diferentes a los de Project App.
5. En caso de que EL CONTRATANTE solicite la instalación y despliegue del producto en un ambiente diferente a los dominios de Project App, dicho ambiente deberá cumplir con los requerimientos técnicos definidos en el Documento Propuesta de Negocio. Este servicio tendrá un costo adicional equivalente al doce por ciento (12%) del valor total del presente contrato.

### Parágrafo Octavo -- Exclusiones

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

### Parágrafo Noveno -- Condiciones de Pago y Entrega

1. La entrega de cada producto está sujeta al pago oportuno por parte de EL CONTRATANTE. Un retraso en los pagos causará un aplazamiento equivalente en los plazos de entrega del siguiente entregable.
2. Cada pago se documentará mediante un acta de entrega y un comprobante de transferencia con la fecha de la transacción.
3. Una vez confirmado el pago correspondiente, se dará inicio al siguiente periodo de desarrollo conforme al cronograma definido en el Documento Propuesta de Negocio.

---

## CLÁUSULA TERCERA -- PRECIO Y FORMA DE PAGO

El valor total del presente contrato, el calendario de pagos y los entregables asociados a cada pago se encuentran definidos en el Documento Propuesta de Negocio anexo al presente contrato. Todos los valores se expresan en pesos colombianos (COP).

### Parágrafo Primero

Los pagos se realizarán mediante transferencia bancaria a la cuenta {bank_name} {bank_account_type} No. {bank_account_number} a nombre de EL CONTRATISTA identificado con número de cédula {contractor_cedula}.

### Parágrafo Segundo

En caso de mora en los pagos por parte de EL CONTRATANTE, se causarán intereses de mora a la tasa máxima legal vigente, sin perjuicio del aplazamiento de los plazos de entrega conforme a lo establecido en el PARÁGRAFO NOVENO de la CLÁUSULA SEGUNDA.

### Parágrafo Tercero

Los pagos correspondientes a fases entregadas y aceptadas conforme al procedimiento del PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA no serán reembolsables.

---

## CLÁUSULA CUARTA -- SUBCONTRATACIÓN

EL CONTRATISTA podrá subcontratar total o parcialmente la ejecución del objeto contractual sin necesidad de autorización previa de EL CONTRATANTE. En todo caso, EL CONTRATISTA será el único responsable ante EL CONTRATANTE por el cumplimiento de las obligaciones derivadas del presente contrato, así como por las cargas contractuales, laborales y de seguridad social que se generen respecto del personal que vincule para tal fin.

---

## CLÁUSULA QUINTA -- SUPERVISIÓN

EL CONTRATANTE podrá supervisar la ejecución del presente contrato. Para ello, las partes definirán de común acuerdo un medio y una periodicidad de comunicación para la actualización del estado del proyecto. EL CONTRATANTE podrá formular observaciones, las cuales serán analizadas conjuntamente con EL CONTRATISTA. La supervisión por parte de EL CONTRATANTE no implicará subordinación ni afectará la autonomía técnica y administrativa de EL CONTRATISTA.

---

## CLÁUSULA SEXTA -- EXCLUSIÓN DE LA RELACIÓN LABORAL

Dada la naturaleza del presente contrato, no existirá relación laboral alguna entre EL CONTRATANTE y EL CONTRATISTA, ni con el personal que este vincule para apoyar la ejecución del objeto contractual. EL CONTRATISTA ejecutará el contrato de forma independiente y con plena autonomía técnica y administrativa. EL CONTRATISTA será responsable del pago de sus propias obligaciones en materia de seguridad social integral (salud, pensión y riesgos laborales), así como de las correspondientes al personal que subcontrate.

---

## CLÁUSULA SÉPTIMA -- OBLIGACIONES DEL CONTRATISTA

a) Cumplir oportunamente el objeto y las actividades definidas en la CLÁUSULA SEGUNDA del presente contrato.
b) Aportar su experiencia y conocimientos para la adecuada ejecución del contrato.
c) Entregar el código fuente, la documentación técnica y los demás entregables conforme a lo establecido en el Documento Propuesta de Negocio.
d) Cumplir con la garantía y soporte en los términos del PARÁGRAFO SEXTO de la CLÁUSULA SEGUNDA.
e) Absolver las consultas de EL CONTRATANTE relacionadas con el objeto del contrato.
f) Asistir a las reuniones en los días y horas previamente acordados entre las partes.
g) Informar oportunamente a EL CONTRATANTE sobre cualquier circunstancia que pueda afectar el cumplimiento de los plazos o el alcance del proyecto.

---

## CLÁUSULA OCTAVA -- OBLIGACIONES DEL CONTRATANTE

a) Pagar los honorarios en los términos establecidos en la CLÁUSULA TERCERA del presente contrato.
b) Facilitar a EL CONTRATISTA, de manera oportuna, el acceso a la información, insumos, contenidos y recursos necesarios para la ejecución del contrato.
c) Designar una persona de contacto con capacidad de decisión para la comunicación con EL CONTRATISTA durante la ejecución del proyecto.
d) Dar respuesta a las entregas dentro de los plazos establecidos en el PARÁGRAFO QUINTO de la CLÁUSULA SEGUNDA.
e) Cumplir con las demás obligaciones y condiciones previstas en el presente contrato y sus anexos.

---

## CLÁUSULA NOVENA -- DERECHOS PATRIMONIALES Y DERECHOS DE EXPLOTACIÓN

En virtud del presente contrato, EL CONTRATANTE adquiere, de manera exclusiva y sin limitación alguna, todos los derechos patrimoniales y de explotación sobre el producto software desarrollado a la medida bajo el presente contrato, incluyendo, pero sin limitarse a, derechos de uso, reproducción, modificación, transformación, adaptación, distribución, comercialización, traducción, disposición, exportación, edición, comunicación pública y cualquier otra forma de explotación o uso por cualquier medio, para cualquier fin y sin restricción territorial, por todo el tiempo de protección legal conforme a la normatividad colombiana vigente.

Estos derechos se transfieren de manera permanente desde el momento de la entrega y aceptación del software, con excepción de los elementos descritos en el PARÁGRAFO SEGUNDO de la presente cláusula, y sin que haya lugar a pago adicional a favor de EL CONTRATISTA, más allá de los montos establecidos en la CLÁUSULA TERCERA.

### Parágrafo Primero -- Uso por el Contratante

EL CONTRATANTE podrá utilizar los resultados parciales y finales del proyecto para adaptarlos, modificarlos o integrarlos en cualquier tipo de producto, proyecto o aplicación que considere necesario, sin requerir autorización adicional de EL CONTRATISTA y sin que ello genere derecho a contraprestación adicional, siempre que se encuentre al día en el cumplimiento de sus obligaciones de pago conforme a la CLÁUSULA TERCERA.

### Parágrafo Segundo -- Excepciones a la Cesión de Derechos

Quedan excluidos de la cesión de derechos prevista en la presente cláusula los siguientes elementos, cuya propiedad intelectual permanecerá en cabeza de EL CONTRATISTA:

a) Componentes, módulos, librerías y frameworks desarrollados por EL CONTRATISTA con anterioridad al presente contrato o de forma independiente a este.
b) Herramientas genéricas, utilidades y código base reutilizable que formen parte del acervo tecnológico de EL CONTRATISTA y que no hayan sido desarrollados exclusivamente para el presente proyecto.
c) Metodologías, procesos, flujos de trabajo y prácticas de desarrollo empleadas por EL CONTRATISTA en la ejecución del contrato.
d) Conocimiento técnico (know-how), experiencia profesional, habilidades y competencias adquiridas o perfeccionadas por EL CONTRATISTA durante la ejecución del contrato.
e) Diseños de arquitectura, patrones de diseño y soluciones técnicas de carácter genérico que no sean exclusivas del producto desarrollado para EL CONTRATANTE.

Sobre los componentes descritos en los literales a) y b), EL CONTRATANTE recibirá una licencia de uso perpetua, irrevocable, no exclusiva y sin costo adicional, que le permitirá utilizar, modificar e integrar dichos elementos dentro del producto software entregado y sus derivados, sin que esta licencia se extienda a su comercialización como productos independientes.

---

## CLÁUSULA DÉCIMA -- CONFIDENCIALIDAD

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

## CLÁUSULA DÉCIMA PRIMERA -- PROTECCIÓN Y TRATAMIENTO DE DATOS PERSONALES

EL CONTRATISTA asume la obligación de proteger los datos personales a los que acceda con ocasión del presente contrato, en cumplimiento de la Ley 1581 de 2012 y sus decretos reglamentarios. Para tal efecto, EL CONTRATISTA deberá:

a) Adoptar las medidas técnicas, administrativas y humanas necesarias para garantizar la seguridad de los datos personales y evitar su adulteración, pérdida, consulta, uso o acceso no autorizado.
b) Limitar el tratamiento de los datos personales de terceros entregados por EL CONTRATANTE exclusivamente a la finalidad propia de sus obligaciones contractuales.
c) Garantizar los derechos de privacidad, intimidad y buen nombre de los titulares de los datos personales.
d) Informar a EL CONTRATANTE de manera inmediata cualquier sospecha de pérdida, fuga, acceso no autorizado o incidente de seguridad que afecte los datos personales a los que haya tenido acceso.
e) Una vez finalizado el contrato, devolver o eliminar los datos personales que le hayan sido entregados, salvo que exista obligación legal de conservarlos.

---

## CLÁUSULA DÉCIMA SEGUNDA -- MODIFICACIONES

Cualquier modificación a los términos y condiciones del presente contrato deberá ser acordada entre las partes y requerirá de un "OTROSÍ" firmado por ellas.

---

## CLÁUSULA DÉCIMA TERCERA -- ACUERDO

El presente contrato, junto con el Documento Propuesta de Negocio y demás anexos que se suscriban, constituye el acuerdo total entre las partes sobre su objeto. Este acuerdo reemplaza en su integridad y deja sin efecto cualquier otro acuerdo verbal o escrito celebrado con anterioridad entre las partes sobre el mismo objeto.

---

## CLÁUSULA DÉCIMA CUARTA -- NOTIFICACIÓN

Para todos los efectos legales y de notificación derivados del presente contrato, las partes establecen los siguientes medios de contacto:

- **EL CONTRATANTE:** correo electrónico {client_email}
- **EL CONTRATISTA:** correo electrónico {contractor_email}

Toda notificación enviada a las direcciones de correo electrónico aquí indicadas se entenderá válidamente surtida al día hábil siguiente a su envío. Cualquier cambio en los datos de notificación deberá ser comunicado por escrito a la otra parte con al menos cinco (5) días hábiles de antelación.

---

## CLÁUSULA DÉCIMA QUINTA -- TERMINACIÓN ANTICIPADA

El presente contrato podrá darse por terminado anticipadamente en los siguientes casos:

### Parágrafo Primero -- Terminación por Mutuo Acuerdo

Las partes podrán dar por terminado el contrato en cualquier momento mediante acuerdo escrito, en el cual se definirán las condiciones de entrega parcial, liquidación de pagos y demás aspectos pendientes.

### Parágrafo Segundo -- Terminación Unilateral por EL CONTRATANTE

EL CONTRATANTE podrá dar por terminado el contrato de forma unilateral, sin necesidad de invocar justa causa, mediante notificación escrita con al menos quince (15) días hábiles de antelación. En este caso:

a) EL CONTRATANTE deberá pagar la totalidad de las fases entregadas y aceptadas, el valor total de la fase en curso al momento de la notificación, y una compensación equivalente al veinte por ciento (20%) del valor de las fases restantes del contrato, a título de lucro cesante.
b) EL CONTRATISTA entregará a EL CONTRATANTE el código fuente y la documentación correspondiente al trabajo efectivamente pagado.
c) Los pagos realizados por fases entregadas y aceptadas no serán reembolsables.
d) La entrega del código fuente y documentación estará condicionada al cumplimiento total de las obligaciones de pago por parte de EL CONTRATANTE.

### Parágrafo Tercero -- Terminación Unilateral por EL CONTRATISTA

EL CONTRATISTA podrá dar por terminado el contrato de forma unilateral, mediante notificación escrita con al menos quince (15) días hábiles de antelación, en los siguientes casos:

a) Cuando EL CONTRATANTE incurra en mora en los pagos por un periodo superior a treinta (30) días calendario.
b) Cuando EL CONTRATANTE incumpla reiteradamente sus obligaciones contractuales, afectando de manera sustancial la ejecución del proyecto.
c) Cuando EL CONTRATANTE no suministre la información, insumos o recursos necesarios para la ejecución del contrato dentro de un plazo razonable, causando una paralización efectiva del proyecto por más de veinte (20) días hábiles.

En caso de terminación por cualquiera de estas causas, EL CONTRATISTA conservará la totalidad de los pagos recibidos hasta la fecha y tendrá derecho al pago del trabajo ejecutado en la fase en curso. La entrega del trabajo realizado estará sujeta al cumplimiento de las obligaciones de pago pendientes.

### Parágrafo Cuarto -- Suspensión por Mora

Sin perjuicio de lo anterior, EL CONTRATISTA podrá suspender la ejecución del contrato cuando EL CONTRATANTE presente mora en los pagos por un periodo superior a quince (15) días calendario, sin que dicha suspensión constituya incumplimiento contractual. La ejecución se reanudará una vez EL CONTRATANTE se ponga al día en sus obligaciones de pago, y los plazos de entrega se ajustarán en un periodo equivalente al de la suspensión.

---

## CLÁUSULA DÉCIMA SEXTA -- INCUMPLIMIENTO

En caso de que cualquiera de las partes incumpla una o varias de las obligaciones derivadas del presente contrato, la parte afectada deberá notificar por escrito a la parte incumplida, describiendo el incumplimiento de manera detallada.

### Parágrafo Primero -- Plazo para Subsanar

La parte incumplida dispondrá de un plazo de quince (15) días hábiles, contados a partir del día siguiente a la recepción de la notificación, para subsanar el incumplimiento. Tratándose de obligaciones de pago, el plazo para subsanar será de diez (10) días hábiles.

### Parágrafo Segundo -- Consecuencias del Incumplimiento No Subsanado

Si transcurrido el plazo correspondiente el incumplimiento no ha sido subsanado, la parte afectada podrá:

a) Dar por terminado el contrato conforme a lo establecido en la CLÁUSULA DÉCIMA QUINTA, sin perjuicio de las acciones legales a que haya lugar.
b) Exigir el cumplimiento de las obligaciones pendientes junto con la indemnización de los perjuicios causados, incluyendo el daño emergente y el lucro cesante, conforme a la legislación civil colombiana y sujeto a los límites establecidos en la CLÁUSULA DÉCIMA NOVENA.

### Parágrafo Tercero -- Derecho de Retención

EL CONTRATISTA podrá retener el código fuente, la documentación técnica y los demás entregables pendientes de entrega cuando EL CONTRATANTE se encuentre en mora en el cumplimiento de sus obligaciones de pago. Esta retención no constituirá incumplimiento contractual por parte de EL CONTRATISTA y se mantendrá hasta que EL CONTRATANTE cumpla la totalidad de sus obligaciones de pago, incluyendo los intereses de mora a que haya lugar conforme a la CLÁUSULA TERCERA.

---

## CLÁUSULA DÉCIMA SÉPTIMA -- RESOLUCIÓN DE CONFLICTOS

Toda controversia o diferencia que surja entre las partes con ocasión del presente contrato, su interpretación, ejecución o terminación, se resolverá conforme al siguiente procedimiento:

1. **Negociación directa:** Las partes intentarán resolver la controversia de manera directa y de buena fe dentro de un plazo de quince (15) días hábiles contados a partir de la notificación escrita de la controversia.
2. **Conciliación:** Si la negociación directa no resuelve la controversia, las partes acudirán a un centro de conciliación legalmente establecido en la ciudad de {contract_city}, Colombia. Los costos de la conciliación serán asumidos por partes iguales.
3. **Jurisdicción ordinaria:** Si la conciliación no prospera dentro de los treinta (30) días calendario siguientes a la solicitud, las partes someterán la controversia a la jurisdicción civil ordinaria de la ciudad de {contract_city}, Colombia, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.

Las costas y gastos judiciales del proceso serán asumidos por la parte vencida, salvo decisión diferente del juez competente.

Durante el trámite de cualquier controversia, las obligaciones de confidencialidad y protección de datos personales previstas en el presente contrato continuarán plenamente vigentes.

---

## CLÁUSULA DÉCIMA OCTAVA -- MÉRITO EJECUTIVO

El presente contrato, junto con sus anexos, las actas de entrega y los comprobantes de pago, prestará mérito ejecutivo para el cobro de las obligaciones claras, expresas y exigibles que de él se deriven, sin necesidad de requerimiento judicial previo ni constitución en mora, de conformidad con lo establecido en el artículo 422 del Código General del Proceso colombiano.

Para todos los efectos legales, las partes reconocen que las obligaciones de pago contenidas en el presente contrato y en el Documento Propuesta de Negocio anexo constituyen títulos ejecutivos suficientes para iniciar las acciones de cobro correspondientes.

---

## CLÁUSULA DÉCIMA NOVENA -- LIMITACIÓN DE RESPONSABILIDAD

La responsabilidad total de EL CONTRATISTA frente a EL CONTRATANTE, por cualquier concepto derivado del presente contrato, incluyendo pero sin limitarse a incumplimiento, daños, perjuicios, indemnizaciones o reclamaciones de cualquier naturaleza, no podrá exceder en ningún caso el valor total efectivamente pagado por EL CONTRATANTE bajo el presente contrato al momento en que se configure la causa de la reclamación.

### Parágrafo Primero -- Exclusión de Daños Indirectos

EL CONTRATISTA no será responsable por daños indirectos, consecuenciales, lucro cesante derivado de la operación del negocio de EL CONTRATANTE, pérdida de datos no ocasionada por negligencia directa de EL CONTRATISTA, ni por daños derivados de la interrupción del negocio de EL CONTRATANTE, salvo en casos de dolo o culpa grave debidamente comprobada.

### Parágrafo Segundo -- Exclusión de Responsabilidad por Terceros

EL CONTRATISTA no será responsable por fallas, interrupciones o daños causados por servicios, plataformas o herramientas de terceros, incluyendo pero sin limitarse a proveedores de hosting, pasarelas de pago, servicios de correo electrónico, certificados SSL y cualquier otro componente externo al producto software desarrollado.

### Parágrafo Tercero -- Derecho de Reparación

Antes de iniciar cualquier reclamación, acción legal o proceso derivado del presente contrato, EL CONTRATANTE deberá notificar por escrito a EL CONTRATISTA el daño o perjuicio identificado, describiendo con suficiente detalle la situación y la evidencia disponible. A partir del día hábil siguiente a la recepción de dicha notificación, EL CONTRATISTA dispondrá de un plazo de veinte (20) días hábiles para evaluar, proponer y ejecutar las acciones correctivas necesarias para reparar el daño causado.

EL CONTRATISTA tendrá derecho a reparar el daño de manera oportuna y a su costo, siempre que la reparación sea técnicamente viable. Si EL CONTRATISTA repara satisfactoriamente el daño dentro del plazo otorgado, no habrá lugar a indemnización por el concepto reparado.

Este derecho de reparación aplicará incluso en casos de dolo o culpa grave, sin que ello implique renuncia por parte de EL CONTRATANTE a las acciones legales correspondientes en caso de que la reparación no sea satisfactoria o no se realice dentro del plazo establecido.\
"""


# ---------------------------------------------------------------------------
# Old template from migration 0064 (for reversibility)
# ---------------------------------------------------------------------------
OLD_CONTRACT_MARKDOWN = """\
Entre las partes, por un lado {client_full_name} identificado con numero de cedula {client_cedula}, quien en adelante y para los efectos del presente contrato se denomina como EL CONTRATANTE, y por el otro, {contractor_full_name} identificado con numero de cedula {contractor_cedula}, quien en adelante y para los efectos del presente contrato se denomina como EL CONTRATISTA, ambos mayores de edad, identificados como aparece al pie de las firmas, hemos acordado suscribir este contrato de prestacion de servicios, el cual se regira por las siguientes clausulas:

## CLAUSULA PRIMERA -- OBJETO DEL CONTRATO

EL CONTRATISTA se obliga a prestar sus servicios profesionales de desarrollo de software para EL CONTRATANTE, conforme a los terminos y condiciones establecidos en la propuesta comercial aprobada por las partes, la cual hace parte integral del presente contrato. El alcance especifico del proyecto, incluyendo funcionalidades, entregables y cronograma, sera el definido en dicha propuesta.

## CLAUSULA SEGUNDA -- EJECUCION DEL CONTRATO

Para la adecuada ejecucion del objeto contractual, las partes acuerdan las siguientes condiciones:

El presente contrato tiene por objeto exclusivo el desarrollo del software descrito en la propuesta comercial. Cualquier funcionalidad, modulo o servicio adicional no contemplado en dicha propuesta debera ser acordado por escrito entre las partes mediante un otrosi al presente contrato, el cual podra generar costos adicionales.

### Paragrafo Primero -- Actividades

EL CONTRATISTA ejecutara las siguientes actividades principales:

1. Diseno: Elaboracion de la arquitectura del sistema, diseno de interfaces de usuario (UI/UX) y definicion de la estructura de datos conforme a los requerimientos aprobados.
2. Desarrollo: Programacion, codificacion e implementacion de las funcionalidades y modulos definidos en la propuesta comercial, utilizando las tecnologias acordadas.
3. Pruebas: Realizacion de pruebas funcionales, de integracion y de rendimiento para asegurar la calidad y el correcto funcionamiento del software.
4. Despliegue: Instalacion, configuracion y puesta en marcha del software en el ambiente de produccion del CONTRATANTE o en la infraestructura acordada.
5. Capacitacion: Entrega de documentacion tecnica y funcional, asi como sesiones de capacitacion al equipo del CONTRATANTE para el uso y administracion basica del software.

### Paragrafo Segundo -- Plazo

El plazo de ejecucion del contrato sera el establecido en la propuesta comercial aprobada por las partes. Dicho plazo comenzara a contarse a partir de la fecha de firma del presente contrato y del pago del anticipo pactado. Cualquier modificacion al cronograma debera ser acordada por escrito entre las partes.

### Paragrafo Tercero -- Entregables

Los entregables del proyecto seran los definidos en la propuesta comercial. EL CONTRATISTA entregara cada componente conforme al cronograma acordado. EL CONTRATANTE dispondra de un plazo de cinco (5) dias habiles a partir de cada entrega para revisar y aprobar o formular observaciones. Transcurrido dicho plazo sin pronunciamiento, el entregable se considerara aprobado.

### Paragrafo Cuarto -- Metodologia

El desarrollo se realizara bajo una metodologia agil que permita entregas incrementales y retroalimentacion continua del CONTRATANTE. Las reuniones de seguimiento, sprints y demos seran programadas de comun acuerdo entre las partes.

### Paragrafo Quinto -- Ambiente de trabajo

EL CONTRATISTA ejecutara sus actividades de manera remota, salvo que las partes acuerden reuniones presenciales especificas. EL CONTRATISTA utilizara sus propias herramientas, equipos y licencias de software necesarios para la ejecucion del contrato.

### Paragrafo Sexto -- Comunicacion

Las partes mantendran comunicacion fluida a traves de los canales acordados (correo electronico, plataforma de gestion de proyectos, videollamadas). EL CONTRATISTA informara oportunamente sobre el avance del proyecto, riesgos identificados y cualquier situacion que pueda afectar el cumplimiento del cronograma.

### Paragrafo Septimo -- Control de cambios

Toda solicitud de cambio que modifique el alcance, cronograma o presupuesto del proyecto debera ser documentada y aprobada por escrito por ambas partes antes de su implementacion. EL CONTRATISTA evaluara el impacto del cambio y presentara una propuesta de ajuste que incluya tiempo y costo adicional, si aplica.

### Paragrafo Octavo -- Garantia tecnica

EL CONTRATISTA garantiza que el software entregado funcionara conforme a las especificaciones aprobadas durante un periodo de treinta (30) dias calendario posteriores a la entrega final y aprobacion del proyecto. Durante este periodo, EL CONTRATISTA corregira sin costo adicional cualquier defecto o error atribuible a su desarrollo. Esta garantia no cubre errores derivados de modificaciones realizadas por terceros, uso inadecuado del software o cambios en la infraestructura del CONTRATANTE.

### Paragrafo Noveno -- Soporte post-entrega

Una vez finalizado el periodo de garantia, EL CONTRATANTE podra contratar servicios adicionales de soporte, mantenimiento o evolucion del software mediante acuerdos separados. EL CONTRATISTA presentara una propuesta de costos para dichos servicios adicionales.

## CLAUSULA TERCERA -- PRECIO Y FORMA DE PAGO

El valor total del contrato sera el establecido en la propuesta comercial aprobada por las partes. Los pagos se realizaran conforme al esquema de hitos o cuotas definido en dicha propuesta.

### Paragrafo Primero -- Forma de pago

Los pagos se realizaran mediante transferencia bancaria a la cuenta de {bank_name} {bank_account_type} No. {bank_account_number} a nombre de EL CONTRATISTA identificado con cedula {contractor_cedula}. El pago se considerara efectuado en la fecha en que los fondos sean acreditados en dicha cuenta.

### Paragrafo Segundo -- Mora en el pago

En caso de mora en cualquiera de los pagos pactados superior a diez (10) dias calendario, EL CONTRATISTA podra suspender la ejecucion del proyecto hasta tanto se regularice el pago, sin que ello constituya incumplimiento de su parte. El cronograma se ajustara en proporcion al tiempo de suspension.

### Paragrafo Tercero -- Impuestos

Cada parte sera responsable de sus propias obligaciones tributarias derivadas del presente contrato. EL CONTRATISTA emitira la facturacion o cuenta de cobro correspondiente a cada pago, conforme a la normatividad vigente.

## CLAUSULA CUARTA -- SUBCONTRATACION

EL CONTRATISTA podra subcontratar parcialmente la ejecucion de actividades especificas del proyecto, siempre que mantenga la responsabilidad total sobre la calidad y el cumplimiento de los entregables frente a EL CONTRATANTE. La subcontratacion no requerira autorizacion previa del CONTRATANTE, salvo que se trate de la totalidad del objeto contractual.

## CLAUSULA QUINTA -- SUPERVISION

EL CONTRATANTE podra designar un representante o supervisor para el seguimiento del proyecto, quien servira como punto de contacto principal para la comunicacion con EL CONTRATISTA. Dicho supervisor tendra la facultad de aprobar entregables, solicitar ajustes dentro del alcance contratado y participar en las reuniones de seguimiento. La supervision no implica subordinacion laboral ni direccion tecnica sobre la forma en que EL CONTRATISTA ejecuta sus actividades.

## CLAUSULA SEXTA -- EXCLUSION DE LA RELACION LABORAL

El presente contrato es de naturaleza civil y de prestacion de servicios. No genera relacion laboral alguna entre las partes, ni vinculo de subordinacion o dependencia. EL CONTRATISTA actua como profesional independiente, asume sus propios riesgos y es responsable de sus obligaciones en materia de seguridad social, salud y pensiones conforme a la legislacion colombiana vigente.

## CLAUSULA SEPTIMA -- OBLIGACIONES DEL CONTRATISTA

Son obligaciones de EL CONTRATISTA:

a) Ejecutar el objeto del contrato con diligencia, calidad profesional y dentro de los plazos acordados.
b) Entregar el software funcional conforme a las especificaciones aprobadas en la propuesta comercial.
c) Informar oportunamente sobre cualquier riesgo, impedimento o situacion que pueda afectar la ejecucion del proyecto.
d) Mantener la confidencialidad de toda la informacion del CONTRATANTE a la que tenga acceso en desarrollo del contrato.
e) Proveer la documentacion tecnica y funcional del software desarrollado.
f) Cumplir con las normas de proteccion de datos personales aplicables.
g) Emitir la facturacion o cuenta de cobro correspondiente a cada pago.

## CLAUSULA OCTAVA -- OBLIGACIONES DEL CONTRATANTE

Son obligaciones de EL CONTRATANTE:

a) Suministrar oportunamente la informacion, accesos y recursos necesarios para la ejecucion del proyecto.
b) Realizar los pagos en los plazos y condiciones pactados en la propuesta comercial.
c) Designar un representante o punto de contacto para la comunicacion con EL CONTRATISTA.
d) Revisar y aprobar los entregables dentro de los plazos establecidos, o formular observaciones oportunas y precisas.
e) No utilizar el software desarrollado para fines distintos a los acordados, ni permitir su uso por terceros no autorizados durante la vigencia del contrato.

## CLAUSULA NOVENA -- DERECHOS PATRIMONIALES

Una vez recibido el pago total del valor del contrato, EL CONTRATISTA cedera a EL CONTRATANTE los derechos patrimoniales de autor sobre el software desarrollado especificamente para el proyecto, incluyendo el codigo fuente, la documentacion tecnica y los disenos creados en ejecucion del presente contrato.

### Paragrafo Primero

Se exceptuan de esta cesion las librerias, frameworks, herramientas, componentes reutilizables y metodologias preexistentes de EL CONTRATISTA que hayan sido utilizadas en el desarrollo del proyecto. Sobre estos elementos, EL CONTRATANTE recibira una licencia de uso perpetua, no exclusiva e intransferible, limitada al funcionamiento del software contratado.

### Paragrafo Segundo

Los derechos morales de autor corresponden de manera irrenunciable e inalienable a EL CONTRATISTA como creador del software, conforme a la legislacion colombiana de derechos de autor.

## CLAUSULA DECIMA -- CONFIDENCIALIDAD

Las partes se comprometen a mantener estricta confidencialidad sobre toda la informacion tecnica, comercial, financiera y estrategica a la que tengan acceso con ocasion del presente contrato. Esta obligacion se extiende a los empleados, subcontratistas y asesores de cada parte.

La obligacion de confidencialidad permanecera vigente durante la ejecucion del contrato y por un periodo de dos (2) anos posteriores a su terminacion.

No se considerara informacion confidencial aquella que:

a) Sea o se convierta en informacion de dominio publico sin culpa de la parte receptora.
b) Haya sido conocida por la parte receptora con anterioridad a su divulgacion, sin obligacion de confidencialidad.
c) Sea recibida legitimamente de un tercero sin restriccion de divulgacion.
d) Deba ser divulgada por orden judicial o requerimiento de autoridad competente.

## CLAUSULA DECIMA PRIMERA -- PROTECCION DE DATOS

Las partes se comprometen a cumplir con la Ley 1581 de 2012 y sus decretos reglamentarios en materia de proteccion de datos personales. En particular:

a) EL CONTRATISTA tratara los datos personales del CONTRATANTE y sus usuarios unicamente para los fines del presente contrato.
b) EL CONTRATISTA implementara las medidas tecnicas y organizativas adecuadas para proteger los datos personales contra acceso no autorizado, perdida o destruccion.
c) Al terminar el contrato, EL CONTRATISTA devolvera o eliminara los datos personales del CONTRATANTE que obren en su poder, salvo obligacion legal de conservacion.
d) En caso de incidente de seguridad que afecte datos personales, la parte que lo detecte informara a la otra en un plazo maximo de cuarenta y ocho (48) horas.
e) Cada parte sera responsable del tratamiento de datos personales que realice en calidad de responsable o encargado, conforme a la normatividad vigente.

## CLAUSULA DECIMA SEGUNDA -- MODIFICACIONES

Toda modificacion al presente contrato debera constar por escrito y ser firmada por ambas partes mediante un otrosi. Ningun acuerdo verbal o comunicacion informal tendra la capacidad de modificar los terminos y condiciones aqui pactados.

## CLAUSULA DECIMA TERCERA -- ACUERDO

El presente contrato, junto con la propuesta comercial aprobada y sus anexos, constituye el acuerdo completo entre las partes respecto al objeto contractual y reemplaza cualquier negociacion, acuerdo o comunicacion previa, ya sea oral o escrita, relacionada con el mismo.

## CLAUSULA DECIMA CUARTA -- NOTIFICACION

Toda notificacion o comunicacion formal relacionada con el presente contrato debera realizarse por escrito a las siguientes direcciones de correo electronico:

EL CONTRATANTE: {client_email}

EL CONTRATISTA: {contractor_email}

Las notificaciones se consideraran realizadas en la fecha de envio del correo electronico, siempre que se pueda acreditar su recepcion. Cualquier cambio en los datos de contacto debera ser comunicado a la otra parte con al menos cinco (5) dias habiles de anticipacion.

## CLAUSULA DECIMA QUINTA -- TERMINACION ANTICIPADA

### Paragrafo Primero

Cualquiera de las partes podra dar por terminado el presente contrato de manera anticipada, mediante comunicacion escrita dirigida a la otra parte con al menos treinta (30) dias calendario de anticipacion.

### Paragrafo Segundo

En caso de terminacion anticipada por parte del CONTRATANTE, este debera pagar a EL CONTRATISTA el valor proporcional de los servicios efectivamente prestados hasta la fecha de terminacion, incluyendo los entregables parciales completados.

### Paragrafo Tercero

En caso de terminacion anticipada por parte del CONTRATISTA, este debera entregar al CONTRATANTE todos los avances, codigo fuente y documentacion generados hasta la fecha de terminacion, y reembolsar la parte proporcional de los pagos recibidos que no correspondan a servicios efectivamente prestados.

### Paragrafo Cuarto

Las obligaciones de confidencialidad, proteccion de datos y derechos de propiedad intelectual subsistiran a la terminacion del contrato en los terminos establecidos en las clausulas correspondientes.

## CLAUSULA DECIMA SEXTA -- INCUMPLIMIENTO

### Paragrafo Primero

En caso de incumplimiento de cualquiera de las obligaciones del presente contrato, la parte cumplida debera requerir por escrito a la parte incumplida, otorgandole un plazo razonable no inferior a quince (15) dias habiles para subsanar el incumplimiento.

### Paragrafo Segundo

Si transcurrido el plazo otorgado el incumplimiento persiste, la parte cumplida podra dar por terminado el contrato y exigir la indemnizacion de los perjuicios causados, conforme a las reglas generales del derecho civil colombiano.

### Paragrafo Tercero

No se considerara incumplimiento el retraso o la imposibilidad de ejecucion derivada de eventos de fuerza mayor o caso fortuito debidamente acreditados, tales como desastres naturales, conflictos armados, pandemias, fallos masivos de infraestructura tecnologica o actos de autoridad que impidan la ejecucion. En tales casos, los plazos se suspenderan por el tiempo que dure el evento.

## CLAUSULA DECIMA SEPTIMA -- RESOLUCION DE CONFLICTOS

Las partes acuerdan resolver cualquier controversia derivada del presente contrato de la siguiente manera:

1. Negociacion directa: Las partes intentaran resolver la controversia de buena fe mediante negociacion directa durante un plazo de treinta (30) dias calendario.
2. Mediacion: Si la negociacion directa no prospera, las partes podran acudir a un mediador neutral de comun acuerdo.
3. Arbitraje o jurisdiccion ordinaria: En caso de no lograr acuerdo mediante los mecanismos anteriores, las partes podran someter la controversia a la jurisdiccion ordinaria de la ciudad de {contract_city}, Colombia.

## CLAUSULA DECIMA OCTAVA -- MERITO EJECUTIVO

El presente contrato presta merito ejecutivo para el cumplimiento de las obligaciones aqui contenidas, de conformidad con el articulo 422 del Codigo General del Proceso.

## CLAUSULA DECIMA NOVENA -- LIMITACION DE RESPONSABILIDAD

La responsabilidad total de EL CONTRATISTA frente a EL CONTRATANTE por cualquier concepto derivado del presente contrato no excedera el valor total efectivamente pagado por el CONTRATANTE al momento de la reclamacion.

### Paragrafo Primero

EL CONTRATISTA no sera responsable por danos indirectos, consecuenciales, lucro cesante o perdida de datos derivados del uso del software, salvo en casos de dolo o culpa grave.

### Paragrafo Segundo

EL CONTRATISTA no sera responsable por el funcionamiento del software en ambientes tecnologicos distintos a los especificados en la propuesta comercial, ni por errores derivados de modificaciones realizadas por terceros sin su autorizacion.

### Paragrafo Tercero

EL CONTRATANTE reconoce que el software se entrega "tal cual" una vez finalizada la garantia tecnica, y que EL CONTRATISTA no garantiza que el software este libre de todo error o que funcione de manera ininterrumpida. El mantenimiento y soporte posterior a la garantia seran objeto de acuerdos separados.\
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
        ('content', '0064_seed_default_contract_template'),
    ]

    operations = [
        migrations.RunPython(update_default_template, revert_default_template),
    ]
