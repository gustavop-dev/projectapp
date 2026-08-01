# Indicadores de Esfuerzo — Calculadora de Requerimientos (v1.3)

> **Propósito.** Este documento es el corazón del procesamiento de un requerimiento. Mapea señales concretas presentes en la **descripción de un requerimiento** hacia un **nivel de esfuerzo (XS → XL)**, que luego se traduce en horas y precio. No estima proyectos completos: clasifica **funcionalidad por funcionalidad** (o feature por feature); el proyecto es la suma.
>
> Existe por dos razones: (1) dar **consistencia** — que el mismo requerimiento reciba el mismo nivel sin importar quién (o qué IA) lo clasifique — y (2) capturar los **patrones que, por experiencia, escalan** el esfuerzo. Se mantiene deliberadamente general: la meta no es precisión quirúrgica, sino **ubicar rápido dónde encaja mejor** un requerimiento.

**Cómo se lee.** El indicador **más alto** que describe el requerimiento fija su nivel base. Los **modificadores** (al final) ajustan por encima o por debajo. Todo parte de dos supuestos: **desarrollo desde cero** (salvo que la descripción diga que se extiende algo existente) e **implementación web** (la calculadora está calibrada para web; PWA y app móvil nativa son modificadores de plataforma, no señales de nivel).

**Niveles:** `XS` Trivial · `S` Bajo · `M` Medio · `L` Feature completo BE+FE / Medio-alto · `XL` Se parte / Alto. Los puntos (1/2/3/5/8) son un *shorthand* de magnitud para comparar rápido, no entran en ninguna fórmula.

**Regla espejo.** Muchas señales aparecen en varios niveles: la misma palabra sube o baja según si se **construye desde cero** (feature → `L`) o se **agrega sobre lo existente** (adición → `M` o menos), y según **volumen / motor** (→ `XL`). Ver la tabla *Señales espejo* al final.

---

## 🔴 ALTO — nivel base `XL` · 8 pts

> **Definición.** `XL` significa **descomposición obligatoria**: sea porque la descripción mezcla 2+ features, o porque la pieza es estructuralmente tan grande que no se cotiza como un solo ítem. Se parte en requerimientos `S` / `M` / `L` y se cotiza cada uno. Las señales de abajo son los disparadores típicos de esa descomposición.

- **Dinero y datos sensibles** — pagos, transacciones financieras, facturación electrónica (DIAN), open banking / conciliación bancaria directa, o cualquier integración con terceros críticos que maneje datos sensibles (pasarelas, entidades financieras).
- **Cobro recurrente y comercio completo** — suscripciones / facturación recurrente (planes, prorrateo, reintentos de cobro, *dunning*) y checkout e-commerce completo (carrito + pago + órdenes + inventario descontado). El carrito sin pago ronda `L`; el link de pago de pasarela es `L`.
- **Cumplimiento regulatorio de dominio** — facturación electrónica DIAN, nómina / liquidación laboral colombiana (prestaciones, PILA, retenciones), Habeas Data avanzado: normativa con cambios frecuentes que exige mantenimiento continuo.
- **Contabilidad de dominio** — plan de cuentas (PUC), comprobantes y asientos de partida doble, libros auxiliares, balances y cierres de periodo: dominio normado (NIIF/PUC) que exige exactitud y cuadre contable. Casi siempre la respuesta comercial correcta es integrarse o exportar hacia un software contable existente (ver *Exportación contable en formato de tercero*, `M`), no construirla.
- **Flujo multi-etapa con traspaso de responsabilidad entre roles** — **≥3 etapas o ≥2 traspasos** con escalamiento, SLA o notificación por etapa. Una aprobación de un solo paso (solicitante → aprobador) es `M` sobre lo existente o `L` como módulo desde cero; un wizard multi-paso de un solo usuario es `L`. "Turnos" aquí = traspaso de responsabilidad dentro del flujo; el turnero/digiturno de atención es `L` (señal propia). Ver familia *Aprobaciones / flujo*.
- **Motor de PDF complejo** — posicionamiento preciso de múltiples elementos, contenido dinámico inyectado, merge de documentos. Una firma-imagen posicionada en un PDF propio es `L`.
- **Sincronización en tiempo real transversal / edición colaborativa concurrente** — múltiples usuarios sobre el mismo estado o documento (CRDT/OT, cursores compartidos, resolución de conflictos).
- **Arquitectura multiempresa / multi-tenant** — aislamiento de datos, roles y configuración por cliente. Estructural y transversal.
- **Migración masiva / ETL desde legacy** — extraer, mapear, limpiar, validar y reconciliar datos históricos. Por sí sola es un proyecto.
- **Motor de workflow / BPM configurable** — el cliente crea etapas, reglas, responsables, aprobaciones y condicionales.
- **Búsqueda full-text con motor de indexación** (Elasticsearch/OpenSearch) — relevancia, facetas, sinónimos (la facetada "a mano" es `L`).
- **Integración bidireccional con ERP/CRM** (SAP, Salesforce, Siigo, World Office) — sincronización de maestros, colas, reconciliación.
- **Firma digital/electrónica certificada** — PKI, estampado cronológico, validez legal (distinta de "firmar un PDF").
- **Offline-first** — operar sin conexión y sincronizar al reconectar (comparte "resolución de conflictos" con la sync en tiempo real, pero el diferenciador es operar desconectado).
- **Agendamiento / reservas críticas** — es `XL` solo cuando concurren **al menos dos** de: múltiples recursos con solapamiento, pagos y reembolsos, concurrencia real por cupos limitados, zonas horarias. La reserva de citas de **un** recurso sin pago (agenda de un profesional, mesas) es `L` (calendario / agenda base).
- **Mensajería a escala** — orquestación multicanal (SMS/WhatsApp/push con proveedor, reintentos, plantillas por canal, opt-in/out) y/o campañas masivas de correo (listas, segmentación, deliverability, bounces, reputación de dominio). Distinto de *notificar por evento* (`M`) y de *un canal único vía proveedor* (`L`).
- **SSO corporativo / endurecimiento de seguridad empresarial** — SAML, LDAP, Active Directory, MFA, políticas de contraseña, auditoría avanzada, cifrado at-rest transversal, cumplimiento de estándar (OWASP/ISO) verificado.
- **Motor de BI / analítica sobre volumen** — agregaciones, drill-down, series temporales (distinto del dashboard `L` y del reporte parametrizable `M`).
- **Marketplace / plataforma de oferta y demanda** — usuarios, publicaciones, pagos, reputación, mensajes, órdenes, administración.
- **Arquitectura de alto volumen / rendimiento** — cuando el volumen **obliga a cambiar la arquitectura**: colas, caché distribuido, particionado, procesamiento paralelo, millones de registros. Operar sobre datasets grandes *dentro* de la arquitectura actual es el modificador *Volumen alto*.
- **Streaming de video/audio en vivo** — transmisión en directo (WebRTC).
- **Pipeline de video bajo demanda** — upload + transcodificación + almacenamiento + reproducción.
- **API pública para terceros** — versionado, API keys, rate limiting, documentación, sandbox, soporte a integradores externos.
- **Entrenamiento / fine-tuning de un modelo de IA propio** — recolección de datos y ajuste (distinto de *usar* una API de IA, que es `M`–`L`).

