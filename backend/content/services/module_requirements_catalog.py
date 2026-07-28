"""Default technical requirements for the optional additionalModules catalog.

Every visible, non-invite module of the functional-requirements
``additionalModules`` catalog ships a per-item set of technical requirements
(ES + EN). ``seed_module_technical_requirements`` injects them into a
proposal's ``technical_document`` when the generation/import left the module
without its own epic, so the "Ver requerimientos (N)" breakdown per module
item never depends on how thorough a given generation was.

Contract:

* One catalog requirement per default module item; ``item`` holds the default
  item name and resolves to ``linked_item_ids`` at seed time via
  ``build_item_id`` (never stored in the catalog — item ids are localized).
* ``flowKey`` values are kebab-case, namespaced per module, and IDENTICAL
  across languages (texts are translated, keys are not).
* Seeded epics/requirements always carry ``linked_module_ids`` with the raw
  module id; ``normalize_technical_document_module_links`` canonicalizes it
  to ``module-<id>`` right after seeding, which is what keeps them gated by
  the client's module selection everywhere (web, PDFs, platform sync).
* Seeding is seed-if-absent PER MODULE: any epic or requirement already
  covering the module (by link or verbatim ``epicKey``) disables seeding for
  it, so seller/LLM-authored content and manual deletions in the panel editor
  always win. The editor save path never seeds.
"""

from __future__ import annotations

import copy
from typing import Any

from django.utils.text import slugify

from content.services.proposal_module_links import build_item_id

