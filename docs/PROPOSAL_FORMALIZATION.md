# Formalización de propuestas

En **Propuestas → editar → Documentos**, el administrador puede descargar los
anexos formales y preparar un correo para revisión y firma. Los PDFs públicos
mantienen su presentación comercial. Los anexos formales usan los datos
guardados en la propuesta y reglas de contenido explícitas.

## Contenido curado

| Documento | Contenido incluido | Contenido excluido |
|---|---|---|
| Propuesta comercial formal | Cliente, proyecto, referencia y emisión; alcance y entregables incluidos con sus IDs; prestaciones concretas de diseño y acompañamiento; cronograma, etapas y aportes del cliente; inversión efectiva y moneda; hitos y medios de pago; condiciones guardadas de hosting, mantenimiento y soporte; condiciones de módulos incluidos; límites y cambios de alcance. | ROI y proyecciones de retorno, argumentos de venta, diagnósticos persuasivos, paquetes de ampliación, precios de alcance no seleccionado, urgencia, testimonios, badges de garantías, próximos pasos comerciales y llamadas a comprar. |
| Detalle técnico formal | Propósito, stack, arquitectura y modelo de datos; preparación técnica actual; épicas y requerimientos del alcance seleccionado, IDs, configuración, flujo de uso y referencias comerciales; API, integraciones incluidas y excluidas; ambientes y roles; seguridad, rendimiento, respaldos, calidad, pruebas y decisiones técnicas. | Evoluciones futuras ofrecidas como posibilidad, ampliaciones no seleccionadas, venta o ROI, URLs y nombres de bases de datos de ambientes y campos arbitrarios de credenciales. |
| Contrato de desarrollo | El PDF final ya generado desde los parámetros de contrato de la propuesta, con el tratamiento de firma existente. | La variante de contrato borrador. |

Los campos estructurados son la fuente. Una sección necesaria en modo de texto
pegado requiere completar sus campos antes de preparar ese anexo. No se extraen
compromisos automáticamente de texto comercial libre ni se inventan obligaciones
o criterios de aceptación. Las garantías y obligaciones remiten al contrato.

La selección funcional y los IDs normalizados se comparten entre anexos. Los
importes porcentuales se calculan sobre la inversión efectiva. Si hosting tiene
varias modalidades guardadas, se presentan como opciones de periodicidad, sin
afirmar que el cliente eligió una. No se refrescan catálogos al producir los PDFs.

## Preparar y enviar

1. Generar el contrato final desde Documentos y completar los datos de la propuesta.
2. Elegir **Preparar correo de formalización**. Los tres documentos empiezan
   seleccionados; se puede desmarcar cualquiera y agregar otros adjuntos de esa
   propuesta. Una selección incompleta indica qué corregir o desmarcar.
3. Revisar destinatarios y CC, asunto, introducción y cierre de la plantilla
   `proposal_formalization`. Agregar, reordenar o quitar secciones de texto o Markdown.
4. Elegir **Preparar vista previa**. Revisar el correo final y descargar o
   previsualizar cada PDF del manifiesto preparado.
5. Elegir **Enviar documentación**. La confirmación permanece visible hasta
   cerrar la ventana; el historial de Correos conserva el mensaje y los adjuntos.

## Revisión y entrega

- La revisión guarda una copia privada del HTML, texto y bytes de cada adjunto.
  El envío utiliza esas copias, sin regenerarlas después de la revisión.
- Sólo el administrador creador puede consultar o enviar esa preparación.
  El acceso vence a las 24 horas; la limpieza diaria retira sus archivos.
- Si cambia el origen o falta un archivo, se requiere preparar y revisar de nuevo.
  El formulario conserva el mensaje para hacerlo.
- Una preparación admite un único intento de entrega. Si el resultado es
  incierto, se consulta su estado y se indica revisar el historial; no se reenvía
  automáticamente. La limpieza concede una hora de margen a un envío en curso
  que atraviese el vencimiento.
- El gateway habitual conserva copias configuradas, destinatarios, evidencias e
  historial. Enviar estos documentos no cambia el estado de la propuesta.
- La migración `content.0249` crea las preparaciones y sus archivos privados.
  Sus modelos son temporales, excluidos de fake data persistente y del MCP.

## Copiar y consultar documentos

**Copiar Markdown** lleva al portapapeles el contenido del documento elegido.
Los anexos comercial y técnico usan los mismos datos guardados y filtros de sus
PDF. El contrato conserva su texto al generar el PDF: un cambio posterior de
plantilla no altera su copia. Los contratos anteriores sin snapshot usan el
texto del PDF guardado y avisan que su formato fue reconstruido.

Los adjuntos muestran acciones explícitas de vista previa, descarga del original
y copia. PDF conserva su visor; DOCX y XLSX presentan texto y tablas, sin reproducir
el diseño de Office. Las fórmulas se muestran como texto. Las imágenes se pueden
visualizar y descargar; copiar requiere OCR, fuera de este alcance. DOC y XLS
requieren conversión a los formatos modernos. Escaneos, archivos protegidos,
corruptos o sin texto muestran una explicación; no se copia una respuesta vacía.

La extracción ocurre bajo demanda en un proceso local con 256 MB de memoria,
8 segundos de CPU y 12 segundos de espera máxima. Rechaza archivos de más de
15 MB, PDF de más de 100 páginas, libros de más de 20.000 celdas, contenido
expandido de más de 50 MB o salidas de más de un millón de caracteres. Los
límites no truncan silenciosamente el texto. PDF con páginas sin texto avisa
cuáles requieren revisión. No hay consultas externas ni ejecución de macros.

La migración `content.0255` añade el snapshot interno `content_markdown` a
`ProposalDocument`; los registros existentes permanecen vacíos hasta una nueva
generación explícita del contrato. No requiere regeneración ni backfill masivo.