_Rondando el borde (raros, normalmente XL):_ Web3 / smart contracts · microservicios (extraer de un monolito) · georreferenciación con rutas y tracking en vivo · integración profunda con hardware físico cuando el dispositivo es el corazón del requerimiento (una integración puntual con impresora/lector es `L` + modificador *Hardware*).

---

## 🟠 MEDIO-ALTO — nivel base `L` · 5 pts · "un feature completo"

> **Definición.** Es `L` cuando hay que construir de forma **integral y desde cero** un feature con **backend y frontend robustos** a la vez: una pieza nueva y autocontenida, no un ajuste sobre algo que ya existe. Si la descripción indica —o al preguntar se confirma— que **la base ya existe** y solo se le agrega algo, **no es `L`: es `M`** (o menor).

- **Renderizado dinámico desde configuración** — formularios o contenido generados desde un esquema o configuración (el usuario final **no** diseña el formulario; si lo diseña, ver constructor).
- **Constructor visual con drag-and-drop desde cero** — *form builder* interno acotado, *page builder*, tablero Kanban (columnas, tarjetas, persistencia del orden). Un motor de formularios configurable como producto (lógica condicional, versionado, publicación) es `XL`. Agregar DnD a una lista existente es `M`.
- **Búsqueda / filtrado avanzado desde cero** — filtros combinados o facetados, autocompletado, paginado y/o preferencias y vistas guardadas por usuario. Con motor de indexación → `XL`; agregar un filtro a un listado existente → `M` o menos.
- **Búsqueda global multi-entidad (omnibox)** — un solo campo que busca sobre varias entidades del sistema con resultados agrupados (con motor de indexación → `XL`).
- **Trazabilidad de historial / auditoría / bitácora de eventos** — construir el registro de quién hizo qué y cuándo: eventos de creación, edición y eliminación sobre uno o varios modelos, con su vista de consulta. Solo *mostrar* logs ya guardados es `M`; extender una bitácora existente a otro modelo es el atenuador (`M` o menos); auditoría avanzada con exigencia de cumplimiento → `XL` (seguridad empresarial).
- **Numeración consecutiva sin huecos con garantía de concurrencia** — consecutivos legales o de facturación que no pueden duplicarse ni saltarse. Un ID único simple (UUID, slug) es `XS`–`S`.
- **Múltiples CRUD relacionados** entre sí / **panel de administración de entidades** (CRUD + permisos + búsqueda sobre varios modelos).
- **Autenticación / registro completo desde cero** — login, signup, verificación de correo, recuperación, sesiones. Piezas sueltas sobre auth existente (OAuth social, recuperación) son `M`; 2FA/MFA es `L`; SSO corporativo es `XL`.
- **Panel de administración de usuarios y roles (RBAC granular)** — crear roles y asignar permisos por vista o por acción.
- **Dashboard / panel de KPIs desde cero** — widgets, gráficas, agregaciones, rangos de fecha.
- **Visualización interactiva compleja a medida** — Gantt, organigrama, árbol jerárquico editable, mapa de procesos con edición/drag. Integrar un componente de terceros que ya lo hace es `M`.
- **Importación masiva con validaciones** — parseo + validación + *preview* + commit + errores fila por fila + progreso. La importación trivial sin validación baja a `M`.
- **Constructor de reportes/consultas por el usuario** — el usuario arma reportes dinámicos (no solo "generar un PDF").
- **Centro / bandeja de notificaciones in-app** — leído/no leído, agrupación, preferencias, tiempo real (distinto de *notificar por evento*, que es `M`).
- **Gestor documental** — cargar, clasificar, consultar, descargar, con permisos, categorías y estados.
- **Centro de plantillas de documentos administrable** — el usuario crea y edita las plantillas (contratos, certificados, correos) con variables. Generar documentos desde una plantilla **fija** es `M`.
- **Calendario / agenda base** — vistas mensual/semanal, eventos, plantilla de disponibilidad con excepciones, recordatorios; incluye la reserva de citas de **un** recurso sin pago (→ `XL` si se vuelve scheduling multi-recurso con concurrencia y pagos).
- **Inventario básico desde cero** — productos, entradas/salidas, existencias, alertas, movimientos.
- **Geolocalización / mapas** — pines, clustering, rutas, polígonos (Google Maps/Mapbox); tracking en vivo → `XL`.
- **Panel de configuración / parametrización del sistema** — variables de negocio, reglas y textos administrables desde la UI.
- **Sistema de comentarios / hilos / anotaciones** — con menciones, adjuntos ligeros y notificación.
- **Chat / mensajería en tiempo real propio** — 1:1 o grupos, historial persistente, presencia. Embeber un widget de chat de terceros (Chatwoot, Tawk) es `M` (componente de terceros).
- **Gestión de etiquetas/taxonomías o de reseñas como feature completo** — agregar un rating a una entidad existente es `M`.
- **Onboarding / wizard multi-paso** con persistencia de progreso (de un solo usuario; con traspaso entre roles → `XL`).
- **Integración con un servicio / API externo (piso)** — toda integración de **datos con backend de terceros autenticada** es **al menos `L`** (incluye el link de pago de pasarela y la generación de guías con transportadoras — Servientrega, Coordinadora, Envía; multi-transportadora con reglas de selección o tracking en vivo → `XL`); sube a `XL` con pagos recurrentes/checkout, facturación, datos sensibles o bidireccionalidad. Excepciones que conservan su nivel: webhook saliente (`M`), componente FE de terceros (`M`), script/pixel (`S`).
- **Canal único de mensajería vía proveedor** — WhatsApp Business API, SMS o push con un proveedor: setup, plantillas aprobadas, envío y estados. Multicanal orquestado → `XL`.
- **Funcionalidad basada en IA / resoluble con IA** — piso `M`, típicamente `L`; **antes de dar precio**, validar alcance y factibilidad. Modelo propio / fine-tuning → `XL`.
- **OCR / extracción de datos desde documentos** — facturas, cédulas, PDFs escaneados: captura + parsing + corrección manual del resultado.
- **Chatbot / asistente con IA sobre datos propios (RAG)** — ingesta de documentos, embeddings, recuperación, UI de conversación (→ `XL` si exige fine-tuning o volumen).
- **Motor de cotizaciones / precios / descuentos / comisiones** — reglas de cálculo de negocio configurables que producen un valor (→ `XL` si el cliente arma las reglas como un BPM). Un cupón/código simple o una lista de precios por cliente es `M`; el motor es `L` cuando las reglas son combinables o configurables.
- **Constructor de encuestas / formularios públicos con resultados** — crear encuesta + responder público + resultados agregados (una encuesta fija simple es `M`).
- **CMS / portal público administrable** — blog, landing o sitio con contenido editable desde el panel (una página estática es `S`; una landing sin CMS es `M`).
- **Catálogo público con pedido por WhatsApp** — catálogo + carrito sin pasarela + deep link `wa.me` con el pedido armado (con pago en línea → `XL` comercio completo).
- **Gamificación** — puntos, niveles, insignias, ranking, reglas de otorgamiento.
- **Estructura organizacional** — sedes, sucursales, equipos, jerarquías con datos y permisos por nodo.
- **Recepción y parseo de correo entrante** — recibir emails hacia la app (inbound), extraer datos, adjuntos, responder.
- **Galería / biblioteca multimedia con procesamiento** — colecciones, miniaturas, orden, metadatos (subir una imagen a una entidad es `M`).
- **Portal de autoservicio del cliente final** — vista externa limitada donde el cliente consulta sus propios datos/documentos/estados (hereda auth y permisos). Si la autenticación de clientes ya existe y es una sola vista de datos propios, baja a `M` (atenuador *extiende algo existente*); el portal completo desde cero es `L`.