MODULE_REQUIREMENTS_CATALOG: dict[str, dict[str, Any]] = {
    'es': {
        'integration_electronic_invoicing': {
            'epic_title': 'Alcance ampliado: Facturación Electrónica e Integración DIAN',
            'epic_description': (
                'Desglose técnico del módulo de facturación electrónica. Cada requerimiento '
                'detalla un elemento del alcance del módulo y su criterio de aceptación.'
            ),
            'requirements': [
                {
                    'flowKey': 'invoicing-generacion-comprobantes',
                    'item': 'Generación de comprobantes electrónicos',
                    'title': 'Emisión de facturas, notas y documentos soporte desde los flujos del negocio',
                    'description': 'Cada venta o pedido completado puede generar su comprobante electrónico (factura, nota crédito/débito o documento soporte) sin salir de la plataforma ni digitar dos veces la información.',
                    'configuration': 'Mapeo de campos fiscales (cliente, ítems, impuestos), numeración autorizada y emisión vía la API del proveedor de facturación; cola con reintentos ante errores del proveedor.',
                    'usageFlow': 'Se completa un pedido → el sistema arma el comprobante → lo envía al proveedor → guarda número, CUFE y PDF → notifica el resultado.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'invoicing-sincronizacion-fiscal',
                    'item': 'Sincronización de datos fiscales',
                    'title': 'Sincronización bidireccional de clientes, productos e impuestos',
                    'description': 'Los catálogos fiscales se mantienen alineados entre la plataforma y el sistema de facturación: lo que se crea o edita en un lado queda reflejado en el otro, sin doble digitación.',
                    'configuration': 'Tareas periódicas (Huey) más webhooks del proveedor cuando existan; llave externa por registro y resolución de conflictos por fecha de última actualización.',
                    'usageFlow': 'Se crea o edita un cliente/producto → se encola la sincronización → el registro queda vinculado por id externo → los cambios remotos se reflejan en la plataforma.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'invoicing-trazabilidad-estado',
                    'item': 'Trazabilidad del estado fiscal',
                    'title': 'Seguimiento del estado DIAN de cada comprobante',
                    'description': 'Desde la plataforma se consulta si cada comprobante fue emitido, aceptado, rechazado o sigue en proceso, con su historial completo y el motivo cuando hay rechazo.',
                    'configuration': 'Consulta de estado vía API con sondeo programado; almacenamiento de la línea de tiempo de estados por comprobante.',
                    'usageFlow': 'El usuario abre el detalle de una factura → ve la línea de tiempo de estados → si hubo rechazo, ve el motivo reportado y puede reemitir.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'invoicing-proveedores-colombia',
                    'item': 'Integración con proveedores colombianos',
                    'title': 'Conexión con el proveedor de facturación del cliente (Siigo, Alegra u otro)',
                    'description': 'La integración se construye contra el proveedor que el negocio ya usa o elija, validada de punta a punta antes de salir a producción.',
                    'configuration': 'Credenciales API del cliente en variables de entorno; adaptador por proveedor con contrato común (emitir, consultar, anular) para poder cambiar de proveedor sin rehacer los flujos.',
                    'usageFlow': 'Se configuran las credenciales → se valida la conexión con una emisión de prueba en sandbox → se activa el modo producción.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'invoicing-automatizaciones-api',
                    'item': 'Automatizaciones vía API',
                    'title': 'Reconciliación de pagos y emisión automática',
                    'description': 'Los eventos del negocio disparan acciones fiscales sin intervención manual: emitir al completar un pedido, conciliar pagos recibidos y avisar cambios de estado.',
                    'configuration': 'Reglas de disparo por evento (pedido completado, pago confirmado) y notificaciones de estado fiscal por correo al responsable.',
                    'usageFlow': 'Ocurre el evento configurado → la automatización ejecuta la acción fiscal → el resultado queda registrado y notificado.',
                    'priority': 'medium',
                },
            ],
        },
        'integration_regional_payments': {
            'epic_title': 'Alcance ampliado: Pasarela de Pago Regional (Colombia)',
            'epic_description': (
                'Desglose técnico de la integración de pagos locales. Cada requerimiento '
                'cubre una pasarela del alcance del módulo.'
            ),
            'requirements': [
                {
                    'flowKey': 'regional-payu',
                    'item': 'PayU',
                    'title': 'Checkout con PayU: tarjeta, PSE y medios en efectivo',
                    'description': 'El cliente final paga con los medios locales más usados en Colombia (tarjeta, PSE, Efecty, Nequi, Daviplata) y el pedido se confirma solo cuando la pasarela confirma el pago.',
                    'configuration': 'Cuenta PayU del cliente (sandbox y producción), firma de integridad por transacción, webhook de confirmación y validación de monto/moneda antes de aprobar el pedido.',
                    'usageFlow': 'Carrito → checkout → pago en PayU → retorno con estado → confirmación del pedido y correo al cliente.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'regional-wompi',
                    'item': 'Wompi (Bancolombia)',
                    'title': 'Checkout con Wompi: PSE, tarjetas y botón Bancolombia',
                    'description': 'Alternativa local con excelente cobertura Bancolombia: el cliente paga con PSE, tarjeta, Nequi o botón Bancolombia y el estado del pago queda trazado en la plataforma.',
                    'configuration': 'Llaves pública/privada de Wompi del cliente, verificación de firma de eventos y conciliación del estado final de cada transacción.',
                    'usageFlow': 'Checkout → widget o redirección Wompi → pago → evento de confirmación → pedido aprobado o rechazado según el estado.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'regional-epayco',
                    'item': 'ePayco',
                    'title': 'Checkout con ePayco: PSE, tarjetas y recaudo físico',
                    'description': 'Opción colombiana de integración ágil: pagos con PSE, tarjeta y recaudos físicos, con confirmación asíncrona verificada del lado del servidor.',
                    'configuration': 'Credenciales ePayco del cliente, página de respuesta y URL de confirmación server-to-server con validación de firma.',
                    'usageFlow': 'Checkout → pago en ePayco → respuesta al cliente → confirmación server-to-server → actualización del estado del pedido.',
                    'priority': 'medium',
                },
            ],
        },
        'integration_international_payments': {
            'epic_title': 'Alcance ampliado: Pasarela de Pago Internacional',
            'epic_description': (
                'Desglose técnico de la integración de pagos internacionales. Cada '
                'requerimiento cubre una pasarela del alcance del módulo.'
            ),
            'requirements': [
                {
                    'flowKey': 'intl-stripe',
                    'item': 'Stripe',
                    'title': 'Cobros internacionales con Stripe: tarjetas y múltiples divisas',
                    'description': 'El negocio recibe pagos con tarjeta de crédito/débito desde cualquier país, en pagos únicos o recurrentes, con confirmación verificada antes de entregar el producto o servicio.',
                    'configuration': 'Claves API restringidas, webhooks firmados (pago exitoso/fallido), manejo de divisas habilitadas y modo suscripción cuando aplique.',
                    'usageFlow': 'Checkout → formulario seguro de Stripe → pago → webhook de confirmación → pedido aprobado y correo de comprobante.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'intl-paypal',
                    'item': 'PayPal',
                    'title': 'Cobros con PayPal: saldo, tarjeta y cuentas internacionales',
                    'description': 'Los clientes que prefieren PayPal pagan con su saldo o tarjeta asociada; la plataforma verifica la captura del pago antes de confirmar el pedido.',
                    'configuration': 'Credenciales de la app PayPal del cliente (sandbox y live), captura de órdenes vía API y verificación del estado antes de aprobar.',
                    'usageFlow': 'Checkout → botón PayPal → aprobación en PayPal → captura del pago → confirmación del pedido.',
                    'priority': 'medium',
                },
            ],
        },
        'pwa_module': {
            'epic_title': 'Alcance ampliado: Aplicación Móvil Instalable (PWA)',
            'epic_description': (
                'Desglose técnico del módulo PWA. Cada requerimiento detalla un elemento '
                'del alcance instalable/offline del módulo.'
            ),
            'requirements': [
                {
                    'flowKey': 'pwa-instalacion-dispositivo',
                    'item': 'Instalación en dispositivo',
                    'title': 'Instalación como aplicación en celular y computador',
                    'description': 'El sitio se instala desde el navegador como una app con ícono y nombre de la marca en la pantalla de inicio, y abre en ventana propia sin barra del navegador.',
                    'configuration': 'Web App Manifest (nombre, colores, íconos maskable), service worker registrado y cumplimiento de los criterios de instalabilidad de Chrome/Safari.',
                    'usageFlow': 'El visitante navega el sitio → el navegador ofrece "Instalar aplicación" → confirma → el ícono queda en la pantalla de inicio y abre en modo standalone.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'pwa-offline',
                    'item': 'Funcionamiento offline',
                    'title': 'Acceso al contenido sin conexión a internet',
                    'description': 'Sin conexión, la app sigue mostrando el contenido ya visitado y una pantalla offline clara para lo no disponible; al reconectar, el contenido se actualiza solo.',
                    'configuration': 'Estrategias de caché por tipo de recurso (precache del shell, stale-while-revalidate para contenido) y página offline de respaldo.',
                    'usageFlow': 'El usuario pierde conexión → abre la app → ve contenido cacheado y aviso de modo offline → al reconectar, todo se actualiza en segundo plano.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'pwa-notificaciones-push',
                    'item': 'Notificaciones push',
                    'title': 'Notificaciones push con permiso del usuario',
                    'description': 'El negocio envía avisos directos al dispositivo (novedades, promociones, actualizaciones) solo a usuarios que aceptaron recibirlos, con opción de desuscribirse.',
                    'configuration': 'Suscripción Web Push con llaves VAPID, solicitud de permiso explícita y envío segmentado desde el backend.',
                    'usageFlow': 'El usuario acepta el permiso → el negocio publica un aviso → la notificación llega al dispositivo aun con el sitio cerrado → al tocarla abre la vista correspondiente.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'pwa-splash-personalizada',
                    'item': 'Pantalla de carga personalizada',
                    'title': 'Splash screen con la identidad de la marca',
                    'description': 'Al abrir la app instalada aparece una pantalla de carga con logo y colores corporativos, en lugar de un fondo genérico del navegador.',
                    'configuration': 'Íconos y colores de fondo/tema definidos en el manifest para generar el splash nativo en Android/iOS.',
                    'usageFlow': 'El usuario abre la app instalada → ve el splash con la marca → entra a la pantalla inicial ya cargada.',
                    'priority': 'low',
                },
                {
                    'flowKey': 'pwa-sincronizacion-segundo-plano',
                    'item': 'Sincronización en segundo plano',
                    'title': 'Reintento automático de operaciones al recuperar conexión',
                    'description': 'Las acciones hechas sin conexión (formularios, cambios) quedan en cola y se envían solas cuando vuelve la señal, sin que el usuario repita nada.',
                    'configuration': 'Cola de operaciones pendientes con Background Sync y reintentos con confirmación al completar.',
                    'usageFlow': 'El usuario envía una acción sin conexión → queda en cola con aviso → al recuperar señal se sincroniza → recibe confirmación.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'pwa-actualizacion-automatica',
                    'item': 'Actualización automática',
                    'title': 'Actualización transparente a la última versión',
                    'description': 'La app se actualiza sola: el usuario siempre usa la versión más reciente sin pasos manuales ni tiendas de aplicaciones.',
                    'configuration': 'Versionado del service worker con activación controlada y aviso discreto de "nueva versión disponible" cuando aplique.',
                    'usageFlow': 'Se publica una nueva versión → el service worker la descarga en segundo plano → en la siguiente apertura la app ya está actualizada.',
                    'priority': 'medium',
                },
            ],
        },
        'corporate_branding_module': {
            'epic_title': 'Alcance ampliado: Identidad Visual e Imagen Corporativa',
            'epic_description': (
                'Desglose técnico del módulo de branding. Cada requerimiento cubre un '
                'punto de contacto donde la identidad de marca se aplica.'
            ),
            'requirements': [
                {
                    'flowKey': 'branding-correos-transaccionales',
                    'item': 'Correos transaccionales con identidad corporativa',
                    'title': 'Todos los correos del sistema salen con plantilla de marca',
                    'description': 'Bienvenida, confirmaciones, alertas y recuperación de contraseña llegan con logo, colores, tipografía y firma de la marca — nunca en texto plano genérico.',
                    'configuration': 'Plantillas HTML responsivas probadas en Gmail/Outlook, con variables por evento y versión de texto plano de respaldo.',
                    'usageFlow': 'Ocurre un evento del sistema → se renderiza la plantilla de marca con los datos del evento → el correo llega con la identidad del negocio.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'branding-pdfs-exportables',
                    'item': 'PDFs y exportables con branding',
                    'title': 'Documentos generados con encabezado y pie de marca',
                    'description': 'Facturas, reportes, certificados y descargas Excel/CSV salen con logo, paleta corporativa y pie de marca: cada documento refuerza la imagen profesional.',
                    'configuration': 'Encabezado/pie estandarizados en el generador de PDFs y estilos de marca en los exportes tabulares.',
                    'usageFlow': 'El usuario descarga o recibe un documento del sistema → el archivo llega con la identidad visual completa de la marca.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'branding-open-graph',
                    'item': 'Tarjetas de previsualización en redes (Open Graph)',
                    'title': 'Los links compartidos muestran tarjeta con logo e imagen de marca',
                    'description': 'Al compartir un link del sitio en WhatsApp, Facebook, LinkedIn o X aparece una tarjeta con logo, imagen y colores de la marca, no un link plano — impacto directo en percepción y clics.',
                    'configuration': 'Metadatos Open Graph y Twitter Card por vista pública (título, descripción, imagen), validados con los depuradores de Meta y LinkedIn.',
                    'usageFlow': 'El usuario comparte un link → la red social lee los metadatos → la conversación muestra la tarjeta de marca.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'branding-pantallas-sistema',
                    'item': 'Pantallas del sistema con identidad de marca',
                    'title': 'Errores, login y estados de carga con la voz de la marca',
                    'description': 'Las páginas 404/500, mantenimiento, login y estados de carga usan la identidad visual y mensajes propios del negocio, en vez de las pantallas genéricas del framework.',
                    'configuration': 'Plantillas de error y mantenimiento personalizadas, skeletons/spinners con la paleta corporativa y textos en la voz de la marca.',
                    'usageFlow': 'El usuario cae en un error o espera una carga → la pantalla mantiene la identidad y lo orienta para continuar.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'branding-metadatos-estructurados',
                    'item': 'Metadatos estructurados para buscadores e IA',
                    'title': 'La marca aparece correctamente en Google y asistentes de IA',
                    'description': 'Buscadores y asistentes (Google, Bing, ChatGPT, Perplexity) reciben datos estructurados de la organización para mostrar logo, contacto y redes en paneles y resultados enriquecidos.',
                    'configuration': 'JSON-LD Organization (logo, colores, redes sociales, datos de contacto) validado con la prueba de resultados enriquecidos de Google.',
                    'usageFlow': 'Un buscador o asistente indexa el sitio → lee el JSON-LD → muestra la marca con sus datos correctos en sus resultados.',
                    'priority': 'medium',
                },
            ],
        },
        'behavior_tracking_module': {
            'epic_title': 'Alcance ampliado: Rastreo de Comportamiento de Usuarios',
            'epic_description': (
                'Desglose técnico del módulo de comportamiento. Alcance incluido: hasta '
                '15 vistas rastreadas, panel con hasta 8 KPIs y 4 gráficos, retención de 12 meses.'
            ),
            'requirements': [
                {
                    'flowKey': 'behavior-sesiones',
                    'item': 'Registro de sesiones y aperturas',
                    'title': 'Registro first-party de cada sesión de uso',
                    'description': 'Cada ingreso queda registrado con fecha, dispositivo y si es primera visita o retorno — todo en datos propios del negocio, sin cookies de terceros ni herramientas externas.',
                    'configuration': 'Evento de sesión first-party con identificador anónimo persistente, marca de tiempo y clasificación nueva visita vs retorno.',
                    'usageFlow': 'El usuario entra a la plataforma → se registra la sesión con su contexto → el dato queda disponible para KPIs y gráficos.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-tiempo-por-vista',
                    'item': 'Vistas abiertas y tiempo por vista',
                    'title': 'Medición de vistas abiertas y segundos de permanencia',
                    'description': 'Se registra qué vistas abre cada usuario y cuánto tiempo activo pasa en cada una, sobre las hasta 15 vistas acordadas con el cliente al inicio.',
                    'configuration': 'Instrumentación de las vistas acordadas con medición de tiempo activo (heartbeat) y corte por inactividad.',
                    'usageFlow': 'El usuario navega entre vistas → cada apertura y su duración quedan registradas → alimentan el mapa de interés y el embudo.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-mapa-interes',
                    'item': 'Mapa de interés por vista',
                    'title': 'Ranking de vistas por atención recibida',
                    'description': 'El negocio ve qué vistas concentran la atención (tiempo acumulado y visitas) y cuáles pasan desapercibidas, para decidir dónde invertir mejoras.',
                    'configuration': 'Agregación por vista de tiempo total y número de aperturas, ordenada de mayor a menor interés.',
                    'usageFlow': 'El administrador abre el panel de comportamiento → ve el ranking de vistas → identifica qué funciona y qué no.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-embudo-abandonos',
                    'item': 'Embudo de recorrido con abandonos',
                    'title': 'Embudo principal con puntos de abandono',
                    'description': 'Un (1) embudo definido junto al cliente muestra cómo avanzan los usuarios entre las vistas rastreadas y en qué paso exacto abandonan.',
                    'configuration': 'Definición del embudo sobre las vistas rastreadas con conversión y abandono por paso.',
                    'usageFlow': 'El administrador abre el embudo → ve el porcentaje que avanza en cada paso → detecta el punto de mayor fuga.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-panel-integrado',
                    'item': 'Panel de comportamiento integrado',
                    'title': 'Dashboard propio con hasta 8 KPIs y 4 gráficos',
                    'description': 'Dentro del propio panel administrativo: sesiones, tiempo promedio, vistas más abiertas y desglose por dispositivo — sin licencias ni suscripciones externas.',
                    'configuration': 'Consultas agregadas optimizadas sobre los eventos propios; tarjetas KPI y gráficos limitados al alcance contratado (8 KPIs / 4 gráficos).',
                    'usageFlow': 'El administrador entra al panel → ve los KPIs y gráficos actualizados → filtra por rango de fechas.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-desglose-dispositivo',
                    'item': 'Desglose por dispositivo',
                    'title': 'Uso por móvil, tablet y escritorio',
                    'description': 'El negocio sabe desde qué tipo de dispositivo usan la plataforma para priorizar mejoras donde los usuarios realmente están.',
                    'configuration': 'Clasificación de dispositivo por user-agent en el evento de sesión, agregada en el panel.',
                    'usageFlow': 'El administrador abre el desglose → ve la proporción móvil/tablet/escritorio → prioriza el canal dominante.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-retencion-datos',
                    'item': 'Datos propios con retención de 12 meses',
                    'title': 'Eventos almacenados en la base del cliente por 12 meses',
                    'description': 'Los datos viven en la base de datos del negocio y se conservan 12 meses; no incluye grabación de pantalla, mapas de calor de clics ni rastreo entre sitios.',
                    'configuration': 'Purga programada de eventos mayores a 12 meses y límites de alcance documentados.',
                    'usageFlow': 'Los eventos se acumulan en la base propia → la purga mensual elimina lo que supera la retención → el panel siempre consulta datos vigentes.',
                    'priority': 'medium',
                },
            ],
        },
        'reports_alerts_module': {
            'epic_title': 'Alcance ampliado: Reportes y Alertas vía Correo o WhatsApp',
            'epic_description': (
                'Desglose técnico del módulo de reportes y alertas. Cada requerimiento '
                'cubre un canal o capacidad del alcance del módulo.'
            ),
            'requirements': [
                {
                    'flowKey': 'reports-correo-automatico',
                    'item': 'Reportes automáticos por correo',
                    'title': 'Resúmenes periódicos con métricas clave en la bandeja de entrada',
                    'description': 'El responsable recibe el resumen del negocio (ventas, registros, actividad) por correo sin entrar al sistema, en la frecuencia que elija.',
                    'configuration': 'Generación programada del reporte con plantilla de marca y métricas acordadas; registro de envíos.',
                    'usageFlow': 'Llega la hora programada → el sistema arma el reporte con los datos del período → lo envía al correo configurado.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'reports-alertas-personalizadas',
                    'item': 'Alertas personalizadas',
                    'title': 'Alertas por eventos y umbrales definidos por el negocio',
                    'description': 'Nuevas ventas, registros de usuarios, stock bajo o cualquier métrica definida disparan un aviso inmediato al responsable.',
                    'configuration': 'Reglas por evento o umbral configurables; evaluación al ocurrir el evento y disparo inmediato del canal elegido.',
                    'usageFlow': 'Ocurre el evento (p. ej. stock bajo) → la regla se evalúa → el aviso llega por el canal configurado con el detalle.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'reports-whatsapp',
                    'item': 'Integración con WhatsApp',
                    'title': 'Alertas y reportes por WhatsApp con la API oficial',
                    'description': 'Los avisos llegan al número de WhatsApp del negocio por el mismo canal donde ya atiende a sus clientes, usando la API oficial.',
                    'configuration': 'API oficial de WhatsApp (Cloud API) con plantillas aprobadas, número verificado del negocio y manejo de fallos de entrega.',
                    'usageFlow': 'Se dispara un reporte o alerta → el sistema envía la plantilla aprobada por WhatsApp → el responsable la recibe en su chat.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'reports-programacion',
                    'item': 'Programación de envíos',
                    'title': 'Frecuencia y horario de reportes configurables',
                    'description': 'Cada reporte se programa diario, semanal, mensual o en tiempo real, en el horario y zona horaria del negocio.',
                    'configuration': 'Tareas programadas (Huey) por reporte con frecuencia, hora y zona horaria configurables desde el panel.',
                    'usageFlow': 'El administrador define la frecuencia y hora → el sistema respeta la programación → puede pausar o ajustar cuando quiera.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'reports-resumen-ejecutivo',
                    'item': 'Resumen ejecutivo periódico',
                    'title': 'Informe consolidado para decisión rápida',
                    'description': 'Un informe con las métricas más relevantes del proyecto, diseñado para leerse en minutos y decidir con datos.',
                    'configuration': 'Selección de métricas clave acordadas con el cliente y formato ejecutivo (titulares + variaciones vs período anterior).',
                    'usageFlow': 'Llega el período configurado → se consolida el informe ejecutivo → el responsable lo lee y actúa sobre los cambios relevantes.',
                    'priority': 'medium',
                },
            ],
        },
        'email_marketing_module': {
            'epic_title': 'Alcance ampliado: Integración de Email Marketing',
            'epic_description': (
                'Desglose técnico del módulo de email marketing. Cada requerimiento '
                'cubre una capacidad del alcance del módulo.'
            ),
            'requirements': [
                {
                    'flowKey': 'email-mkt-captura-leads',
                    'item': 'Captura de leads',
                    'title': 'Formularios y pop-ups que capturan correos de interesados',
                    'description': 'Los visitantes interesados dejan su correo en formularios optimizados y pop-ups no invasivos, con validación y confirmación de suscripción.',
                    'configuration': 'Formularios con validación de correo, reglas de aparición del pop-up (tiempo/scroll/salida) y registro anti-duplicados.',
                    'usageFlow': 'El visitante ve el formulario o pop-up → deja su correo → recibe la confirmación → queda en la lista del negocio.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'email-mkt-automatizaciones',
                    'item': 'Automatizaciones de email',
                    'title': 'Secuencias automáticas de bienvenida, carrito y re-engagement',
                    'description': 'Los suscriptores reciben secuencias sin intervención manual: bienvenida al registrarse, recordatorio de carrito abandonado, seguimiento post-compra y reactivación de inactivos.',
                    'configuration': 'Disparadores por evento (alta, carrito, compra, inactividad) conectados a las automatizaciones del proveedor elegido.',
                    'usageFlow': 'Ocurre el evento → se dispara la secuencia correspondiente → los correos salen en los intervalos definidos.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'email-mkt-segmentacion',
                    'item': 'Segmentación de audiencia',
                    'title': 'Suscriptores clasificados por comportamiento e intereses',
                    'description': 'Las listas se segmentan por comportamiento, intereses y datos demográficos para que cada mensaje llegue a quien le es relevante.',
                    'configuration': 'Sincronización de atributos y etiquetas desde la plataforma hacia el proveedor (compras, categorías vistas, origen del lead).',
                    'usageFlow': 'El suscriptor interactúa con el sitio → sus atributos se actualizan → las campañas se dirigen al segmento correcto.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'email-mkt-analitica',
                    'item': 'Analítica de campañas',
                    'title': 'Métricas de apertura, clics y conversión por campaña',
                    'description': 'Cada campaña reporta aperturas, clics, conversiones y ROI para optimizar la estrategia de comunicación con datos reales.',
                    'configuration': 'Lectura de métricas vía API del proveedor y atribución de conversiones con parámetros UTM en los enlaces.',
                    'usageFlow': 'Se envía la campaña → las métricas se consultan desde el panel → el negocio ajusta contenido y segmentos según resultados.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'email-mkt-integracion-plataformas',
                    'item': 'Integración con plataformas',
                    'title': 'Conexión nativa con el proveedor elegido (Mailchimp, SendGrid, Brevo…)',
                    'description': 'La plataforma queda conectada con el proveedor de email marketing que el negocio use o elija, con listas y eventos sincronizados.',
                    'configuration': 'Credenciales API del proveedor, mapeo de listas/audiencias y sincronización de altas, bajas y rebotes.',
                    'usageFlow': 'Se configuran las credenciales → se valida la conexión con una lista de prueba → las altas y eventos fluyen automáticamente.',
                    'priority': 'high',
                },
            ],
        },
        'qr_generator_module': {
            'epic_title': 'Alcance ampliado: Generador de Códigos QR',
            'epic_description': (
                'Desglose técnico del módulo QR. Cada requerimiento cubre una capacidad '
                'del generador y su ciclo de vida.'
            ),
            'requirements': [
                {
                    'flowKey': 'qr-generacion-instantanea',
                    'item': 'Generación instantánea',
                    'title': 'QR desde URLs, textos, vCard, WiFi o WhatsApp en segundos',
                    'description': 'Cualquier enlace, texto, contacto vCard, red WiFi o número de WhatsApp se convierte en un QR listo para usar, generado al instante desde el panel.',
                    'configuration': 'Generación server-side con corrección de errores configurable y tipos de contenido soportados (URL, texto, vCard, WiFi, wa.me).',
                    'usageFlow': 'El administrador elige el tipo de contenido → ingresa el dato → el QR se genera y queda listo para descargar o compartir.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'qr-personalizacion-marca',
                    'item': 'Personalización con tu marca',
                    'title': 'QR con colores corporativos, logo y formatos de impresión',
                    'description': 'Cada código puede llevar los colores de la marca y el logo al centro, exportado en PNG, SVG o PDF en alta resolución sin perder lectura.',
                    'configuration': 'Paleta corporativa aplicada con verificación de contraste/escaneabilidad y exportes vectoriales para imprenta.',
                    'usageFlow': 'El administrador aplica el estilo de marca → previsualiza y prueba el escaneo → descarga el formato que necesita.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-codigos-dinamicos',
                    'item': 'Códigos dinámicos editables',
                    'title': 'Cambiar el destino de un QR ya impreso sin reimprimirlo',
                    'description': 'Los QR dinámicos apuntan a un enlace propio editable: el negocio cambia el destino (menú de temporada, promoción, evento) y el código impreso sigue sirviendo.',
                    'configuration': 'Redirector propio con slug corto por código y edición del destino desde el panel; el QR impreso apunta siempre al redirector.',
                    'usageFlow': 'El administrador edita el destino del código → guarda → todos los escaneos siguientes llegan al nuevo destino.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'qr-tracking-escaneos',
                    'item': 'Tracking de escaneos',
                    'title': 'Conteo de escaneos por código, dispositivo y momento',
                    'description': 'Cada código reporta cuántas veces fue escaneado, desde qué tipo de dispositivo y cuándo — para medir campañas físicas con datos.',
                    'configuration': 'Registro de escaneo en el redirector (marca de tiempo, dispositivo) con agregados por código y campaña.',
                    'usageFlow': 'Alguien escanea el código → el redirector registra el evento y redirige → las métricas quedan visibles en el panel.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-biblioteca',
                    'item': 'Biblioteca de códigos',
                    'title': 'Todos los QR organizados por campaña o propósito',
                    'description': 'Los códigos generados quedan en una biblioteca ordenada, listos para reutilizar, descargar de nuevo o desactivar cuando ya no apliquen.',
                    'configuration': 'Listado con agrupación por campaña/propósito, estados activo/inactivo y regeneración de descargas.',
                    'usageFlow': 'El administrador abre la biblioteca → filtra por campaña → reutiliza, descarga o desactiva el código que necesita.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-casos-de-uso',
                    'item': 'Casos de uso listos para activar',
                    'title': 'Plantillas preconfiguradas: menú, WhatsApp, eventos, reseñas',
                    'description': 'Casos comunes listos para arrancar el mismo día: menú digital, link a WhatsApp, registro a eventos, descarga de catálogo, encuestas, propinas o reseñas.',
                    'configuration': 'Plantillas por caso de uso con el tipo de contenido y estilo predefinidos, editables antes de generar.',
                    'usageFlow': 'El administrador elige la plantilla del caso → ajusta el dato puntual → el QR queda operativo de inmediato.',
                    'priority': 'low',
                },
            ],
        },
        'content_generator_module': {
            'epic_title': 'Alcance ampliado: Generador de Contenido con IA y Calendario Editorial',
            'epic_description': (
                'Desglose técnico del módulo de contenido. Cada requerimiento cubre una '
                'capacidad del generador o del calendario editorial.'
            ),
            'requirements': [
                {
                    'flowKey': 'content-redaccion-ia',
                    'item': 'Redacción asistida con IA',
                    'title': 'Borradores de blogs, correos y posts desde un brief simple',
                    'description': 'A partir de una idea breve, la IA entrega borradores de blogs, newsletters y publicaciones, con control de tono, extensión y formato en un par de clics.',
                    'configuration': 'Generación vía proveedor de IA con plantillas de prompt por tipo de pieza y parámetros de tono/extensión.',
                    'usageFlow': 'El usuario escribe el brief → elige tipo de pieza y tono → recibe el borrador → lo edita y aprueba.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-voz-de-marca',
                    'item': 'Voz de marca y plantillas',
                    'title': 'La identidad editorial se define una vez y se respeta siempre',
                    'description': 'Tono, estilo, palabras prohibidas y llamados a la acción se configuran una sola vez; cada pieza generada respeta esa voz.',
                    'configuration': 'Perfil editorial persistente (tono, estilo, vocabulario vetado, CTAs) inyectado en cada generación.',
                    'usageFlow': 'El negocio define su voz una vez → cada nueva pieza sale alineada → puede ajustar el perfil cuando la marca evolucione.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-multicanal',
                    'item': 'Multicanal: blog, email y redes',
                    'title': 'Una idea adaptada al formato de cada canal',
                    'description': 'La misma idea se convierte en post largo para blog, asunto y cuerpo para email, y copy corto para Instagram, LinkedIn o X — sin reescribir desde cero.',
                    'configuration': 'Transformaciones por canal con límites de longitud y formato específicos de cada plataforma.',
                    'usageFlow': 'El usuario elige la pieza base → pide las variantes de canal → recibe cada versión adaptada y lista para programar.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'content-calendario-editorial',
                    'item': 'Calendario editorial visual',
                    'title': 'Vista mensual y semanal con arrastrar y soltar',
                    'description': 'Todas las piezas (borrador, programada, publicada) se ven en un calendario mensual o semanal; reorganizar fechas es arrastrar y soltar.',
                    'configuration': 'Calendario con estados por pieza y reprogramación por drag & drop persistida al soltar.',
                    'usageFlow': 'El usuario abre el calendario → ve el plan del mes → arrastra una pieza a otra fecha → el cambio queda guardado.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-programacion-automatica',
                    'item': 'Programación y publicación automática',
                    'title': 'Publicación sola en la fecha y hora agendadas',
                    'description': 'Cada pieza agendada se publica sin intervención: el blog la publica, el correo se envía y las redes conectadas reciben el post en el momento definido.',
                    'configuration': 'Cola de publicación programada (Huey) por canal con manejo de fallos y reintento notificado.',
                    'usageFlow': 'El usuario agenda la pieza → llega la fecha/hora → el sistema publica en el canal → el estado pasa a "publicada".',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-panel-seguimiento',
                    'item': 'Panel de seguimiento',
                    'title': 'Estado y desempeño de cada publicación en un solo lugar',
                    'description': 'Borrador, programada, publicada o fallida: cada pieza muestra su estado y métricas básicas, con reagendar o duplicar a un clic.',
                    'configuration': 'Estados por pieza con métricas básicas por canal y acciones rápidas (reagendar, duplicar).',
                    'usageFlow': 'El usuario abre el panel → revisa estados y desempeño → reintenta una fallida o duplica la que funcionó.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'content-integracion-canales',
                    'item': 'Integración con tus canales',
                    'title': 'Blog, proveedor de email y redes conectados al calendario',
                    'description': 'Lo planeado en el calendario sale publicado en los canales reales del negocio: su blog, su proveedor de correo y sus redes sociales conectadas.',
                    'configuration': 'Conexión API por canal (blog propio, proveedor de email, redes) con validación de credenciales y estado de conexión visible.',
                    'usageFlow': 'El negocio conecta sus canales una vez → el calendario publica en ellos → el estado de conexión avisa si algo requiere re-autorización.',
                    'priority': 'medium',
                },
            ],
        },
        'i18n_module': {
            'epic_title': 'Alcance ampliado: Multi-idioma y Localización Regional',
            'epic_description': (
                'Desglose técnico del módulo de internacionalización. Cada requerimiento '
                'cubre una capacidad del alcance multi-idioma.'
            ),
            'requirements': [
                {
                    'flowKey': 'i18n-multi-idioma',
                    'item': 'Soporte multi-idioma nativo',
                    'title': 'Todo el contenido servido en dos o más idiomas',
                    'description': 'El sitio sirve su contenido completo en los idiomas definidos, con selector visible y la preferencia del usuario recordada entre visitas.',
                    'configuration': 'Estructura i18n nativa (rutas o prefijos por idioma), selector persistente y contenido bilingüe por sección.',
                    'usageFlow': 'El visitante cambia el idioma en el selector → todo el contenido cambia → su preferencia queda recordada para la próxima visita.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'i18n-formatos-regionales',
                    'item': 'Formatos regionales de moneda y fecha',
                    'title': 'Monedas, números y fechas en el formato de cada región',
                    'description': 'Los montos, números y fechas se muestran con el formato correcto de la región o idioma activo, sin ambigüedades para el visitante.',
                    'configuration': 'Formateo por locale (separadores, símbolo de moneda, orden de fecha) aplicado en todas las vistas con datos.',
                    'usageFlow': 'El visitante navega en su idioma → precios y fechas aparecen en su formato regional → no hay confusión de montos ni fechas.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'i18n-catalogos-por-pais',
                    'item': 'Catálogos y precios por país',
                    'title': 'Productos, precios y disponibilidad diferenciados por mercado',
                    'description': 'El negocio puede mostrar catálogos, precios y disponibilidad distintos según el país o mercado objetivo del visitante.',
                    'configuration': 'Reglas de visibilidad y precio por región sobre el catálogo, con mercado por defecto de respaldo.',
                    'usageFlow': 'El visitante entra desde un mercado configurado → ve el catálogo y precios de su región → compra en las condiciones correctas.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'i18n-flujo-traduccion',
                    'item': 'Flujo de traducción integrado',
                    'title': 'Panel para gestionar traducciones sin intervención técnica',
                    'description': 'El equipo del negocio administra las traducciones de cada sección desde el panel, con indicador claro de contenido pendiente por traducir.',
                    'configuration': 'Editor de traducciones por sección con estado (traducido/pendiente) y vista previa por idioma.',
                    'usageFlow': 'El administrador abre el panel de traducciones → ve lo pendiente → completa la traducción → publica el idioma actualizado.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'i18n-deteccion-idioma',
                    'item': 'Detección automática de idioma',
                    'title': 'El visitante llega directo a la versión de su idioma',
                    'description': 'El sitio detecta el idioma preferido del navegador y redirige automáticamente a la versión correspondiente desde la primera visita.',
                    'configuration': 'Detección por encabezado del navegador con redirección a la variante correcta y respeto de la elección manual posterior.',
                    'usageFlow': 'El visitante abre el sitio → es llevado a su idioma automáticamente → si cambia manualmente, esa elección manda.',
                    'priority': 'medium',
                },
            ],
        },
        'live_chat_module': {
            'epic_title': 'Alcance ampliado: Chat en Vivo First-Party',
            'epic_description': (
                'Desglose técnico del módulo de chat. Cada requerimiento cubre una '
                'capacidad del chat alojado en la infraestructura del cliente.'
            ),
            'requirements': [
                {
                    'flowKey': 'chat-widget-embebido',
                    'item': 'Widget de chat embebido',
                    'title': 'Conversación en tiempo real sin salir de la página',
                    'description': 'Un componente flotante en el sitio permite al visitante iniciar y continuar una conversación mientras sigue navegando la página.',
                    'configuration': 'Widget propio (sin servicios externos) con estado abierto/minimizado persistente y branding del negocio.',
                    'usageFlow': 'El visitante abre el widget → escribe su mensaje → conversa en tiempo real sin abandonar la página.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-panel-agente',
                    'item': 'Panel de agente en el admin',
                    'title': 'Los agentes atienden desde el propio panel administrativo',
                    'description': 'Las conversaciones se atienden desde el mismo panel del sitio: sin aplicaciones externas, cuentas adicionales ni costos por asiento.',
                    'configuration': 'Bandeja de conversaciones con estados (nueva, en curso, cerrada), asignación de agente y vista de historial del visitante.',
                    'usageFlow': 'El agente abre la bandeja → toma una conversación → responde y la cierra al resolver.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-websocket',
                    'item': 'Comunicación en tiempo real (WebSocket)',
                    'title': 'Mensajes instantáneos en ambos sentidos',
                    'description': 'Visitante y agente se leen al instante, sin recargar la página ni demoras perceptibles, incluso en conversaciones largas.',
                    'configuration': 'Conexión persistente WebSocket con reconexión automática y entrega confirmada de mensajes.',
                    'usageFlow': 'Cualquiera de las partes escribe → el mensaje aparece al instante del otro lado → si se corta la conexión, se restablece sola.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-historial-propio',
                    'item': 'Historial de conversaciones propio',
                    'title': 'Todas las conversaciones guardadas en la base del cliente',
                    'description': 'El historial completo vive en la base de datos del negocio, con búsqueda, filtros por fecha y exportación — los datos son 100% propios.',
                    'configuration': 'Persistencia de conversaciones y mensajes con búsqueda por texto, filtros por fecha/estado y exportación.',
                    'usageFlow': 'El administrador busca una conversación → la encuentra por texto o fecha → la revisa o exporta cuando la necesita.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'chat-respuestas-automaticas',
                    'item': 'Respuestas automáticas configurables',
                    'title': 'Bienvenida, fuera de horario y FAQ sin agente disponible',
                    'description': 'El chat responde solo con mensajes de bienvenida, avisos fuera de horario y respuestas frecuentes, manteniendo la atención activa 24/7.',
                    'configuration': 'Mensajes automáticos configurables por horario de atención y catálogo de respuestas frecuentes.',
                    'usageFlow': 'El visitante escribe fuera de horario → recibe el aviso y las opciones de FAQ → su mensaje queda en la bandeja para el siguiente turno.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'chat-notificaciones',
                    'item': 'Notificaciones de nuevos chats',
                    'title': 'El agente se entera al instante de cada mensaje nuevo',
                    'description': 'Cada conversación nueva o mensaje entrante notifica al agente en tiempo real, garantizando tiempos de respuesta mínimos.',
                    'configuration': 'Alertas en el panel (sonido/contador) al crear conversación o recibir mensaje, con indicador de no leídos.',
                    'usageFlow': 'El visitante escribe → el agente ve la alerta y el contador → entra a la conversación y responde.',
                    'priority': 'medium',
                },
            ],
        },
        'dark_mode_module': {
            'epic_title': 'Alcance ampliado: Modo Oscuro y Claro',
            'epic_description': (
                'Desglose técnico del módulo de tema visual. Cada requerimiento cubre '
                'una capacidad del sistema de modo claro/oscuro.'
            ),
            'requirements': [
                {
                    'flowKey': 'dark-paleta-dual',
                    'item': 'Paleta de colores dual',
                    'title': 'Dos sistemas de color completos y coherentes',
                    'description': 'Claro y oscuro tienen cada uno su paleta completa: textos legibles, contrastes correctos y coherencia visual en todas las vistas.',
                    'configuration': 'Variables CSS semánticas por tema con verificación de contraste en componentes clave.',
                    'usageFlow': 'El usuario alterna el tema → toda la interfaz cambia al instante → nada queda ilegible ni fuera de estilo.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'dark-deteccion-sistema',
                    'item': 'Detección automática de preferencia del sistema',
                    'title': 'El tema inicial respeta la preferencia del dispositivo',
                    'description': 'Desde la primera visita, el sitio aplica el modo que el usuario ya usa en su sistema operativo, sin que tenga que configurarlo.',
                    'configuration': 'Lectura de prefers-color-scheme al cargar, antes del primer render para evitar parpadeo de tema.',
                    'usageFlow': 'El visitante con su sistema en oscuro abre el sitio → lo ve directamente en oscuro → sin destello claro intermedio.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'dark-persistencia',
                    'item': 'Persistencia de elección del usuario',
                    'title': 'La elección manual manda sobre el sistema y se recuerda',
                    'description': 'Si el usuario elige un modo manualmente, esa elección se guarda y prevalece en futuras visitas sobre la configuración del sistema.',
                    'configuration': 'Preferencia almacenada en el navegador con prioridad sobre prefers-color-scheme.',
                    'usageFlow': 'El usuario cambia el tema manualmente → cierra y vuelve otro día → el sitio abre en el tema que eligió.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'dark-transicion',
                    'item': 'Transición fluida entre modos',
                    'title': 'Cambio de tema suave, sin parpadeos',
                    'description': 'Alternar entre claro y oscuro se siente elegante: transición suave, sin saltos visuales ni destellos que interrumpan la navegación.',
                    'configuration': 'Transiciones CSS acotadas a colores/fondos con duración corta y sin animar propiedades costosas.',
                    'usageFlow': 'El usuario pulsa el toggle → la interfaz funde de un tema al otro → sigue navegando sin interrupción.',
                    'priority': 'low',
                },
                {
                    'flowKey': 'dark-adaptacion-medios',
                    'item': 'Adaptación de imágenes y multimedia',
                    'title': 'Imágenes e íconos legibles en ambos modos',
                    'description': 'Logos, íconos y gráficos se ajustan al modo activo para mantener contraste y legibilidad, sin elementos que "desaparezcan" en oscuro.',
                    'configuration': 'Variantes de assets por tema donde aplique e íconos con color heredado del tema.',
                    'usageFlow': 'El usuario alterna el tema → los elementos gráficos se adaptan → todo sigue visible y con buen contraste.',
                    'priority': 'medium',
                },
            ],
        },
        'gift_cards_module': {
            'epic_title': 'Alcance ampliado: Gift Cards y Vouchers Digitales',
            'epic_description': (
                'Desglose técnico del módulo de gift cards. Cada requerimiento cubre '
                'una etapa del ciclo de vida de la tarjeta de regalo.'
            ),
            'requirements': [
                {
                    'flowKey': 'gift-creacion-venta',
                    'item': 'Creación y venta de gift cards',
                    'title': 'Compra de tarjetas de regalo con saldo configurable',
                    'description': 'Los clientes compran gift cards digitales con el saldo que elijan directamente en el sitio, con pago integrado y entrega inmediata al destinatario.',
                    'configuration': 'Montos configurables (fijos o libres dentro de un rango), pago por la pasarela activa y entrega por correo al destinatario.',
                    'usageFlow': 'El comprador elige monto y destinatario → paga → el destinatario recibe la tarjeta con su código por correo.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'gift-canje-checkout',
                    'item': 'Canje en checkout con código único',
                    'title': 'El código se aplica como pago parcial o total en el checkout',
                    'description': 'El destinatario ingresa su código único en el checkout y el saldo se descuenta del total, como pago parcial o completo, con validación en el momento.',
                    'configuration': 'Códigos únicos verificables con validación de vigencia y saldo en el checkout; descuento aplicado de forma atómica.',
                    'usageFlow': 'El destinatario compra → ingresa el código en el checkout → el sistema valida saldo y vigencia → el total se descuenta y el saldo restante queda registrado.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'gift-historial-saldo',
                    'item': 'Historial de saldo y movimientos',
                    'title': 'Saldo disponible y movimientos consultables por ambas partes',
                    'description': 'Comprador y destinatario consultan el saldo disponible, los canjes realizados y la fecha de vencimiento de cada tarjeta.',
                    'configuration': 'Registro de movimientos por tarjeta (compra, canjes, ajustes) con consulta por código.',
                    'usageFlow': 'El usuario consulta su tarjeta → ve saldo, movimientos y vencimiento → sabe exactamente cuánto puede canjear.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'gift-diseno-marca',
                    'item': 'Diseño de marca personalizado',
                    'title': 'Tarjetas con la identidad del negocio y mensaje personal',
                    'description': 'Cada gift card sale con el logo y colores de la marca, más un mensaje personalizable del comprador para el destinatario.',
                    'configuration': 'Plantilla de tarjeta con identidad visual del negocio y campo de mensaje personal del comprador.',
                    'usageFlow': 'El comprador escribe su mensaje → la tarjeta se genera con la marca y el mensaje → el destinatario recibe una pieza cuidada.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'gift-vencimiento',
                    'item': 'Vencimiento configurable',
                    'title': 'Políticas de vencimiento por tipo de tarjeta con avisos',
                    'description': 'El negocio define el vencimiento por tipo de tarjeta (sin vencimiento, 6 meses, 1 año o personalizado) y el destinatario recibe avisos antes de expirar.',
                    'configuration': 'Política de vencimiento por tipo con notificaciones automáticas programadas antes de la expiración.',
                    'usageFlow': 'La tarjeta se acerca a su vencimiento → el destinatario recibe el aviso → canjea a tiempo o el negocio decide extender.',
                    'priority': 'medium',
                },
            ],
        },
    },
    'en': {
        'integration_electronic_invoicing': {
            'epic_title': 'Extended scope: Electronic Invoicing & DIAN Integration',
            'epic_description': (
                'Technical breakdown of the electronic invoicing module. Each requirement '
                'details one element of the module scope with its acceptance criteria.'
            ),
            'requirements': [
                {
                    'flowKey': 'invoicing-generacion-comprobantes',
                    'item': 'Electronic Receipt Generation',
                    'title': 'Invoices, notes and support documents issued from business flows',
                    'description': 'Every completed sale or order can generate its electronic receipt (invoice, credit/debit note or support document) without leaving the platform or re-typing data.',
                    'configuration': 'Fiscal field mapping (client, items, taxes), authorized numbering and issuance via the invoicing provider API; retry queue for provider errors.',
                    'usageFlow': 'An order is completed → the system builds the receipt → sends it to the provider → stores number, CUFE and PDF → notifies the result.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'invoicing-sincronizacion-fiscal',
                    'item': 'Fiscal Data Synchronization',
                    'title': 'Bidirectional sync of clients, products and taxes',
                    'description': 'Fiscal catalogs stay aligned between the platform and the invoicing system: whatever is created or edited on one side is reflected on the other, with no double data entry.',
                    'configuration': 'Periodic jobs (Huey) plus provider webhooks when available; external key per record and conflict resolution by last-update date.',
                    'usageFlow': 'A client/product is created or edited → sync is enqueued → the record is linked by external id → remote changes flow back into the platform.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'invoicing-trazabilidad-estado',
                    'item': 'Fiscal Status Traceability',
                    'title': 'DIAN status tracking for every receipt',
                    'description': 'From the platform you can check whether each receipt was issued, accepted, rejected or is still in process, with its full history and the rejection reason when applicable.',
                    'configuration': 'Status queries via API with scheduled polling; per-receipt status timeline storage.',
                    'usageFlow': 'The user opens an invoice detail → sees the status timeline → on rejection, sees the reported reason and can re-issue.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'invoicing-proveedores-colombia',
                    'item': 'Colombian Provider Integration',
                    'title': "Connection with the client's invoicing provider (Siigo, Alegra or other)",
                    'description': 'The integration is built against the provider the business already uses or chooses, validated end to end before going to production.',
                    'configuration': 'Client API credentials in environment variables; per-provider adapter with a common contract (issue, query, void) so switching providers never means rebuilding the flows.',
                    'usageFlow': 'Credentials are configured → the connection is validated with a sandbox test issuance → production mode is enabled.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'invoicing-automatizaciones-api',
                    'item': 'API Automations',
                    'title': 'Payment reconciliation and automatic issuance',
                    'description': 'Business events trigger fiscal actions with no manual steps: issue on order completion, reconcile received payments and notify status changes.',
                    'configuration': 'Event-based trigger rules (order completed, payment confirmed) and fiscal status notifications by email to the responsible user.',
                    'usageFlow': 'The configured event happens → the automation runs the fiscal action → the result is logged and notified.',
                    'priority': 'medium',
                },
            ],
        },
        'integration_regional_payments': {
            'epic_title': 'Extended scope: Regional Payment Gateway (Colombia)',
            'epic_description': (
                'Technical breakdown of the local payments integration. Each requirement '
                'covers one gateway in the module scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'regional-payu',
                    'item': 'PayU',
                    'title': 'PayU checkout: cards, PSE and cash methods',
                    'description': 'End customers pay with the most used local methods in Colombia (card, PSE, Efecty, Nequi, Daviplata) and the order is confirmed only when the gateway confirms the payment.',
                    'configuration': "Client's PayU account (sandbox and production), per-transaction integrity signature, confirmation webhook and amount/currency validation before approving the order.",
                    'usageFlow': 'Cart → checkout → payment at PayU → return with status → order confirmation and customer email.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'regional-wompi',
                    'item': 'Wompi (Bancolombia)',
                    'title': 'Wompi checkout: PSE, cards and Bancolombia button',
                    'description': 'Local alternative with excellent Bancolombia coverage: customers pay with PSE, card, Nequi or the Bancolombia button, with the payment status traced in the platform.',
                    'configuration': "Client's Wompi public/private keys, event signature verification and reconciliation of each transaction's final status.",
                    'usageFlow': 'Checkout → Wompi widget or redirect → payment → confirmation event → order approved or rejected by status.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'regional-epayco',
                    'item': 'ePayco',
                    'title': 'ePayco checkout: PSE, cards and physical collection',
                    'description': 'Agile Colombian option: PSE, card and physical collection payments, with asynchronous confirmation verified server-side.',
                    'configuration': "Client's ePayco credentials, response page and server-to-server confirmation URL with signature validation.",
                    'usageFlow': 'Checkout → payment at ePayco → customer response page → server-to-server confirmation → order status updated.',
                    'priority': 'medium',
                },
            ],
        },
        'integration_international_payments': {
            'epic_title': 'Extended scope: International Payment Gateway',
            'epic_description': (
                'Technical breakdown of the international payments integration. Each '
                'requirement covers one gateway in the module scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'intl-stripe',
                    'item': 'Stripe',
                    'title': 'International charges with Stripe: cards and multiple currencies',
                    'description': 'The business takes credit/debit card payments from any country, one-time or recurring, with verified confirmation before delivering the product or service.',
                    'configuration': 'Restricted API keys, signed webhooks (payment succeeded/failed), enabled currency handling and subscription mode when applicable.',
                    'usageFlow': 'Checkout → Stripe secure form → payment → confirmation webhook → order approved and receipt email.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'intl-paypal',
                    'item': 'PayPal',
                    'title': 'PayPal charges: balance, cards and international accounts',
                    'description': 'Customers who prefer PayPal pay with their balance or linked card; the platform verifies the payment capture before confirming the order.',
                    'configuration': "Client's PayPal app credentials (sandbox and live), order capture via API and status verification before approval.",
                    'usageFlow': 'Checkout → PayPal button → approval at PayPal → payment capture → order confirmation.',
                    'priority': 'medium',
                },
            ],
        },
        'pwa_module': {
            'epic_title': 'Extended scope: Installable Mobile App (PWA)',
            'epic_description': (
                'Technical breakdown of the PWA module. Each requirement details one '
                'element of the installable/offline scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'pwa-instalacion-dispositivo',
                    'item': 'Device Installation',
                    'title': 'Installation as an app on phone and computer',
                    'description': "The site installs from the browser as an app with the brand's icon and name on the home screen, opening in its own window without the browser bar.",
                    'configuration': 'Web App Manifest (name, colors, maskable icons), registered service worker and compliance with Chrome/Safari installability criteria.',
                    'usageFlow': 'The visitor browses the site → the browser offers "Install app" → confirms → the icon lands on the home screen and opens standalone.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'pwa-offline',
                    'item': 'Offline Functionality',
                    'title': 'Content access without an internet connection',
                    'description': 'Offline, the app keeps showing previously visited content and a clear offline screen for what is unavailable; on reconnection, content refreshes by itself.',
                    'configuration': 'Per-resource caching strategies (shell precache, stale-while-revalidate for content) and a fallback offline page.',
                    'usageFlow': 'The user loses connection → opens the app → sees cached content and an offline notice → on reconnection everything refreshes in the background.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'pwa-notificaciones-push',
                    'item': 'Push Notifications',
                    'title': 'Push notifications with user consent',
                    'description': 'The business sends direct device notices (news, promotions, updates) only to users who opted in, with an unsubscribe option.',
                    'configuration': 'Web Push subscription with VAPID keys, explicit permission prompt and segmented sending from the backend.',
                    'usageFlow': 'The user grants permission → the business publishes a notice → the notification reaches the device even with the site closed → tapping it opens the right view.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'pwa-splash-personalizada',
                    'item': 'Custom Splash Screen',
                    'title': "Splash screen with the brand's identity",
                    'description': 'Opening the installed app shows a loading screen with the corporate logo and colors instead of a generic browser background.',
                    'configuration': 'Icons and background/theme colors defined in the manifest to generate the native splash on Android/iOS.',
                    'usageFlow': 'The user opens the installed app → sees the branded splash → lands on the loaded home screen.',
                    'priority': 'low',
                },
                {
                    'flowKey': 'pwa-sincronizacion-segundo-plano',
                    'item': 'Background Sync',
                    'title': 'Automatic retry of operations on reconnection',
                    'description': 'Actions performed offline (forms, changes) are queued and sent on their own when the signal returns, without the user repeating anything.',
                    'configuration': 'Pending-operation queue with Background Sync and retries with completion confirmation.',
                    'usageFlow': 'The user submits an action offline → it queues with a notice → on reconnection it syncs → the user gets the confirmation.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'pwa-actualizacion-automatica',
                    'item': 'Automatic Updates',
                    'title': 'Transparent updates to the latest version',
                    'description': 'The app updates itself: users always run the latest version with no manual steps and no app stores.',
                    'configuration': 'Service worker versioning with controlled activation and a discreet "new version available" hint when applicable.',
                    'usageFlow': 'A new version ships → the service worker downloads it in the background → next launch the app is already updated.',
                    'priority': 'medium',
                },
            ],
        },
        'corporate_branding_module': {
            'epic_title': 'Extended scope: Visual Identity & Corporate Branding',
            'epic_description': (
                'Technical breakdown of the branding module. Each requirement covers one '
                'touchpoint where the brand identity is applied.'
            ),
            'requirements': [
                {
                    'flowKey': 'branding-correos-transaccionales',
                    'item': 'Branded Transactional Emails',
                    'title': 'Every system email ships with the brand template',
                    'description': 'Welcome, confirmations, alerts and password recovery arrive with the brand logo, colors, typography and signature — never as generic plain text.',
                    'configuration': 'Responsive HTML templates tested on Gmail/Outlook, with per-event variables and a plain-text fallback version.',
                    'usageFlow': 'A system event happens → the brand template renders with the event data → the email arrives with the business identity.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'branding-pdfs-exportables',
                    'item': 'PDFs & Exports with Branding',
                    'title': 'Generated documents with branded header and footer',
                    'description': 'Invoices, reports, certificates and Excel/CSV downloads ship with logo, corporate palette and brand footer: every document reinforces the professional image.',
                    'configuration': 'Standardized header/footer in the PDF generator and brand styles in tabular exports.',
                    'usageFlow': 'The user downloads or receives a system document → the file arrives with the complete brand identity.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'branding-open-graph',
                    'item': 'Social Link Preview Cards (Open Graph)',
                    'title': 'Shared links show a card with brand logo and image',
                    'description': 'Sharing a site link on WhatsApp, Facebook, LinkedIn or X shows a card with the brand logo, image and colors instead of a plain link — direct impact on perception and clicks.',
                    'configuration': 'Open Graph and Twitter Card metadata per public view (title, description, image), validated with the Meta and LinkedIn debuggers.',
                    'usageFlow': 'A user shares a link → the social network reads the metadata → the conversation shows the brand card.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'branding-pantallas-sistema',
                    'item': 'System Screens with Brand Identity',
                    'title': "Errors, login and loading states in the brand's voice",
                    'description': "404/500 pages, maintenance, login and loading states use the business's visual identity and messaging instead of the framework's generic screens.",
                    'configuration': 'Custom error and maintenance templates, skeletons/spinners with the corporate palette and copy in the brand voice.',
                    'usageFlow': 'The user hits an error or waits for a load → the screen keeps the identity and guides them forward.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'branding-metadatos-estructurados',
                    'item': 'Structured Metadata for Search & AI',
                    'title': 'The brand shows correctly on Google and AI assistants',
                    'description': 'Search engines and assistants (Google, Bing, ChatGPT, Perplexity) receive structured organization data to display the logo, contact and social profiles in panels and rich results.',
                    'configuration': "JSON-LD Organization (logo, colors, social profiles, contact data) validated with Google's rich results test.",
                    'usageFlow': 'A search engine or assistant indexes the site → reads the JSON-LD → displays the brand with its correct data.',
                    'priority': 'medium',
                },
            ],
        },
        'behavior_tracking_module': {
            'epic_title': 'Extended scope: User Behavior Tracking',
            'epic_description': (
                'Technical breakdown of the behavior module. Included scope: up to 15 '
                'tracked views, a panel with up to 8 KPIs and 4 charts, 12-month retention.'
            ),
            'requirements': [
                {
                    'flowKey': 'behavior-sesiones',
                    'item': 'Session & Open Tracking',
                    'title': 'First-party logging of every usage session',
                    'description': "Every entry is logged with date, device and whether it's a first visit or a return — all in the business's own data, with no third-party cookies or external tools.",
                    'configuration': 'First-party session event with a persistent anonymous identifier, timestamp and new-vs-returning classification.',
                    'usageFlow': 'The user enters the platform → the session is logged with its context → the data feeds KPIs and charts.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-tiempo-por-vista',
                    'item': 'Views Opened & Time per View',
                    'title': 'Measurement of opened views and seconds of active time',
                    'description': 'The system records which views each user opens and how much active time they spend on each, over the up-to-15 views agreed with the client at kickoff.',
                    'configuration': 'Instrumentation of the agreed views with active-time measurement (heartbeat) and inactivity cutoff.',
                    'usageFlow': 'The user navigates between views → each open and its duration are logged → they feed the interest map and the funnel.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-mapa-interes',
                    'item': 'Interest Map per View',
                    'title': 'View ranking by attention received',
                    'description': 'The business sees which views concentrate attention (accumulated time and visits) and which go unnoticed, to decide where to invest improvements.',
                    'configuration': 'Per-view aggregation of total time and open count, sorted by interest.',
                    'usageFlow': 'The admin opens the behavior panel → sees the view ranking → identifies what works and what does not.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-embudo-abandonos',
                    'item': 'Journey Funnel with Drop-off',
                    'title': 'Main funnel with drop-off points',
                    'description': 'One (1) funnel defined with the client shows how users advance across the tracked views and at which exact step they leave.',
                    'configuration': 'Funnel definition over the tracked views with per-step conversion and drop-off.',
                    'usageFlow': 'The admin opens the funnel → sees the share advancing at each step → spots the biggest leak.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-panel-integrado',
                    'item': 'Built-in Behavior Panel',
                    'title': 'Own dashboard with up to 8 KPIs and 4 charts',
                    'description': 'Inside the own admin panel: sessions, average time, most-opened views and device breakdown — no external licenses or subscriptions.',
                    'configuration': 'Optimized aggregate queries over the first-party events; KPI cards and charts capped to the contracted scope (8 KPIs / 4 charts).',
                    'usageFlow': 'The admin enters the panel → sees the updated KPIs and charts → filters by date range.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'behavior-desglose-dispositivo',
                    'item': 'Device Breakdown',
                    'title': 'Usage by mobile, tablet and desktop',
                    'description': 'The business knows which device type its users prefer, to prioritize improvements where users actually are.',
                    'configuration': 'Device classification by user-agent on the session event, aggregated in the panel.',
                    'usageFlow': 'The admin opens the breakdown → sees the mobile/tablet/desktop share → prioritizes the dominant channel.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'behavior-retencion-datos',
                    'item': 'Own Data with 12-Month Retention',
                    'title': "Events stored in the client's database for 12 months",
                    'description': "Data lives in the business's own database and is kept for 12 months; it does not include screen recording, click heatmaps or cross-site tracking.",
                    'configuration': 'Scheduled purge of events older than 12 months and documented scope limits.',
                    'usageFlow': 'Events accumulate in the own database → the monthly purge removes what exceeds retention → the panel always queries current data.',
                    'priority': 'medium',
                },
            ],
        },
        'reports_alerts_module': {
            'epic_title': 'Extended scope: Reports & Alerts via Email or WhatsApp',
            'epic_description': (
                'Technical breakdown of the reports and alerts module. Each requirement '
                'covers one channel or capability of the module scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'reports-correo-automatico',
                    'item': 'Automated Email Reports',
                    'title': 'Periodic summaries with key metrics in the inbox',
                    'description': 'The owner receives the business summary (sales, sign-ups, activity) by email without logging in, at the frequency they choose.',
                    'configuration': 'Scheduled report generation with the brand template and the agreed metrics; delivery log.',
                    'usageFlow': 'The scheduled time arrives → the system builds the report with the period data → sends it to the configured email.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'reports-alertas-personalizadas',
                    'item': 'Custom Alerts',
                    'title': 'Alerts on business-defined events and thresholds',
                    'description': 'New sales, user registrations, low stock or any defined metric trigger an immediate notice to the responsible person.',
                    'configuration': 'Configurable event/threshold rules; evaluation on event occurrence and immediate dispatch to the chosen channel.',
                    'usageFlow': 'The event happens (e.g. low stock) → the rule evaluates → the notice arrives on the configured channel with the detail.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'reports-whatsapp',
                    'item': 'WhatsApp Integration',
                    'title': 'Alerts and reports on WhatsApp via the official API',
                    'description': "Notices reach the business's WhatsApp number on the same channel where it already serves customers, using the official API.",
                    'configuration': 'Official WhatsApp API (Cloud API) with approved templates, verified business number and delivery-failure handling.',
                    'usageFlow': 'A report or alert fires → the system sends the approved template via WhatsApp → the owner receives it in chat.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'reports-programacion',
                    'item': 'Scheduled Delivery',
                    'title': 'Configurable report frequency and timing',
                    'description': "Each report is scheduled daily, weekly, monthly or real-time, in the business's preferred time and timezone.",
                    'configuration': 'Scheduled tasks (Huey) per report with frequency, time and timezone configurable from the panel.',
                    'usageFlow': 'The admin sets frequency and time → the system honors the schedule → they can pause or adjust anytime.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'reports-resumen-ejecutivo',
                    'item': 'Periodic Executive Summary',
                    'title': 'Consolidated report for fast decisions',
                    'description': "A report with the project's most relevant metrics, designed to be read in minutes and to decide with data.",
                    'configuration': 'Key metrics agreed with the client and an executive format (headlines + deltas vs previous period).',
                    'usageFlow': 'The configured period arrives → the executive report consolidates → the owner reads it and acts on relevant changes.',
                    'priority': 'medium',
                },
            ],
        },
        'email_marketing_module': {
            'epic_title': 'Extended scope: Email Marketing Integration',
            'epic_description': (
                'Technical breakdown of the email marketing module. Each requirement '
                'covers one capability of the module scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'email-mkt-captura-leads',
                    'item': 'Lead Capture',
                    'title': 'Forms and pop-ups capturing interested visitors',
                    'description': 'Interested visitors leave their email on optimized forms and non-invasive pop-ups, with validation and subscription confirmation.',
                    'configuration': 'Email-validated forms, pop-up display rules (time/scroll/exit) and duplicate-safe registration.',
                    'usageFlow': "The visitor sees the form or pop-up → leaves their email → receives confirmation → joins the business's list.",
                    'priority': 'high',
                },
                {
                    'flowKey': 'email-mkt-automatizaciones',
                    'item': 'Email Automations',
                    'title': 'Automatic welcome, cart and re-engagement sequences',
                    'description': 'Subscribers receive sequences with no manual steps: welcome on sign-up, abandoned-cart reminder, post-purchase follow-up and inactive-user reactivation.',
                    'configuration': "Event triggers (sign-up, cart, purchase, inactivity) wired to the chosen provider's automations.",
                    'usageFlow': 'The event happens → the matching sequence fires → the emails go out at the defined intervals.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'email-mkt-segmentacion',
                    'item': 'Audience Segmentation',
                    'title': 'Subscribers classified by behavior and interests',
                    'description': 'Lists are segmented by behavior, interests and demographics so every message reaches the people it is relevant to.',
                    'configuration': 'Attribute and tag sync from the platform to the provider (purchases, viewed categories, lead source).',
                    'usageFlow': 'The subscriber interacts with the site → their attributes update → campaigns target the right segment.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'email-mkt-analitica',
                    'item': 'Campaign Analytics',
                    'title': 'Open, click and conversion metrics per campaign',
                    'description': 'Every campaign reports opens, clicks, conversions and ROI to optimize the communication strategy with real data.',
                    'configuration': "Metric reads via the provider's API and conversion attribution with UTM parameters on links.",
                    'usageFlow': 'The campaign is sent → metrics are checked from the panel → the business adjusts content and segments by results.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'email-mkt-integracion-plataformas',
                    'item': 'Platform Integration',
                    'title': 'Native connection with the chosen provider (Mailchimp, SendGrid, Brevo…)',
                    'description': 'The platform is wired to the email marketing provider the business uses or chooses, with synced lists and events.',
                    'configuration': 'Provider API credentials, list/audience mapping and sync of sign-ups, unsubscribes and bounces.',
                    'usageFlow': 'Credentials are configured → the connection is validated with a test list → sign-ups and events flow automatically.',
                    'priority': 'high',
                },
            ],
        },
        'qr_generator_module': {
            'epic_title': 'Extended scope: QR Code Generator',
            'epic_description': (
                'Technical breakdown of the QR module. Each requirement covers one '
                'capability of the generator and its lifecycle.'
            ),
            'requirements': [
                {
                    'flowKey': 'qr-generacion-instantanea',
                    'item': 'Instant Generation',
                    'title': 'QR from URLs, text, vCard, WiFi or WhatsApp in seconds',
                    'description': 'Any link, text, vCard contact, WiFi network or WhatsApp number becomes a ready-to-use QR, generated instantly from the panel.',
                    'configuration': 'Server-side generation with configurable error correction and supported content types (URL, text, vCard, WiFi, wa.me).',
                    'usageFlow': 'The admin picks the content type → enters the data → the QR is generated and ready to download or share.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'qr-personalizacion-marca',
                    'item': 'Branded Customization',
                    'title': 'QR with corporate colors, logo and print formats',
                    'description': "Each code can carry the brand's colors and the logo at the center, exported as PNG, SVG or PDF in high resolution without losing scannability.",
                    'configuration': 'Corporate palette applied with contrast/scannability verification and vector exports for print.',
                    'usageFlow': 'The admin applies the brand style → previews and test-scans → downloads the needed format.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-codigos-dinamicos',
                    'item': 'Editable Dynamic Codes',
                    'title': 'Change where a printed QR points without reprinting',
                    'description': 'Dynamic QRs point to an own editable link: the business changes the destination (seasonal menu, promo, event) and the printed code keeps working.',
                    'configuration': 'Own redirector with a short slug per code and destination editing from the panel; the printed QR always points to the redirector.',
                    'usageFlow': 'The admin edits the code destination → saves → every following scan lands on the new destination.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'qr-tracking-escaneos',
                    'item': 'Scan Tracking',
                    'title': 'Scan counts per code, device and moment',
                    'description': 'Each code reports how many times it was scanned, from which device type and when — to measure physical campaigns with data.',
                    'configuration': 'Scan logging at the redirector (timestamp, device) with aggregates per code and campaign.',
                    'usageFlow': 'Someone scans the code → the redirector logs the event and redirects → metrics show in the panel.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-biblioteca',
                    'item': 'Code Library',
                    'title': 'Every QR organized by campaign or purpose',
                    'description': 'Generated codes live in an organized library, ready to reuse, re-download or deactivate once no longer needed.',
                    'configuration': 'Listing grouped by campaign/purpose, active/inactive states and download regeneration.',
                    'usageFlow': 'The admin opens the library → filters by campaign → reuses, downloads or deactivates the code they need.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'qr-casos-de-uso',
                    'item': 'Ready-to-Use Cases',
                    'title': 'Preconfigured templates: menu, WhatsApp, events, reviews',
                    'description': 'Common cases ready to launch the same day: digital menu, WhatsApp link, event check-in, catalog download, surveys, tipping or reviews.',
                    'configuration': 'Per-case templates with the content type and style predefined, editable before generating.',
                    'usageFlow': 'The admin picks the case template → adjusts the specific data → the QR is operational immediately.',
                    'priority': 'low',
                },
            ],
        },
        'content_generator_module': {
            'epic_title': 'Extended scope: AI Content Generator with Editorial Calendar',
            'epic_description': (
                'Technical breakdown of the content module. Each requirement covers one '
                'capability of the generator or the editorial calendar.'
            ),
            'requirements': [
                {
                    'flowKey': 'content-redaccion-ia',
                    'item': 'AI-Assisted Writing',
                    'title': 'Drafts for blogs, emails and posts from a simple brief',
                    'description': 'From a short idea, the AI delivers drafts for blogs, newsletters and posts, with tone, length and format controlled in a couple of clicks.',
                    'configuration': 'Generation via AI provider with per-piece prompt templates and tone/length parameters.',
                    'usageFlow': 'The user writes the brief → picks piece type and tone → receives the draft → edits and approves it.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-voz-de-marca',
                    'item': 'Brand Voice & Templates',
                    'title': 'The editorial identity is defined once and always honored',
                    'description': 'Tone, style, banned words and calls to action are configured once; every generated piece honors that voice.',
                    'configuration': 'Persistent editorial profile (tone, style, banned vocabulary, CTAs) injected into every generation.',
                    'usageFlow': 'The business defines its voice once → every new piece comes out aligned → the profile can evolve with the brand.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-multicanal',
                    'item': 'Multichannel: Blog, Email & Social',
                    'title': "One idea adapted to each channel's format",
                    'description': 'The same idea becomes a long blog post, an email subject and body, and short copy for Instagram, LinkedIn or X — without rewriting from scratch.',
                    'configuration': 'Per-channel transformations with platform-specific length and format limits.',
                    'usageFlow': 'The user picks the base piece → requests the channel variants → receives each adapted version ready to schedule.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'content-calendario-editorial',
                    'item': 'Visual Editorial Calendar',
                    'title': 'Monthly and weekly views with drag and drop',
                    'description': 'Every piece (draft, scheduled, published) shows on a monthly or weekly calendar; rearranging dates is drag and drop.',
                    'configuration': 'Calendar with per-piece states and drag-&-drop rescheduling persisted on drop.',
                    'usageFlow': "The user opens the calendar → sees the month's plan → drags a piece to another date → the change is saved.",
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-programacion-automatica',
                    'item': 'Scheduling & Auto-Publishing',
                    'title': 'Publishing happens on its own at the scheduled date and time',
                    'description': 'Each scheduled piece publishes with no intervention: the blog posts it, the email is sent and connected networks receive the post at the defined moment.',
                    'configuration': 'Scheduled publishing queue (Huey) per channel with failure handling and notified retry.',
                    'usageFlow': 'The user schedules the piece → the date/time arrives → the system publishes to the channel → the state turns "published".',
                    'priority': 'high',
                },
                {
                    'flowKey': 'content-panel-seguimiento',
                    'item': 'Tracking Panel',
                    'title': 'Status and performance of every publication in one place',
                    'description': 'Draft, scheduled, published or failed: each piece shows its state and basic metrics, with reschedule or duplicate one click away.',
                    'configuration': 'Per-piece states with basic per-channel metrics and quick actions (reschedule, duplicate).',
                    'usageFlow': 'The user opens the panel → reviews states and performance → retries a failed piece or duplicates the one that worked.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'content-integracion-canales',
                    'item': 'Channel Integrations',
                    'title': 'Blog, email provider and social networks wired to the calendar',
                    'description': "What's planned on the calendar gets published on the business's real channels: its blog, its email provider and its connected social networks.",
                    'configuration': 'Per-channel API connection (own blog, email provider, social) with credential validation and a visible connection status.',
                    'usageFlow': 'The business connects its channels once → the calendar publishes to them → the connection status warns if re-authorization is needed.',
                    'priority': 'medium',
                },
            ],
        },
        'i18n_module': {
            'epic_title': 'Extended scope: Multi-language & Regional Localization',
            'epic_description': (
                'Technical breakdown of the internationalization module. Each requirement '
                'covers one capability of the multi-language scope.'
            ),
            'requirements': [
                {
                    'flowKey': 'i18n-multi-idioma',
                    'item': 'Native Multi-language Support',
                    'title': 'All content served in two or more languages',
                    'description': "The site serves its complete content in the defined languages, with a visible selector and the user's preference remembered between visits.",
                    'configuration': 'Native i18n structure (per-language routes or prefixes), persistent selector and bilingual content per section.',
                    'usageFlow': 'The visitor switches language in the selector → all content switches → the preference is remembered for the next visit.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'i18n-formatos-regionales',
                    'item': 'Regional Currency & Date Formats',
                    'title': "Currencies, numbers and dates in each region's format",
                    'description': 'Amounts, numbers and dates display in the correct format for the active region or language, with no ambiguity for the visitor.',
                    'configuration': 'Locale-based formatting (separators, currency symbol, date order) applied on every data view.',
                    'usageFlow': 'The visitor browses in their language → prices and dates appear in their regional format → no amount or date confusion.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'i18n-catalogos-por-pais',
                    'item': 'Catalogs & Pricing by Country',
                    'title': 'Products, prices and availability differentiated by market',
                    'description': "The business can show different catalogs, prices and availability depending on the visitor's country or target market.",
                    'configuration': 'Per-region visibility and pricing rules over the catalog, with a default fallback market.',
                    'usageFlow': "The visitor enters from a configured market → sees their region's catalog and prices → buys under the right conditions.",
                    'priority': 'medium',
                },
                {
                    'flowKey': 'i18n-flujo-traduccion',
                    'item': 'Integrated Translation Workflow',
                    'title': 'Panel to manage translations without technical help',
                    'description': "The business team manages each section's translations from the panel, with a clear indicator of content pending translation.",
                    'configuration': 'Per-section translation editor with state (translated/pending) and per-language preview.',
                    'usageFlow': 'The admin opens the translations panel → sees what is pending → completes the translation → publishes the updated language.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'i18n-deteccion-idioma',
                    'item': 'Automatic Language Detection',
                    'title': 'Visitors land directly on their language version',
                    'description': "The site detects the browser's preferred language and automatically redirects to the matching version from the first visit.",
                    'configuration': 'Browser-header detection with redirection to the right variant, honoring later manual choices.',
                    'usageFlow': 'The visitor opens the site → is taken to their language automatically → a manual switch takes precedence afterwards.',
                    'priority': 'medium',
                },
            ],
        },
        'live_chat_module': {
            'epic_title': 'Extended scope: First-Party Live Chat',
            'epic_description': (
                'Technical breakdown of the chat module. Each requirement covers one '
                "capability of the chat hosted on the client's infrastructure."
            ),
            'requirements': [
                {
                    'flowKey': 'chat-widget-embebido',
                    'item': 'Embedded Chat Widget',
                    'title': 'Real-time conversation without leaving the page',
                    'description': 'A floating component on the site lets the visitor start and continue a conversation while still browsing the page.',
                    'configuration': 'Own widget (no external services) with persistent open/minimized state and business branding.',
                    'usageFlow': 'The visitor opens the widget → writes their message → chats in real time without leaving the page.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-panel-agente',
                    'item': 'Agent Panel in Admin',
                    'title': "Agents respond from the site's own admin panel",
                    'description': "Conversations are handled from the site's own panel: no external apps, extra accounts or per-seat costs.",
                    'configuration': "Conversation inbox with states (new, active, closed), agent assignment and the visitor's history view.",
                    'usageFlow': 'The agent opens the inbox → takes a conversation → replies and closes it on resolution.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-websocket',
                    'item': 'Real-time Communication (WebSocket)',
                    'title': 'Instant messages in both directions',
                    'description': 'Visitor and agent read each other instantly, with no page reloads or perceptible delays, even in long conversations.',
                    'configuration': 'Persistent WebSocket connection with automatic reconnection and confirmed message delivery.',
                    'usageFlow': 'Either side writes → the message appears instantly on the other side → a dropped connection re-establishes itself.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'chat-historial-propio',
                    'item': 'Owned Conversation History',
                    'title': "All conversations stored in the client's database",
                    'description': "The full history lives in the business's database, with search, date filters and export — the data is 100% owned.",
                    'configuration': 'Conversation and message persistence with text search, date/state filters and export.',
                    'usageFlow': 'The admin searches a conversation → finds it by text or date → reviews or exports it when needed.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'chat-respuestas-automaticas',
                    'item': 'Configurable Auto-responses',
                    'title': 'Welcome, after-hours and FAQ with no agent available',
                    'description': 'The chat answers on its own with welcome messages, after-hours notices and frequent answers, keeping support active 24/7.',
                    'configuration': 'Automatic messages configurable by business hours and a frequent-answers catalog.',
                    'usageFlow': "The visitor writes after hours → receives the notice and FAQ options → their message waits in the inbox for the next shift.",
                    'priority': 'medium',
                },
                {
                    'flowKey': 'chat-notificaciones',
                    'item': 'New Chat Notifications',
                    'title': 'Agents learn of every new message instantly',
                    'description': 'Every new conversation or incoming message notifies the agent in real time, guaranteeing minimal response times.',
                    'configuration': 'Panel alerts (sound/counter) on conversation creation or new message, with an unread indicator.',
                    'usageFlow': 'The visitor writes → the agent sees the alert and counter → enters the conversation and replies.',
                    'priority': 'medium',
                },
            ],
        },
        'dark_mode_module': {
            'epic_title': 'Extended scope: Dark & Light Mode',
            'epic_description': (
                'Technical breakdown of the visual theme module. Each requirement covers '
                'one capability of the light/dark system.'
            ),
            'requirements': [
                {
                    'flowKey': 'dark-paleta-dual',
                    'item': 'Dual Color Palette',
                    'title': 'Two complete, coherent color systems',
                    'description': 'Light and dark each have a full palette: readable text, correct contrast and visual coherence across every view.',
                    'configuration': 'Semantic CSS variables per theme with contrast verification on key components.',
                    'usageFlow': 'The user toggles the theme → the whole interface switches instantly → nothing becomes unreadable or off-style.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'dark-deteccion-sistema',
                    'item': 'Automatic System Preference Detection',
                    'title': "The initial theme honors the device's preference",
                    'description': 'From the first visit, the site applies the mode the user already uses on their operating system, with no configuration needed.',
                    'configuration': 'prefers-color-scheme read at load, before first render, to avoid a theme flash.',
                    'usageFlow': 'A visitor with a dark system opens the site → sees it directly in dark → with no light flash in between.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'dark-persistencia',
                    'item': 'User Choice Persistence',
                    'title': 'Manual choice wins over the system and is remembered',
                    'description': 'If the user picks a mode manually, that choice is stored and prevails on future visits over the operating system setting.',
                    'configuration': 'Preference stored in the browser with priority over prefers-color-scheme.',
                    'usageFlow': 'The user switches the theme manually → returns another day → the site opens in the theme they chose.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'dark-transicion',
                    'item': 'Smooth Mode Transition',
                    'title': 'Smooth theme switch, no flashes',
                    'description': 'Switching between light and dark feels elegant: a smooth transition with no visual jumps or flashes interrupting navigation.',
                    'configuration': 'CSS transitions limited to colors/backgrounds with short duration, avoiding expensive properties.',
                    'usageFlow': 'The user taps the toggle → the interface fades from one theme to the other → they keep browsing uninterrupted.',
                    'priority': 'low',
                },
                {
                    'flowKey': 'dark-adaptacion-medios',
                    'item': 'Image & Media Adaptation',
                    'title': 'Images and icons readable in both modes',
                    'description': 'Logos, icons and graphics adjust to the active mode to keep contrast and readability, with no elements "disappearing" in dark.',
                    'configuration': 'Per-theme asset variants where needed and icons inheriting the theme color.',
                    'usageFlow': 'The user toggles the theme → graphic elements adapt → everything stays visible with good contrast.',
                    'priority': 'medium',
                },
            ],
        },
        'gift_cards_module': {
            'epic_title': 'Extended scope: Gift Cards & Digital Vouchers',
            'epic_description': (
                'Technical breakdown of the gift cards module. Each requirement covers '
                "one stage of the gift card's lifecycle."
            ),
            'requirements': [
                {
                    'flowKey': 'gift-creacion-venta',
                    'item': 'Gift Card Creation & Sales',
                    'title': 'Gift card purchase with configurable balance',
                    'description': 'Customers buy digital gift cards with the balance they choose directly on the site, with integrated payment and immediate delivery to the recipient.',
                    'configuration': 'Configurable amounts (fixed or free within a range), payment through the active gateway and email delivery to the recipient.',
                    'usageFlow': 'The buyer picks amount and recipient → pays → the recipient receives the card with its code by email.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'gift-canje-checkout',
                    'item': 'Checkout Redemption with Unique Code',
                    'title': 'The code applies as partial or full payment at checkout',
                    'description': 'The recipient enters their unique code at checkout and the balance is discounted from the total, as partial or full payment, validated on the spot.',
                    'configuration': 'Unique verifiable codes with validity and balance validation at checkout; discount applied atomically.',
                    'usageFlow': 'The recipient shops → enters the code at checkout → the system validates balance and validity → the total is discounted and the remaining balance recorded.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'gift-historial-saldo',
                    'item': 'Balance & Transaction History',
                    'title': 'Balance and movements visible to both parties',
                    'description': 'Buyer and recipient can check the available balance, redemptions made and the expiration date of each card.',
                    'configuration': 'Per-card movement log (purchase, redemptions, adjustments) queryable by code.',
                    'usageFlow': 'The user checks their card → sees balance, movements and expiration → knows exactly how much they can redeem.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'gift-diseno-marca',
                    'item': 'Custom Branded Design',
                    'title': "Cards with the business's identity and a personal message",
                    'description': "Every gift card ships with the brand's logo and colors, plus a customizable message from the buyer to the recipient.",
                    'configuration': "Card template with the business's visual identity and a personal-message field for the buyer.",
                    'usageFlow': 'The buyer writes their message → the card is generated with the brand and message → the recipient receives a polished piece.',
                    'priority': 'medium',
                },
                {
                    'flowKey': 'gift-vencimiento',
                    'item': 'Configurable Expiration',
                    'title': 'Per-card-type expiration policies with notices',
                    'description': 'The business defines expiration per card type (no expiration, 6 months, 1 year or custom) and the recipient gets notices before it expires.',
                    'configuration': 'Per-type expiration policy with automatic notifications scheduled before expiry.',
                    'usageFlow': 'The card approaches expiry → the recipient receives the notice → redeems in time or the business decides to extend.',
                    'priority': 'medium',
                },
            ],
        },
    },
}


