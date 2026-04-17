from django.db import migrations


NDA_MARKDOWN = """# ACUERDO DE CONFIDENCIALIDAD

**ENTRE:** {client_full_name} (EL CLIENTE)
**Y:** {contractor_full_name} (EL CONSULTOR)

---

Entre las partes, por un lado **{client_full_name}**, identificado con NIT/C.C. número {client_cedula}, representado legalmente por {client_legal_representative}, quien en adelante y para los efectos del presente acuerdo se denominará **EL CLIENTE**; y por el otro, **{contractor_full_name}**, identificado con NIT/C.C. número {contractor_cedula}, quien en adelante y para los efectos del presente acuerdo se denominará **EL CONSULTOR**; ambos mayores de edad, identificados como aparece al pie de las firmas, hemos acordado suscribir el presente Acuerdo de Confidencialidad, el cual se regirá por las siguientes cláusulas.

---

## CONSIDERACIONES PREVIAS

1. Que EL CLIENTE ha contratado o se encuentra en proceso de contratar con EL CONSULTOR la prestación de un servicio de diagnóstico técnico sobre una aplicación de software de su propiedad, el cual implica el acceso a información sensible, técnica, operativa, comercial y estratégica.

2. Que para la correcta ejecución del diagnóstico, EL CLIENTE deberá entregar a EL CONSULTOR acceso a los repositorios de código fuente, documentación técnica, información de negocio y cualquier otro insumo requerido.

3. Que ambas partes reconocen la necesidad de regular el tratamiento, uso, protección y reserva de la información que se intercambie con ocasión del servicio, bajo el marco de la legislación colombiana vigente.

4. Que el presente acuerdo se enmarca en la **Ley 1581 de 2012** y su decreto reglamentario **Decreto 1377 de 2013** sobre protección de datos personales, el **artículo 15 de la Constitución Política de Colombia** que protege el derecho a la intimidad, la **Decisión 486 de 2000 de la Comunidad Andina** sobre secretos empresariales, la **Ley 256 de 1996** sobre competencia desleal, el **Código de Comercio Colombiano** y las demás normas aplicables.

---

## CLÁUSULA PRIMERA - OBJETO

El presente acuerdo tiene por objeto establecer las condiciones bajo las cuales EL CONSULTOR se obliga a mantener la reserva, confidencialidad y protección de toda la información a la que tenga acceso con ocasión del servicio de diagnóstico técnico contratado por EL CLIENTE, así como regular las obligaciones recíprocas de confidencialidad entre las partes durante y después de la ejecución del servicio.

---

## CLÁUSULA SEGUNDA - DEFINICIÓN DE INFORMACIÓN CONFIDENCIAL

Para efectos del presente acuerdo, se entenderá como **INFORMACIÓN CONFIDENCIAL** toda aquella información, en cualquier formato o medio (físico, digital, verbal, visual o de cualquier otra naturaleza), que sea entregada, revelada o a la que tenga acceso EL CONSULTOR con ocasión del servicio, incluyendo, pero sin limitarse a:

a) **Código fuente:** Repositorios, ramas, commits, archivos de configuración, credenciales, llaves, tokens y cualquier artefacto técnico presente en los repositorios.
b) **Arquitectura y diseño técnico:** Diagramas, modelos de datos, esquemas, decisiones de diseño, patrones implementados y documentación técnica.
c) **Información de negocio:** Estrategias comerciales, modelos de monetización, información financiera, planes de crecimiento, clientes, proveedores y estructura organizacional.
d) **Datos personales:** Cualquier dato personal de usuarios, empleados, clientes o terceros que esté presente en bases de datos, logs, repositorios o documentación, conforme a la Ley 1581 de 2012.
e) **Propiedad intelectual:** Know-how, metodologías, procesos internos, algoritmos, fórmulas y cualquier desarrollo propio de EL CLIENTE.
f) **Información operativa:** Procesos internos, flujos de trabajo, reglas de negocio, debilidades técnicas identificadas, hallazgos del diagnóstico y cualquier observación realizada durante el servicio.
g) **Credenciales y accesos:** Usuarios, contraseñas, claves API, tokens, certificados y cualquier otro mecanismo de autenticación al que se otorgue acceso.
h) **Información de terceros:** Cualquier información que EL CLIENTE esté obligado a proteger por contratos con sus propios clientes, proveedores o aliados.

Se entenderá que la información es confidencial con independencia de si está expresamente marcada como tal, siempre que por su naturaleza razonablemente pueda considerarse reservada.

---

## CLÁUSULA TERCERA - OBLIGACIONES DEL CONSULTOR

EL CONSULTOR se obliga a:

a) Mantener absoluta reserva sobre la Información Confidencial, absteniéndose de divulgarla, revelarla, comercializarla, publicarla o compartirla con terceros, salvo autorización expresa y escrita de EL CLIENTE.

b) Utilizar la Información Confidencial exclusivamente para los fines del diagnóstico técnico contratado, y no para ningún otro propósito personal, comercial, académico o de cualquier otra naturaleza.

c) Adoptar las medidas técnicas, administrativas y humanas razonables para proteger la Información Confidencial contra accesos no autorizados, pérdida, alteración, destrucción, uso indebido o divulgación.

d) Limitar el acceso a la Información Confidencial exclusivamente al personal estrictamente necesario para la ejecución del diagnóstico, garantizando que dichas personas estén sujetas a obligaciones de confidencialidad equivalentes a las establecidas en el presente acuerdo.

e) No almacenar la Información Confidencial en dispositivos personales sin protección adecuada, ni en servicios en la nube no autorizados por EL CLIENTE.

f) No hacer copias, reproducciones, extractos o transcripciones de la Información Confidencial más allá de lo estrictamente necesario para la ejecución del diagnóstico.

g) Notificar a EL CLIENTE de manera inmediata, y a más tardar dentro de las veinticuatro (24) horas siguientes, cualquier sospecha o hecho relacionado con pérdida, fuga, acceso no autorizado o incidente de seguridad que afecte la Información Confidencial.

h) No utilizar la Información Confidencial para desarrollar, para sí mismo o para terceros, productos, servicios o soluciones que compitan con EL CLIENTE.

i) Cumplir estrictamente con la Ley 1581 de 2012 y el Decreto 1377 de 2013 en lo relacionado con el tratamiento de datos personales a los que acceda con ocasión del servicio.

j) No realizar ingeniería inversa, explotación, análisis con fines distintos al diagnóstico o aprovechamiento de las vulnerabilidades identificadas durante el servicio.

---

## CLÁUSULA CUARTA - OBLIGACIONES DEL CLIENTE

EL CLIENTE se obliga a:

a) Mantener la reserva sobre cualquier información técnica, metodológica o comercial propia de EL CONSULTOR a la que tenga acceso durante la ejecución del servicio, incluyendo herramientas, procesos, metodologías de diagnóstico y know-how.

b) No divulgar, reproducir ni compartir con terceros los entregables, informes o documentos producidos por EL CONSULTOR sin su autorización, salvo para uso interno propio de EL CLIENTE.

c) Respetar los derechos de propiedad intelectual de EL CONSULTOR sobre sus metodologías, plantillas, frameworks de análisis y demás herramientas utilizadas para la prestación del servicio.

---

## CLÁUSULA QUINTA - EXCEPCIONES

Las obligaciones de confidencialidad establecidas en el presente acuerdo no aplicarán sobre aquella información que:

a) Sea o llegue a ser de dominio público sin que medie acto u omisión de la parte receptora.
b) Estuviese en posesión legítima de la parte receptora con anterioridad a su divulgación y sin estar sujeta a obligación de confidencialidad.
c) Sea legítimamente obtenida de un tercero que no esté sujeto a restricciones de confidencialidad.
d) Sea desarrollada de forma independiente por la parte receptora sin uso de la Información Confidencial.
e) Deba ser divulgada por orden judicial, requerimiento de autoridad competente o mandato legal, en cuyo caso la parte receptora deberá notificar a la parte reveladora con la mayor antelación posible para permitirle ejercer sus derechos de oposición.

---

## CLÁUSULA SEXTA - TRATAMIENTO DE DATOS PERSONALES

En cumplimiento de la Ley 1581 de 2012 y el Decreto 1377 de 2013, EL CONSULTOR asume la calidad de **Encargado del Tratamiento** respecto de los datos personales a los que acceda con ocasión del servicio, y EL CLIENTE conserva la calidad de **Responsable del Tratamiento**.

EL CONSULTOR se compromete a:

a) Tratar los datos personales únicamente para los fines autorizados por EL CLIENTE.
b) Garantizar los derechos de los titulares de los datos: habeas data, rectificación, actualización y supresión.
c) Implementar medidas de seguridad adecuadas.
d) No transferir los datos personales a terceros sin autorización expresa de EL CLIENTE.
e) Devolver o eliminar los datos personales una vez finalizado el servicio, salvo obligación legal de conservación.

---

## CLÁUSULA SÉPTIMA - DEVOLUCIÓN Y ELIMINACIÓN DE LA INFORMACIÓN

Finalizado el servicio, o en cualquier momento a requerimiento de EL CLIENTE, EL CONSULTOR deberá:

a) Devolver toda la Información Confidencial en el formato original en que fue entregada, cuando esto sea posible.
b) Eliminar de forma segura y verificable toda copia, respaldo o reproducción de la Información Confidencial en su posesión, incluyendo archivos locales, respaldos en la nube, correos electrónicos y cualquier otro medio de almacenamiento.
c) Emitir a EL CLIENTE, dentro de los cinco (5) días hábiles siguientes a la finalización o requerimiento, una certificación escrita donde conste la devolución y/o eliminación de la Información Confidencial.

Se exceptúan de esta obligación las copias que EL CONSULTOR deba conservar por obligación legal, las cuales seguirán sujetas a las obligaciones de confidencialidad del presente acuerdo.

---

## CLÁUSULA OCTAVA - VIGENCIA

Las obligaciones de confidencialidad establecidas en el presente acuerdo tendrán vigencia durante la ejecución del servicio de diagnóstico y por un periodo de **cinco (5) años** contados a partir de la fecha de finalización del mismo, o de la terminación anticipada del acuerdo por cualquier causa.

Tratándose de datos personales y secretos empresariales que por su naturaleza requieran protección indefinida, las obligaciones de confidencialidad se extenderán de conformidad con lo dispuesto por la normatividad colombiana aplicable, pudiendo ser de carácter permanente.

---

## CLÁUSULA NOVENA - INCUMPLIMIENTO Y CONSECUENCIAS

El incumplimiento de las obligaciones establecidas en el presente acuerdo dará lugar a:

a) **Cesación inmediata** del uso indebido de la Información Confidencial por parte de la parte incumplida.

b) **Indemnización integral** de los perjuicios causados, incluyendo daño emergente y lucro cesante, conforme a los artículos 1613 y 1614 del Código Civil Colombiano.

c) **Acciones legales** por competencia desleal conforme a la Ley 256 de 1996, cuando aplique.

d) **Sanciones penales** conforme al artículo 308 del Código Penal Colombiano (violación de reserva industrial o comercial) y demás tipos penales aplicables.

e) **Sanciones administrativas** ante la Superintendencia de Industria y Comercio, conforme a la Ley 1581 de 2012, cuando el incumplimiento involucre datos personales.

Adicionalmente, la parte afectada podrá solicitar medidas cautelares para prevenir, detener o remediar el uso indebido de la Información Confidencial.

---

## CLÁUSULA DÉCIMA - CLÁUSULA PENAL

En caso de incumplimiento de las obligaciones de confidencialidad por parte de cualquiera de las partes, la parte incumplida pagará a la parte afectada, a título de cláusula penal, una suma equivalente a {penal_clause_value}, sin perjuicio del derecho de la parte afectada a reclamar los perjuicios adicionales que el incumplimiento le haya generado.

---

## CLÁUSULA DÉCIMA PRIMERA - NO CONCESIÓN DE DERECHOS

El presente acuerdo no constituye ni implica cesión, licencia ni transferencia de derechos de propiedad intelectual sobre la Información Confidencial. Toda la Información Confidencial seguirá siendo propiedad exclusiva de la parte que la reveló.

---

## CLÁUSULA DÉCIMA SEGUNDA - INDEPENDENCIA DE LAS PARTES

El presente acuerdo no crea una relación laboral, sociedad, agencia, representación, joint venture ni ningún otro tipo de vínculo distinto al estrictamente establecido aquí. Cada parte actuará de forma independiente y asumirá sus propias obligaciones tributarias, laborales y de seguridad social.

---

## CLÁUSULA DÉCIMA TERCERA - NOTIFICACIONES

Para todos los efectos del presente acuerdo, las partes establecen los siguientes medios de contacto:

- **EL CLIENTE:** Correo electrónico {client_email}
- **EL CONSULTOR:** Correo electrónico {contractor_email}

Toda notificación enviada a las direcciones de correo electrónico aquí indicadas se entenderá válidamente surtida al día hábil siguiente a su envío. Cualquier cambio en los datos de notificación deberá ser comunicado por escrito a la otra parte con al menos cinco (5) días hábiles de antelación.

---

## CLÁUSULA DÉCIMA CUARTA - RESOLUCIÓN DE CONFLICTOS

Toda controversia o diferencia que surja entre las partes con ocasión del presente acuerdo, su interpretación, ejecución, incumplimiento o terminación, se resolverá conforme al siguiente procedimiento:

1. **Negociación directa:** Las partes intentarán resolver la controversia de manera directa y de buena fe dentro de un plazo de quince (15) días hábiles contados a partir de la notificación escrita de la controversia.

2. **Conciliación:** Si la negociación directa no resuelve la controversia, las partes acudirán a un centro de conciliación legalmente establecido en la ciudad de {contract_city}, Colombia. Los costos de la conciliación serán asumidos por partes iguales.

3. **Jurisdicción ordinaria:** Si la conciliación no prospera dentro de los treinta (30) días calendario siguientes a la solicitud, las partes someterán la controversia a la jurisdicción civil ordinaria de la ciudad de {contract_city}, Colombia, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.

---

## CLÁUSULA DÉCIMA QUINTA - LEGISLACIÓN APLICABLE

El presente acuerdo se rige e interpretará conforme a las leyes de la República de Colombia, en particular:

- Constitución Política de Colombia (artículo 15).
- Ley 1581 de 2012 y Decreto 1377 de 2013 sobre protección de datos personales.
- Decisión 486 de 2000 de la Comunidad Andina sobre propiedad industrial y secretos empresariales.
- Ley 256 de 1996 sobre competencia desleal.
- Código de Comercio Colombiano.
- Código Civil Colombiano.
- Código Penal Colombiano.
- Y demás normas concordantes y complementarias.

---

## CLÁUSULA DÉCIMA SEXTA - MODIFICACIONES

Cualquier modificación al presente acuerdo deberá constar por escrito y estar firmada por ambas partes mediante un "OTROSÍ" para ser válida y exigible.

---

## CLÁUSULA DÉCIMA SÉPTIMA - ACUERDO INTEGRAL

El presente acuerdo constituye el acuerdo integral entre las partes sobre la materia de confidencialidad y reemplaza cualquier entendimiento, acuerdo verbal o escrito previo sobre el mismo objeto. En caso de conflicto entre este acuerdo y cualquier otro documento suscrito entre las partes, prevalecerá este acuerdo en lo relacionado con la confidencialidad.

---

## CLÁUSULA DÉCIMA OCTAVA - MÉRITO EJECUTIVO

El presente acuerdo prestará mérito ejecutivo para el cobro de las obligaciones claras, expresas y exigibles que de él se deriven, incluyendo la cláusula penal establecida en la CLÁUSULA DÉCIMA, de conformidad con lo establecido en el artículo 422 del Código General del Proceso colombiano.

---

## FIRMAS

En constancia de lo anterior, las partes firman el presente acuerdo en la ciudad de {contract_city}, a los {contract_day} días del mes de {contract_month} de {contract_year}, en dos (2) ejemplares del mismo tenor, uno para cada parte.
"""


def seed_template(apps, schema_editor):
    ConfidentialityTemplate = apps.get_model('content', 'ConfidentialityTemplate')
    if ConfidentialityTemplate.objects.filter(is_default=True).exists():
        return
    ConfidentialityTemplate.objects.create(
        name='Acuerdo de Confidencialidad - ProjectApp (Colombia)',
        content_markdown=NDA_MARKDOWN,
        is_default=True,
    )


def unseed_template(apps, schema_editor):
    ConfidentialityTemplate = apps.get_model('content', 'ConfidentialityTemplate')
    ConfidentialityTemplate.objects.filter(
        name='Acuerdo de Confidencialidad - ProjectApp (Colombia)',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0098_confidentiality_template_and_nda_fields'),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]