- **Módulo de tickets / PQRS / mesa de ayuda** — radicación (interna o formulario público) con número de caso, asignación a un responsable, estados, respuestas en hilo y notificación al solicitante. Con SLA, escalamiento automático o traspaso configurable entre áreas → `XL`.
- **Pipeline de documentos comerciales** — cadena cotización → orden/pedido → remisión → factura o cuenta de cobro, con conversión entre documentos (heredando ítems y totales), numeración y estados por documento. Cada documento suelto es `M`; el pipeline encadenado es `L`; con pago en línea o facturación DIAN → `XL`.
- **Turnero / gestión de filas (digiturno)** — tomar turno (kiosco, QR o recepción), tablero de llamado con actualización en vivo, módulos/ventanillas de atención y estadísticas básicas de espera. Con priorización configurable, múltiples sedes o integración con pantallas físicas → suma modificadores o `XL`.
- **Módulo de caja** — apertura y cierre de turno de caja, registro de ingresos/egresos, arqueo con conteo y detección de descuadre por responsable.
- **Analítica de comportamiento con panel propio** — tracking de eventos + agregaciones + panel de uso (sesiones, rutas más visitadas, tiempos, embudos simples). El tracking básico sin panel es `M`; sobre gran volumen o con series temporales complejas → `XL` (motor de BI).
- **Motor de emparejamiento / matching entre dos conjuntos** — personas↔personas, personas↔publicaciones, demanda↔oferta, con criterios ponderados, sugerencias y opcionalmente mutualidad (ambas partes aceptan para conectar). Un listado "recomendados" que solo aplica filtros sobre una búsqueda existente es `M`; con colas en tiempo real, escala o modelo aprendido → `XL`.
- **Seguimiento de progreso con desbloqueo secuencial** — avance sobre una secuencia de contenidos o requisitos: unidades completadas, prerequisitos que desbloquean lo siguiente, reanudar donde se quedó, evento "completado" que dispara acciones. Un simple % de completitud calculado sobre campos llenos es `M` (campos calculados).
- **Credenciales / comprobantes verificables** — emisión automática al cumplirse una condición (completar curso, pagar entrada, aprobar verificación) con código/QR único, verificación pública y ciclo de estados (válido / usado / vencido / revocado). Generar el PDF desde plantilla fija es `M`; con venta → `XL` (comercio); con control de acceso físico → modificador *Hardware*.
- **Lista de espera con promoción automática** — cola ordenada (o priorizada) cuando el cupo/stock está lleno; al liberarse un lugar se ofrece al siguiente con ventana de aceptación que expira y pasa el turno. Un "avísame cuando haya disponibilidad" que solo notifica sin reservar turno es `M`.
- **Re-enganche automático por abandono** — detectar un flujo iniciado y no terminado (carrito, solicitud, reserva, registro) o inactividad, con secuencia programada de 2–3 recordatorios, enlace de reanudación al punto exacto y supresión al completar. Un recordatorio único por evento es `M`; con orquestación multicanal → `XL` (mensajería a escala).
- **Moderación de contenido generado por usuarios (UGC)** — reportar/denunciar con motivos, bandeja de revisión, acciones (aprobar / ocultar / eliminar) y sanciones acumulativas al autor (strikes, suspensión). Distinto del maker-checker (aprobación de operaciones internas): aquí dispara la denuncia del público y hay régimen de sanciones. Un botón "reportar" que solo crea un registro visible al admin es `M`; con IA o escalamiento entre roles → `XL`.
- **Billetera / ledger de saldo y créditos internos** — cuenta por usuario con saldo, movimientos inmutables (abonos/cargos con concepto), atomicidad en el débito y extracto — créditos, puntos canjeables, horas, tokens de uso; **sin dinero real**. Con recargas por pasarela o retiros/payouts → `XL` (dinero y datos sensibles). ≠ puntos de gamificación (premian, no se gastan como medio de pago).
- **Límites y features por plan (feature gating / entitlements)** — planes con límites cuantitativos (N usuarios, N registros, X GB), medición del consumo, bloqueo o aviso al alcanzar el límite y llamados a upgrade. No incluye el cobro (suscripciones → `XL`). Gatear features con un booleano por plan es `M` (como permisos por rol). Tiende a sumar el multiplicador *Transversal*.
- **Asignación / despacho de tareas o pedidos (dispatch)** — distribuir unidades de trabajo (pedidos, citas, leads, casos) entre un pool de responsables con reglas — round-robin, carga, zona, habilidad — más aceptar/rechazar, reasignación y notificación. Un campo "asignado a" manual con notificación es `M`; despacho automático en tiempo real con geolocalización y rutas → `XL`.
- **Oferta / contraoferta entre dos partes (negociación)** — una parte ofrece, la otra acepta, rechaza o contraoferta; historial del hilo, expiración y notificación por movimiento. ≠ pipeline de documentos comerciales (ahí emite la empresa; aquí negocian dos usuarios). Una oferta simple sin réplica es `M`; subasta con pujas en tiempo real → `XL`.
- **Corte y liquidación periódica a contrapartes** — cierre de periodo que congela las transacciones incluidas, cálculo del neto (usa el motor de comisiones si existe), estado de cuenta y estados pagado/pendiente/en disputa (vendedores, repartidores, comisionistas, propietarios). La dispersión real del dinero es `XL` (pagos); la nómina es `XL` regulatorio.