def _norm_id_list(raw: Any) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [str(v).strip() for v in raw if isinstance(v, str) and str(v).strip()]


def _epic_key_for(module_id: str) -> str:
    return f"mod-{slugify(str(module_id)).replace('_', '-')}"


def _module_match_keys(module_id: str) -> set[str]:
    return {module_id, f'module-{module_id}', _epic_key_for(module_id)}


def _epic_requirements(epic: dict) -> list:
    reqs = epic.get('requirements')
    return reqs if isinstance(reqs, list) else []


def _epic_matches_module(epic: dict, keys: set[str]) -> bool:
    ids = set(_norm_id_list(epic.get('linked_module_ids') or epic.get('linkedModuleIds')))
    if ids & keys:
        return True
    epic_key = str(epic.get('epicKey') or '').strip()
    return bool(epic_key) and epic_key in keys


def _module_covered(epics: list, keys: set[str]) -> bool:
    """A module is covered when seller/LLM content already speaks for it."""
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        reqs = [r for r in _epic_requirements(epic) if isinstance(r, dict)]
        if _epic_matches_module(epic, keys) and reqs:
            return True
        for req in reqs:
            ids = set(_norm_id_list(req.get('linked_module_ids') or req.get('linkedModuleIds')))
            if ids & keys:
                return True
    return False