_Rondando el borde:_ carrito de compras sin pago · feed/timeline de actividad · invitaciones/referidos · web scraping/crawling (proxies, CAPTCHAs).

---

## 🟡 MEDIO — nivel base `M` · 3 pts

> **Definición.** Funcionalidad **acotada**: no exige el feature completo BE+FE de un `L`. Suele ser una **adición o ajuste sobre una base que ya existe** o una pieza pequeña construida desde cero. Es donde cae la mayoría del trabajo real del día a día.

- **CRUD de una entidad con extras acotados** — validaciones, permisos básicos, búsqueda. Varios CRUD relacionados entre sí → `L`.
- **Combo de listado server-side** — paginación + ordenamiento + búsqueda (o scroll infinito) manteniendo los filtros. Es lo que casi todo CRUD termina pidiendo.
- **Acciones masivas / bulk** — seleccionar N registros y aplicar (eliminar, cambiar estado, exportar, asignar).
- **Generación de reportes / archivos** (Excel, PDF) — desde básicos hasta **parametrizables** (filtros/rangos) o **programados** (cron → suma *Tarea programada*). Incluye exportación simple desde una vista existente y "descargar mis datos" (portabilidad, Habeas Data).
- **Soft delete / papelera / restauración** — borrado lógico + vista de eliminados + restaurar.
- **Permisos / visibilidad por rol** — reglas de qué ve o hace cada rol, incluyendo mostrar u ocultar contenido según rol. Ocultar **un** elemento por rol es `XS`; panel RBAC granular es `L`.
- **Lógica condicional** en formularios.
- **Validaciones de negocio complejas** — cross-field, contra el backend, con reglas (distintas de las validaciones básicas `XS`).
- **Campos calculados / derivados** — totales, subtotales, impuestos, saldos, vencidos que se recalculan.
- **Carga de imágenes / archivos con procesamiento** y **adjuntar archivos a una entidad existente**.
- **Clonar / duplicar una entidad con sus relaciones** (más que duplicar un documento, que es `S`).
- **Versionado ligero / snapshots** con reversión a una versión previa.
- **Autoguardado / borradores (drafts).**
- **Preferencias de usuario / de app** — columnas visibles, orden, vista o tema preferido; aplican en runtime.
- **Documento o correo con maquetación / branding** — membretes, tipografías, identidad corporativa, marcas de agua ligeras. Incluye generar contratos, certificados o actas desde una **plantilla fija** con variables (centro de plantillas administrable → `L`; motor de PDF complejo → `XL`).
- **Cuenta de cobro / factura simple no-DIAN en PDF** — documento de cobro con numeración y branding, sin facturación electrónica. La facturación electrónica DIAN es `XL` (regulatorio). Su numeración asume secuencia simple; si exigen consecutivo legal sin huecos bajo concurrencia, esa pieza sube a `L`.
- **Notificaciones por evento** (in-app o correo) — detectar el evento, plantilla, envío. Periódica o resumen (digest) → suma *Tarea programada*.
- **Máquina de estados / cambios de estado** — transiciones y reglas sobre un registro (→ `L` si hay acciones/permisos por estado o varios actores). Cambiar el estado de un **conjunto** de registros a la vez es *Acciones masivas / bulk* (`M`); mostrar el estado es badge (`S`).
- **Mostrar historial ya registrado** — si los logs ya se guardan y solo hay que exponerlos (construir la trazabilidad es `L`).
- **Integrar un componente de terceros en el FE** — mapa embebido, editor WYSIWYG, date-range picker, tabla avanzada, reCAPTCHA, recorte de imagen, widget de chat (Chatwoot/Tawk).
- **Webhook saliente simple** — enviar un payload a un tercero cuando ocurre un evento.
- **Login social (OAuth) o recuperación de contraseña** sobre una autenticación que ya existe.
- **Importación simple** sin motor avanzado de validación o conciliación.
- **Tema claro / oscuro (theming)** — ligero pero **transversal**.
- **Configurar / parametrizar una regla de negocio antes fija en el código** — UI para administrarla (→ `L` si es un panel de configuración completo).
- **Generalizar una operación (crear/editar/eliminar) del caso base a N casos o modelos** — creación en cascada (→ `L` si obliga a un motor completo).
- **Multidioma (i18n)** — construir la capacidad; **transversal**. Entregar un feature en 2 idiomas sobre i18n ya existente es el modificador *Entregable bilingüe*.
- **Firma dibujada en canvas / aceptación en pantalla** — trazo sobre canvas o botón "acepto" con evidencia (≠ firma-imagen posicionada en PDF `L`, ≠ certificada `XL`).
- **Generación / lectura de códigos QR o de barras** — generar el código es simple; escanear con cámara sube dentro de `M` o a `L` según el flujo.
- **Actualización en vivo de una vista puntual** — polling o un websocket acotado para refrescar un dato (≠ *sincronización en tiempo real transversal*, `XL`).
- **Multi-moneda / conversión de divisas** — mostrar y calcular montos en más de una moneda con tasa administrable.
- **Vencimientos / renovaciones con alertas** — fechas de expiración de contratos, membresías o documentos + recordatorio (suma *Tarea programada*).
- **Términos y condiciones con aceptación versionada / consentimientos** — registrar quién aceptó qué versión y cuándo (Habeas Data básico).
- **Sesiones activas / cierre remoto / bloqueo por inactividad** — listar dispositivos, cerrar sesión a distancia, timeout.
- **Impersonación ("ingresar como usuario") para admins** — con evidencia de auditoría y salida segura.
- **Rate limiting / anti-abuso / captcha** en formularios o endpoints públicos.
- **Cifrado de campos sensibles / anonimización puntual** — proteger columnas específicas (≠ endurecimiento de seguridad empresarial, `XL`).
- **Landing / página de marketing multi-sección con formulario** — página nueva con varias secciones y captura de contacto, sin CMS (página estática simple = `S`; administrable = `L`).
- **Cotizador / calculadora pública embebida con captura de lead** — con reglas de cálculo simples fijas (con motor de reglas configurable → `L`).
- **Tarea técnica no funcional pedida como requerimiento** — actualizar framework, migrar hosting, SSL/dominio, optimización puntual: se clasifica y cotiza aparte del roadmap funcional.

- **Aprobación de un paso (maker-checker)** — un usuario registra o solicita y otro aprueba/rechaza antes de que surta efecto: estado pendiente, notificación al aprobador y evidencia de quién aprobó (→ `L` si el módulo de solicitudes se construye desde cero; → `XL` con ≥3 etapas, escalamiento o reglas configurables).
- **Cupones / códigos de descuento simples** — código con porcentaje o valor fijo, vigencia, límite de usos y validación al aplicar. Reglas combinables o configurables por el cliente (motor) → `L`.
- **Exportación contable en formato de tercero** — archivo plano o Excel con la estructura exigida por un software contable (Siigo, World Office, contador), con homologación parametrizable de cuentas, terceros e impuestos (→ `L` si la homologación exige un panel de parametrización completo; la integración por API con el ERP es `XL`).
- **Listas de precios / precio especial por cliente o segmento** — asignar precios diferenciados sobre un catálogo existente, con vigencia y precio por defecto. Reglas de cálculo configurables (volumen, combinaciones) → motor `L`.
- **Tracking de uso / telemetría propia básica** — registrar eventos de navegación o acciones del usuario (endpoints visitados, vistas, tiempos) vía middleware o eventos, con consulta simple de los datos. Con panel de análisis propio → `L`; con script de terceros (GA/Hotjar) es `S`. Ojo Habeas Data: puede requerir consentimiento (ver *T&C / consentimientos*).
- **Comparador de ítems lado a lado** — seleccionar N ítems de un catálogo existente y verlos en tabla comparativa de atributos, con persistencia de la selección. Si los atributos comparables los configura el admin o se comparan entidades heterogéneas → `L`.
- **Texto sugerido automáticamente por el sistema, editable por el usuario** — el sistema propone un texto a partir de datos ya registrados (movimientos, historial, plantillas de contexto) y el usuario lo complementa o sobrescribe antes de persistir: observaciones, descripciones, respuestas precargadas. Si la sugerencia la produce una IA → señal *Funcionalidad basada en IA* (`M`–`L`).
- **Bloqueo/reserva exclusiva de un registro por usuario** — al iniciar el trabajo, el registro queda reservado a quien lo tomó y un segundo usuario recibe el mensaje de bloqueo (lock con `select_for_update` o equivalente). Suele sumar el modificador *Concurrencia / atomicidad*; la liberación por timeout/vencimiento se cotiza con su *Tarea programada*. ≠ edición colaborativa concurrente sobre el mismo estado (→ `XL` sincronización en tiempo real).

_Rondando el borde:_ favoritos/guardados · recordatorios/snooze · manejo de zona horaria/locale.

---

## 🟢 BAJO-MEDIO — nivel base `S` · 2 pts

> **Definición.** Cambio **visible para el usuario pero de alcance reducido**: interacción de UI o feedback puntual, sin tocar el modelo de datos ni la lógica de negocio.

- Cambios de **estilo (UI) o de plantilla** / ajustes menores a tarjetas, tablas, botones o formularios.
- **Diálogo de confirmación** (antes de una acción destructiva).
- **Toast / alerta efímera** de éxito, error o advertencia.
- **Operaciones client-side sobre datos ya cargados** — búsqueda, filtro, orden y/o paginación (incl. *typeahead* sobre un endpoint existente).
- **Badge / chip de estado** — mostrar el estado visualmente (sin la máquina de estados `M`).
- **Copiar al portapapeles / compartir enlace.**
- **Descarga de archivo estático** / enlace de descarga (sin generación dinámica).
- **Tabs / acordeón / secciones colapsables** — reorganizar una vista existente.
- **Estados de carga** — spinner, skeleton o empty state.
- **Formato condicional visual** — colorear filas/celdas/valores según una regla simple.
- **Tooltip / ayuda contextual.**
- **Modales / popups.**
- **Validación regex específica** en un campo (password, placa, formato).
- **Imprimir una vista** — *print stylesheet* / `window.print`.
- **Página estática** — términos, ayuda, política, información (sin CMS).
- **Plantillas de correo básicas** (texto plano).
- **Duplicación de documentos.**
- **Contador / temporizador en UI** — countdown, cronómetro, o indicador de frescura ("última actualización hace X").
- **Script de terceros simple** — pixel, Hotjar, Google Analytics.
- **Ajuste responsive puntual** de una sección (el responsive completo es un modificador).
- **Meta tags / Open Graph / favicon por página** — configurar títulos, descripciones e imagen de compartir (reemplazar el asset del logo/favicon es `XS`).
- **Animaciones / micro-interacciones puntuales** — transiciones, hover, feedback visual.
- **Deep link con restauración de estado** — abrir una vista en una pestaña/sección/filtro específico vía URL (query params → estado). El ancla o enlace simple es `XS`.
- **Retiro controlado de un comportamiento ya entregado** — eliminar un endpoint/acción y su UI, reescribiendo las pruebas que lo cubrían (≠ ocultar un elemento existente, `XS`; sube a `M` si exige decidir o archivar datos históricos del comportamiento retirado).

_Rondando el borde:_ breadcrumbs · contador de caracteres/límites en input.

---

## ⚪ BAJO — nivel base `XS` · 1 pt

> **Definición.** Cambio **puntual y aislado** que no toca estructura, modelo de datos, flujo, permisos amplios ni lógica de negocio.