def _matching_empty_epic(epics: list, keys: set[str]) -> dict | None:
    for epic in epics:
        if (
            isinstance(epic, dict)
            and _epic_matches_module(epic, keys)
            and not _epic_requirements(epic)
        ):
            return epic
    return None


def _collect_live_item_ids(fr_content: Any) -> set[str]:
    ids: set[str] = set()
    if not isinstance(fr_content, dict):
        return ids
    for arr_key in ('groups', 'additionalModules'):
        for group in fr_content.get(arr_key) or []:
            if not isinstance(group, dict):
                continue
            for item in group.get('items') or []:
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get('id') or '').strip() or build_item_id(
                    group.get('id'), item.get('name'),
                )
                if item_id:
                    ids.add(item_id)
    return ids


def _collect_flow_keys(epics: list) -> set[str]:
    keys: set[str] = set()
    for epic in epics:
        if not isinstance(epic, dict):
            continue
        for req in _epic_requirements(epic):
            if isinstance(req, dict):
                flow_key = str(req.get('flowKey') or '').strip()
                if flow_key:
                    keys.add(flow_key)
    return keys


def _dedupe_flow_key(base: str, taken: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in taken:
        candidate = f'{base}-{suffix}'
        suffix += 1
    return candidate


def seed_module_technical_requirements(
    technical_content_json: Any,
    sections: list[dict] | None,
    language: str = 'es',
) -> dict[str, Any]:
    """Seed default technical requirements for uncovered catalog modules.

    Pure function (no ORM): takes the technical_document content_json plus the
    proposal's section payloads (``[{'section_type', 'content_json'}]``) and
    returns a deep copy where every visible, non-invite additionalModule that
    has a catalog entry and no epic/requirement of its own gets its default
    epic appended (or an existing empty matching epic filled).

    Seeded rows carry raw ``linked_module_ids`` — callers run
    ``normalize_technical_document_module_links`` right after so the stored
    document uses canonical ``module-<id>`` links and stays selection-gated.
    """
    out = copy.deepcopy(technical_content_json) if isinstance(technical_content_json, dict) else {}
    catalog = MODULE_REQUIREMENTS_CATALOG.get('en' if language == 'en' else 'es') or {}

    fr = next(
        (
            s for s in (sections or [])
            if isinstance(s, dict) and s.get('section_type') == 'functional_requirements'
        ),
        None,
    )
    fr_content = (fr or {}).get('content_json')
    if not isinstance(fr_content, dict):
        return out

    epics = out.get('epics')
    if not isinstance(epics, list):
        epics = []
        out['epics'] = epics

    live_item_ids = _collect_live_item_ids(fr_content)
    taken_flow_keys = _collect_flow_keys(epics)

    for module in fr_content.get('additionalModules') or []:
        if not isinstance(module, dict):
            continue
        module_id = str(module.get('id') or '').strip()
        entry = catalog.get(module_id)
        if not entry:
            continue
        if module.get('is_visible') is False or module.get('is_invite'):
            continue
        keys = _module_match_keys(module_id)
        if _module_covered(epics, keys):
            continue

        seeded = []
        for req in entry['requirements']:
            flow_key = _dedupe_flow_key(req['flowKey'], taken_flow_keys)
            taken_flow_keys.add(flow_key)
            item_id = build_item_id(module_id, req.get('item'))
            seeded.append({
                'flowKey': flow_key,
                'title': req['title'],
                'description': req.get('description', ''),
                'configuration': req.get('configuration', ''),
                'usageFlow': req.get('usageFlow', ''),
                'priority': req.get('priority', 'medium'),
                'linked_module_ids': [module_id],
                'linked_item_ids': [item_id] if item_id in live_item_ids else [],
            })

        target = _matching_empty_epic(epics, keys)
        if target is not None:
            target['requirements'] = seeded
            existing_ids = _norm_id_list(
                target.get('linked_module_ids') or target.get('linkedModuleIds'),
            )
            if not set(existing_ids) & keys:
                target['linked_module_ids'] = existing_ids + [module_id]
        else:
            epics.append({
                'epicKey': _epic_key_for(module_id),
                'title': entry['epic_title'],
                'description': entry.get('epic_description', ''),
                'linked_module_ids': [module_id],
                'requirements': seeded,
            })

    return out