- **Cambio de copy** — texto, etiqueta, título, placeholder, mensaje de validación o typo (sin lógica). Incluye actualizar el contenido de una página estática existente (p. ej., textos legales).
- **Cambio visual puntual** — color, ícono, logo/favicon/imagen de marca (reemplazo del asset, sin rediseño), imagen estática, espaciado, tamaño, variable CSS / theming menor.
- **Cambiar el valor por defecto** de un campo.
- **Marcar un campo requerido/opcional** o cambiar un límite (maxlength/rango) · validación básica.
- **Agregar / quitar una opción estática** a un select o enum existente.
- **Ocultar / mostrar un elemento existente** (por rol o condición simple).
- Agregar un **checkbox/toggle** o un **enlace simple** / cambiar una ruta, redirección o ancla.
- **Ajustar un permiso puntual** — dar acceso de una vista a un rol.
- **Cambiar formato de visualización** — fecha, moneda, número — o el orden por defecto.
- **Reordenar campos o columnas** / cambiar el criterio de un filtro fijo.
- **Activar / desactivar** un feature flag o configuración ya construida.
- **Actualizar una variable de entorno** / API key / URL (staging → producción).

---

## Modificadores y reglas de ajuste

No definen el nivel por sí solos: lo **ajustan**. Fórmula de aplicación (ver detalle en `market-pricing.md`):

`horas = base × (1 + Σ% aditivos) × factor transversal + horas fijas (cron)` · si aplica app nativa: `× 1,6` **al final**.

### Estructurales

| Modificador | Efecto |
|---|---|
| Pantalla nueva (frontend que hoy no existe) — **solo aplica a `XS`–`M`**: un `L` ya la incluye por definición | `+15–25%` |
| Modelo de datos / migraciones (tablas, campos, relaciones) — **solo aplica a `XS`–`M`**: un `L` ya lo incluye | `+10–20%` |
| Transversal (toca muchas pantallas o documentos) — **multiplicador**, no aditivo | `×1,4–1,8` |
| Motor nuevo (PDF de reportes, plantillas de correo, etiquetas) | `+30–80%` (o `+1 nivel` si es pesado) |
| Concurrencia / atomicidad (bloqueos, stock atómico) | `+20–40%` |
| Tarea programada / cron (Huey) — **horas fijas**, se suman al final | `+8–16 h` |

### Plataforma (excluyentes entre sí; web = default sin recargo)

| Modificador | Efecto |
|---|---|
| Aplica también a la PWA contratada | `+30%` |
| Implementación como app móvil nativa (iOS/Android + tiendas) — se aplica `×1,6` al final, sobre el resultado ya modificado; la primera publicación en tiendas (cuentas, firma, revisión) puede cotizarse como ítem de *Despliegue/operación* | `+60%` |

### Costo y riesgo

| Modificador | Efecto |
|---|---|
| Diseño UI/UX **no** entregado por el cliente | `+15–30%` |
| Responsive completo (móvil + tablet + desktop) | `+15–35%` |
| Permisos por campo o por acción (granular, sobre algo existente) | `+20–40%` |
| Carga inicial / *backfill* de datos al desplegar (≠ crear el modelo nuevo) | `+10–30%` |
| Volumen alto de datos — el volumen se maneja **dentro** de la arquitectura actual (índices, paginación obligatoria, queries pesadas); si obliga a **cambiar** la arquitectura → señal `XL` | `+20–50%` |
| Pruebas con múltiples roles | `+10–25%` |
| Observabilidad / logging de errores exigido | `+10–20%` |
| Tests automatizados / cobertura mínima exigida | `+10–25%` |
| Código legacy sin tests / deuda técnica | `+15–40%` |
| Dependencia de tercero externo (mal documentado o sandbox inestable) | `+15–40%` |
| Despliegue / operación en producción (dominios, correos, variables, backups, CI/CD, monitoreo, colas nuevas) | `+10–30%` o ítem aparte |
| Accesibilidad (WCAG) o SEO/SSR como requisito explícito | `+20–50%` (refactor total de la plataforma = `XL`) |
| Datos semilla / fake data para demo o capacitación | `+5–10%` (o ítem aparte si es un dataset grande) |
| Documentación / manual de usuario exigido como entregable | `+10–20%` |
| Capacitación / acompañamiento exigido | ítem aparte |
| Hardware o pruebas en sitio (dispositivos físicos, visitas) | `+25–60%` (+ visitas como ítem aparte) |
| Urgencia / entrega exprés exigida (cronograma comprimido) | `+20–50%` |
| Coordinación con equipo/proveedor del cliente (comités, dependencia de su TI, reuniones recurrentes) | `+10–25%` |
| Entregable bilingüe (ES/EN) sobre i18n ya existente (construir i18n desde cero es la señal `M` transversal) | `+5–15%` |

### Atenuador

| Modificador | Efecto |
|---|---|
| **Extiende algo ya existente** — agregar un filtro, una columna, un drag-and-drop o una opción a algo que ya existe | Baja el nivel: como **no** se construye el feature completo, **rara vez es `L`** → suele quedar en `M` o menos. Rompe el supuesto "desde cero"; **debe estar declarado** (si no, preguntar). |

### Condiciones de bloqueo (no son porcentaje)

- **Requerimiento ambiguo o con reglas sin definir** → **no cerrar precio fijo** hasta aclarar. Es una decisión comercial, no un ajuste de tamaño.
- **Bloqueo externo** → depende de que el cliente o un tercero entregue credenciales, accesos o datos. Afecta el cronograma, no el tamaño.

---

## Señales espejo (misma palabra, distinto nivel)

El diferenciador es *desde cero vs. sobre lo existente* y *volumen / motor*.

| Familia | `XS`–`S` | `M` | `L` | `XL` |
|---|---|---|---|---|
| Búsqueda | client-side sobre datos cargados | server-side en un listado | facetada con autocompletado / global multi-entidad | full-text con indexación |
| Importación | — | simple sin validación | masiva con validaciones | migración / ETL desde legacy |
| Notificaciones | toast efímero | por evento (in-app/correo) | centro in-app / canal único vía proveedor | mensajería a escala (multicanal, campañas) |
| Datos / visualización | badge de estado | métricas o reporte parametrizable | dashboard / visualización interactiva a medida | motor de BI sobre volumen |
| Autenticación | — | OAuth / recuperación sobre lo existente | módulo completo o 2FA/MFA | SSO corporativo |
| Permisos | ajuste puntual (XS) | permisos / visibilidad por rol | panel RBAC granular | seguridad empresarial |
| Documentos | descarga estática | adjuntar a una entidad / plantilla fija con variables | gestor documental / centro de plantillas | firma certificada / motor de PDF complejo |
| Facturación / contabilidad | — | cuenta de cobro / factura simple PDF · exportación contable formato tercero | pipeline de documentos comerciales | facturación electrónica DIAN / contabilidad de dominio |
| Duplicar | duplicar un documento (S) | clonar entidad con relaciones | — | — |
| Drag-and-drop | — | agregar DnD a una lista existente | constructor / Kanban desde cero | motor de formularios como producto |
| Validación | requerido/límite (XS), regex (S) | de negocio (cross-field) | — | cumplimiento regulatorio |
| Geo / mapas | — | — | mapa con pines y rutas | tracking en vivo / georreferenciación |
| Tiempo real | refresco manual / botón actualizar | polling o websocket en una vista | chat o feed en vivo propio | sincronización transversal / colaborativa |
| Firma | — | dibujada en canvas / aceptación | firma-imagen posicionada en un PDF propio | certificada PKI / validez legal |
| Pagos | — | — | link de pago de pasarela | checkout completo / suscripciones |
| Correo | plantilla básica texto plano | con branding / por evento / plantilla fija | centro de plantillas administrable | campañas masivas / deliverability |
| IA | — | llamada a API con prompt fijo | feature con IA + UI (RAG típico) | fine-tuning / modelo propio |
| Plataforma | responsive puntual (S) | responsive completo (mod +15–35%) | PWA (mod +30%) | app nativa (mod +60%) — *toda la fila son modificadores; el nivel lo da la funcionalidad* |
| Media / archivos | descarga estática | upload con procesamiento | galería / gestor multimedia | pipeline de video / streaming en vivo |
| Encuestas / formularios | — | encuesta fija simple | constructor de encuestas / form builder interno | motor de formularios como producto |
| Auditoría / eventos | — | mostrar historial ya registrado | construir bitácora/auditoría (quién, qué, cuándo) | auditoría avanzada con cumplimiento (seguridad empresarial) |
| Analítica de uso | script de terceros (GA/pixel) | tracking/telemetría propia básica | analítica de comportamiento con panel propio | motor de BI sobre volumen |
| Aprobaciones / flujo | — | maker-checker sobre lo existente | módulo de solicitudes desde cero / tickets-PQRS | ≥3 etapas con escalamiento/SLA / workflow configurable (BPM) |
| Agendamiento / reservas | — | vencimientos / recordatorios con alertas | agenda base / cita de un recurso sin pago | scheduling multi-recurso con concurrencia y pagos |
| Precios / descuentos | cambiar un precio o % fijo (XS) | cupón simple / lista de precios por cliente / parametrizar regla fija | motor de reglas de precios / comisiones | el cliente configura reglas como BPM |
| Integraciones | script / pixel (S) | webhook saliente / componente FE de terceros | API de datos autenticada / canal único de mensajería / link de pago | ERP-CRM bidireccional / pagos recurrentes / datos sensibles / API pública propia |
| Inventario / stock | — | campo de stock + alerta de mínimos sobre lo existente | inventario básico desde cero | checkout con stock descontado / alto volumen con concurrencia |
| Matching | — | "sugeridos" por filtros fijos sobre búsqueda existente | motor de emparejamiento con criterios y mutualidad | matching en tiempo real a escala / con modelo propio |
| Espera / cupo | — | "avísame cuando haya disponibilidad" (alerta pasiva) | lista de espera con promoción automática y ventana | reservas críticas con pagos y concurrencia |
| Créditos / saldo | — | contador simple decrementable sin historial | billetera / ledger con extracto y atomicidad | recargas / retiros de dinero real |
| Asignación | — | "asignado a" manual con notificación | dispatch con reglas y aceptar/rechazar | despacho en tiempo real con tracking / rutas |
| Negociación | — | oferta simple sin réplica | oferta / contraoferta con expiración | subasta con pujas en tiempo real |
| Estados | badge / chip de estado | máquina de estados de un registro / cambio masivo (bulk) | acciones y permisos por estado o varios actores | flujo multi-etapa ≥3 / workflow configurable (BPM) |

_Ejemplo componible (no señal propia): "alertas por búsqueda guardada" = búsqueda avanzada con vistas guardadas (`L`) + notificación por evento (`M`) + modificador *Tarea programada*._

---

## Notas de clasificación

- **`M` vs `L` — la pregunta clave.** `L` = construir un **feature completo BE+FE desde cero**, integral y autocontenido. `M` = **agregar o ajustar sobre algo que ya existe**, o una pieza que no llega a feature completo. Ante la duda de si la base existe, **preguntar**: si no existe, primero hay que construirla (eso sí es `L`) y el ajuste viene después.
- **`XL` = descomposición obligatoria.** Sea por mezcla de features o por tamaño estructural, nunca se cotiza entero: se descompone en requerimientos `S` / `M` / `L` y cada uno se cotiza.
- **Web por defecto.** Toda estimación asume implementación web. PWA (`+30%`) y app nativa (`+60%`) son modificadores de plataforma excluyentes entre sí; el nivel de la funcionalidad no cambia.
- **Personalización = escalón, no salto.** Volver configurable algo fijo en código suele quedar en `M`; solo es `L` si el espacio de configuración es en sí un feature completo.
- **Generalización = escalón.** "Que funcione para todos los casos, no solo el base" tiende a `M`; pasa a `L` cuando obliga a construir un **motor** (ver *Motor nuevo*).
- **Integraciones: piso `L` con excepciones nombradas.** Toda integración de datos con backend de terceros autenticada es al menos `L`; el piso sube según autenticación, volumen, bidireccionalidad y criticidad del dato. Webhook saliente (`M`), componente FE (`M`) y script/pixel (`S`) conservan su nivel.
- **IA: primero alcance, luego precio.** Piso `M`, tiende a `L`; modelo propio o fine-tuning es `XL`.
- **"Factura" ≠ facturación electrónica.** Una cuenta de cobro o factura simple en PDF es `M`; solo la facturación electrónica DIAN dispara el `XL` regulatorio. Preguntar cuál es antes de clasificar.
- **Presentación con marca.** Un PDF o correo deja de ser básico (`S`) apenas pide membrete o identidad → `M`; solo llega a `XL` con posicionamiento preciso múltiple o contenido dinámico complejo.
- **Operación en producción no es gratis.** Despliegue, dominios, correos, backups, ambientes y monitoreo se cobran como modificador o ítem aparte.
- **Lo técnico también se cotiza.** Upgrades de framework, migraciones de hosting y optimizaciones son requerimientos por derecho propio (`M`–`L` según alcance), no favores implícitos.
- **Hardware = riesgo físico.** Cualquier dispositivo físico agrega pruebas en sitio, drivers y variables fuera del control del software: nunca subestimarlo.

---

## Qué cambió en esta versión (v1.3 — simulación de mercado + patrones por arquetipo)

**Correcciones a señales que sobre-disparaban (6):** `XL` *Flujo multi-etapa* ahora exige **≥3 etapas o ≥2 traspasos** (una aprobación de un paso ya no es XL — era el falso positivo más costoso) · `XL` *Agendamiento/reservas críticas* exige **al menos dos** condiciones concurrentes (la cita de un recurso sin pago es `L`) · notas de desempate en *Motor de cotizaciones* (cupón/lista de precios = `M`), *Cuenta de cobro* (consecutivo legal = `L`), *Portal de autoservicio* (una vista sobre auth existente = `M`) y "turnos" (flujo ≠ turnero).

**Señales del dueño (auditoría de eventos y uso):** `L` *Trazabilidad/auditoría* refinada — nombra explícitamente la bitácora de eventos de creación/edición/eliminación sobre uno o varios modelos · **nuevas** `M` *Tracking de uso / telemetría propia básica* y `L` *Analítica de comportamiento con panel propio*.

**Señales nuevas por simulación de mercado (9):** maker-checker (`M`) · tickets/PQRS (`L`) · pipeline de documentos comerciales (`L`) · cupones simples (`M`) · exportación contable formato tercero (`M`) · turnero/digiturno (`L`) · listas de precios por cliente (`M`) · contabilidad de dominio (`XL`) · módulo de caja (`L`).

**Patrones generalizados por arquetipo (12):** matching entre dos conjuntos (`L`) · progreso con desbloqueo secuencial (`L`) · credenciales verificables (`L`) · lista de espera con promoción automática (`L`) · re-enganche por abandono (`L`) · comparador de ítems (`M`) · moderación UGC (`L`) · billetera/ledger interno (`L`) · feature gating por plan (`L`) · dispatch/asignación con reglas (`L`) · oferta/contraoferta (`L`) · corte y liquidación a contrapartes (`L`).

**Señales espejo:** 13 filas nuevas (Auditoría/eventos, Analítica de uso, Aprobaciones/flujo, Agendamiento/reservas, Precios/descuentos, Integraciones, Inventario/stock, Matching, Espera/cupo, Créditos/saldo, Asignación, Negociación, Estados) y fila *Facturación/contabilidad* ampliada — total 33 familias. La familia *Estados* desambigua la palabra más frecuente del día a día: badge (`S`) → máquina de estados / bulk (`M`) → permisos por estado (`L`) → workflow (`XL`).

**Enriquecimientos menores:** transportadoras como ejemplo de integración (piso `L`) · digest en notificaciones por evento · disponibilidad con excepciones en agenda base · "alertas por búsqueda guardada" documentada como composición.

---

## Qué cambió en la versión anterior (v1.2 — auditoría anti-duplicados)

**Recalibración de plataforma (directriz del dueño):** la calculadora asume **web por defecto**; se eliminó la señal `XL` "app móvil nativa" y se reemplazó por el modificador de plataforma `+60%` (PWA `+30%` y nativa `+60%` son excluyentes entre sí).

**Fusiones de duplicados (13 grupos):** clúster financiero XL 5→2 señales (*Dinero y datos sensibles* + *Cobro recurrente y comercio completo*) · nómina → ejemplo de *Cumplimiento regulatorio de dominio* · edición colaborativa → dentro de *Sincronización en tiempo real* · multicanal + mailing masivo → *Mensajería a escala* · "medidas de seguridad extensas" (vaga) → absorbida por *SSO / endurecimiento empresarial* · "manipulación compleja de PDF" → *Motor de PDF complejo* (resuelve contradicción con la familia Firma) · streaming acotado a video/audio en vivo · filtrado con preferencias + buscador facetado → *Búsqueda/filtrado avanzado* (L) · trío de formularios deslindado (renderizado desde config / constructor DnD / encuestas) · visualización según rol → dentro de *Permisos/visibilidad por rol* (M) · portabilidad de datos → ejemplo de *Reportes/archivos* (M) · paginación client-side → dentro de *Operaciones client-side* (S) · logo/favicon y textos legales → ejemplos de señales XS existentes.

**Re-redacciones de reglas vagas:** secuencias/IDs → *numeración consecutiva sin huecos con concurrencia* · flujo multi-etapa → *con traspaso entre ≥2 roles* · CRUD con extras → *de una entidad, con extras acotados* · temporizadores → *contador en UI / indicador de frescura* · deep links → *con restauración de estado* · chat: widget de terceros = M, chat propio = L · frontera volumen (modificador vs XL) definida · nota de integraciones precisada con sus excepciones.

**Señales nuevas (8, mercado PYME colombiano):** búsqueda global multi-entidad (L) · visualización interactiva compleja a medida (L) · generación de documentos desde plantilla fija (M) / centro de plantillas administrable (L) · cotizador público embebido con captura de lead (M/L) · canal único de mensajería vía proveedor (L) · cuenta de cobro / factura simple no-DIAN (M) · landing multi-sección sin CMS (M) · catálogo público con pedido por WhatsApp (L).

**Hardware reubicado:** la señal `XL` "integración con hardware físico" se reemplazó por el modelo *integración (piso `L`) + modificador Hardware `+25–60%`*; queda en el borde `XL` solo cuando el dispositivo es el corazón del requerimiento.

**Modificadores:** tabla reorganizada en 4 grupos (estructurales / plataforma / costo-riesgo / atenuador) · todos con rango cerrado (legacy `+15–40%`, WCAG/SEO `+20–50%`, hardware `+25–60%`) · anti-doble-conteo explícito (pantalla nueva y modelo de datos no aplican sobre `L`) · renombrado *Observabilidad / logging de errores* · **nuevos:** urgencia/exprés `+20–50%` · coordinación con equipo del cliente `+10–25%` · entregable bilingüe `+5–15%` · capacitación → ítem aparte.

**Señales espejo:** filas nuevas *Facturación*, *Duplicar* y *Plataforma*; celdas corregidas en Firma, Pagos, Correo, Tiempo real, DnD y Encuestas para eliminar contradicciones con los bullets.
