# Indicadores de Esfuerzo — Calculadora de Requerimientos (v1.1)

> **Propósito.** Este documento es el corazón del procesamiento de un requerimiento. Mapea señales concretas presentes en la **descripción de un requerimiento** hacia un **nivel de esfuerzo (XS → XL)**, que luego se traduce en horas y precio. No estima proyectos completos: clasifica **funcionalidad por funcionalidad** (o feature por feature); el proyecto es la suma.
>
> Existe por dos razones: (1) dar **consistencia** — que el mismo requerimiento reciba el mismo nivel sin importar quién (o qué IA) lo clasifique — y (2) capturar los **patrones que, por experiencia, escalan** el esfuerzo. Se mantiene deliberadamente general: la meta no es precisión quirúrgica, sino **ubicar rápido dónde encaja mejor** un requerimiento.

**Cómo se lee.** El indicador **más alto** que describe el requerimiento fija su nivel base. Los **modificadores** (al final) ajustan por encima o por debajo. Todo parte del supuesto de **desarrollo desde cero**, salvo que la descripción diga explícitamente que se extiende algo ya existente.

**Niveles:** `XS` Trivial · `S` Bajo · `M` Medio · `L` Feature completo BE+FE / Medio-alto · `XL` Varios features (se parte) / Alto.

**Regla espejo.** Muchas señales aparecen en varios niveles: la misma palabra sube o baja según si se **construye desde cero** (feature → `L`) o se **agrega sobre lo existente** (adición → `M` o menos), y según **volumen / motor** (→ `XL`). Ver la tabla *Señales espejo* al final.

---

## 🔴 ALTO — nivel base `XL` · 8 pts

> **Definición.** Si algo cae aquí es porque **debe partirse en varios requerimientos** más pequeños (`S` / `M` / `L`). No se cotiza como un solo ítem: se descompone primero. Las señales de abajo son los disparadores típicos de esa descomposición.

- Integración que maneja **pagos, facturación electrónica o datos sensibles** (pasarelas, DIAN, terceros críticos).
- Maneja **transacciones financieras** o datos sensibles.
- **Cumplimiento regulatorio** (DIAN, firmas legales, etc.).
- **Flujo multi-etapa** con múltiples tipos de usuario.
- **Manipulación compleja de PDF**: firmas, posicionamiento preciso, contenido dinámico inyectado.
- **Sincronización en tiempo real.**
- **Medidas de seguridad extensas.**
- **Arquitectura multiempresa / multi-tenant** — aislamiento de datos, roles y configuración por cliente. Estructural y transversal.
- **Migración masiva / ETL desde legacy** — extraer, mapear, limpiar, validar y reconciliar datos históricos. Por sí sola es un proyecto.
- **Motor de workflow / BPM configurable** — el cliente crea etapas, reglas, responsables, aprobaciones y condicionales.
- **Suscripciones / facturación recurrente** — planes, prorrateo, reintentos de cobro, *dunning*. Va más allá del pago puntual.
- **Búsqueda full-text con motor de indexación** (Elasticsearch/OpenSearch) — relevancia, facetas, sinónimos (la facetada "a mano" es `L`).
- **Integración bidireccional con ERP/CRM** (SAP, Salesforce, Siigo, World Office) — sincronización de maestros, colas, reconciliación.
- **Firma digital/electrónica certificada** — PKI, estampado cronológico, validez legal (distinta de "firmar un PDF").
- **Offline-first** — operar sin conexión y sincronizar con resolución de conflictos.
- **Agendamiento / reservas críticas** — disponibilidad de recursos, cupos, zonas horarias, solapamiento, concurrencia, pagos y cancelaciones.
- **Orquestación de notificaciones multicanal** — SMS/WhatsApp/push con proveedor, reintentos, plantillas por canal, opt-in/out.
- **SSO corporativo / seguridad empresarial** — SAML, LDAP, Active Directory, MFA, políticas de contraseña, auditoría avanzada.
- **Motor de BI / analítica sobre volumen** — agregaciones, drill-down, series temporales (distinto del dashboard `L` y del reporte parametrizable `M`).
- **Marketplace / plataforma de oferta y demanda** — usuarios, publicaciones, pagos, reputación, mensajes, órdenes, administración.
- **Arquitectura de alto volumen / rendimiento** — colas, caché, procesamiento paralelo, millones de registros.
- **Streaming en tiempo real** — video/audio (WebRTC) o sockets masivos.
- **Entrenamiento / fine-tuning de un modelo de IA propio** — recolección de datos y ajuste (distinto de *usar* una API de IA, que es `M`–`L`).
- **App móvil nativa / publicación en tiendas** — iOS/Android, build, firma, revisión de App Store / Play Store, actualizaciones (la PWA es un modificador; la app nativa es otro producto).
- **Integración con hardware / dispositivos físicos** — impresoras térmicas, lectores de código de barras, básculas, datáfonos, torniquetes, sensores: drivers, protocolos, pruebas en sitio.
- **Nómina / liquidación laboral colombiana** — prestaciones, seguridad social, PILA, retenciones: regulatorio de dominio con cambios normativos frecuentes.
- **Envío masivo de correos / campañas de mailing** — listas, segmentación, deliverability, bounces, unsubscribe, reputación de dominio (distinto de "notificar por evento", `M`).
- **Edición colaborativa concurrente** — varios usuarios editando el mismo documento a la vez (CRDT/OT, cursores, merge).
- **Pipeline de video** — upload + transcodificación + almacenamiento + reproducción bajo demanda.
- **API pública para terceros** — versionado, API keys, rate limiting, documentación, sandbox, soporte a integradores externos.
- **Open banking / integración bancaria directa** — conciliación de movimientos, seguridad financiera, certificaciones.
- **Checkout e-commerce completo** — carrito + pago + órdenes + estados + inventario descontado (el carrito sin pago ronda `L`).

_Rondando el borde (raros, normalmente XL):_ Web3 / smart contracts · microservicios (extraer de un monolito) · georreferenciación con rutas y tracking en vivo.

---

## 🟠 MEDIO-ALTO — nivel base `L` · 5 pts · "un feature completo"

> **Definición.** Es `L` cuando hay que construir de forma **integral y desde cero** un feature con **backend y frontend robustos** a la vez: una pieza nueva y autocontenida, no un ajuste sobre algo que ya existe. Si la descripción indica —o al preguntar se confirma— que **la base ya existe** y solo se le agrega algo, **no es `L`: es `M`** (o menor).

- **Generación dinámica** de contenido / formularios.
- **Constructor visual con drag-and-drop desde cero** — *form builder*, *page builder*, tablero Kanban (columnas, tarjetas, persistencia del orden). Agregar DnD a una lista existente es `M`.
- **Filtrado complejo** con preferencias guardadas (desde cero).
- **Buscador avanzado / búsqueda facetada** con autocompletado, filtros combinados y paginado (sin motor de indexación; con motor → `XL`).
- **Trazabilidad de historial / auditoría** (construir el registro de quién cambió qué; solo *mostrar* logs ya guardados es `M`).
- **Generación de secuencias o IDs únicos.**
- **Múltiples CRUD relacionados** entre sí / **panel de administración de entidades** (CRUD + permisos + búsqueda sobre varios modelos).
- **Autenticación / registro completo desde cero** — login, signup, verificación de correo, recuperación, sesiones. Piezas sueltas sobre auth existente (OAuth social, recuperación) son `M`; 2FA/MFA es `L`; SSO corporativo es `XL`.
- **Panel de administración de usuarios y roles (RBAC granular)** — crear roles y asignar permisos por vista o por acción.
- **Dashboard / panel de KPIs desde cero** — widgets, gráficas, agregaciones, rangos de fecha.
- **Importación masiva con validaciones** — parseo + validación + *preview* + commit + errores fila por fila + progreso. La importación trivial sin validación baja a `M`.
- **Constructor de reportes/consultas por el usuario** — el usuario arma reportes dinámicos (no solo "generar un PDF").
- **Centro / bandeja de notificaciones in-app** — leído/no leído, agrupación, preferencias, tiempo real (distinto de *notificar por evento*, que es `M`).
- **Gestor documental** — cargar, clasificar, consultar, descargar, con permisos, categorías y estados.
- **Calendario / agenda base** — vistas mensual/semanal, eventos, disponibilidad, recordatorios (→ `XL` si se vuelve scheduling con recursos y concurrencia).
- **Inventario básico desde cero** — productos, entradas/salidas, existencias, alertas, movimientos.
- **Geolocalización / mapas** — pines, clustering, rutas, polígonos (Google Maps/Mapbox); tracking en vivo → `XL`.
- **Panel de configuración / parametrización del sistema** — variables de negocio, reglas y textos administrables desde la UI.
- **Sistema de comentarios / hilos / anotaciones** — con menciones, adjuntos ligeros y notificación.
- **Gestión de etiquetas/taxonomías o de reseñas como feature completo** — agregar un rating a una entidad existente es `M`.
- **Onboarding / wizard multi-paso** con persistencia de progreso.
- **Integración con un servicio / API externo (piso)** — toda integración es **al menos `L`**; sube a `XL` con pagos, facturación, datos sensibles o bidireccionalidad.
- **Funcionalidad basada en IA / resoluble con IA** — piso `M`, típicamente `L`; **antes de dar precio**, validar alcance y factibilidad. Modelo propio / fine-tuning → `XL`.
- **OCR / extracción de datos desde documentos** — facturas, cédulas, PDFs escaneados: captura + parsing + corrección manual del resultado.
- **Chatbot / asistente con IA sobre datos propios (RAG)** — ingesta de documentos, embeddings, recuperación, UI de conversación (→ `XL` si exige fine-tuning o volumen).
- **Motor de cotizaciones / precios / descuentos / comisiones** — reglas de cálculo de negocio configurables que producen un valor (→ `XL` si el cliente arma las reglas como un BPM).
- **Constructor de encuestas / formularios públicos con resultados** — crear encuesta + responder público + resultados agregados (una encuesta fija simple es `M`).
- **CMS / portal público administrable** — blog, landing o sitio con contenido editable desde el panel (una página estática es `S`).
- **Gamificación** — puntos, niveles, insignias, ranking, reglas de otorgamiento.
- **Estructura organizacional** — sedes, sucursales, equipos, jerarquías con datos y permisos por nodo.
- **Recepción y parseo de correo entrante** — recibir emails hacia la app (inbound), extraer datos, adjuntos, responder.
- **Galería / biblioteca multimedia con procesamiento** — colecciones, miniaturas, orden, metadatos (subir una imagen a una entidad es `M`).
- **Portal de autoservicio del cliente final** — vista externa limitada donde el cliente consulta sus propios datos/documentos/estados (hereda auth y permisos).

_Rondando el borde:_ carrito de compras sin pago · feed/timeline de actividad · invitaciones/referidos · web scraping/crawling (proxies, CAPTCHAs).

---

## 🟡 MEDIO — nivel base `M` · 3 pts

> **Definición.** Funcionalidad **acotada**: no exige el feature completo BE+FE de un `L`. Suele ser una **adición o ajuste sobre una base que ya existe** o una pieza pequeña construida desde cero. Es donde cae la mayoría del trabajo real del día a día.

- **CRUD estándar** con funcionalidades adicionales.
- **Combo de listado server-side** — paginación + ordenamiento + búsqueda (o scroll infinito) manteniendo los filtros. Es lo que casi todo CRUD termina pidiendo.
- **Acciones masivas / bulk** — seleccionar N registros y aplicar (eliminar, cambiar estado, exportar, asignar).
- **Generación de reportes / archivos** (Excel, PDF) — desde básicos hasta **parametrizables** (filtros/rangos) o **programados** (cron → suma *Tarea programada*). Exportación simple desde una vista existente también es `M`.
- **Soft delete / papelera / restauración** — borrado lógico + vista de eliminados + restaurar.
- **Sistemas de permisos / visibilidad.**
- **Lógica condicional** en formularios.
- **Validaciones de negocio complejas** — cross-field, contra el backend, con reglas (distintas de las validaciones básicas `XS`).
- **Campos calculados / derivados** — totales, subtotales, impuestos, saldos, vencidos que se recalculan.
- **Carga de imágenes / archivos con procesamiento** y **adjuntar archivos a una entidad existente**.
- **Clonar / duplicar una entidad con sus relaciones** (más que duplicar un documento, que es `S`).
- **Versionado ligero / snapshots** con reversión a una versión previa.
- **Autoguardado / borradores (drafts).**
- **Preferencias de usuario / de app** — columnas visibles, orden, vista o tema preferido; aplican en runtime.
- **Visualización de contenido según rol.**
- **Documento o correo con maquetación / branding** — membretes, tipografías, identidad corporativa, marcas de agua ligeras (entre la plantilla básica `S` y el PDF complejo `XL`).
- **Notificaciones por evento** (in-app o correo) — detectar el evento, plantilla, envío. Periódica → suma *Tarea programada*.
- **Máquina de estados / cambios de estado** — transiciones y reglas (→ `L` si hay acciones/permisos por estado o varios actores).
- **Mostrar historial ya registrado** — si los logs ya se guardan y solo hay que exponerlos (construir la trazabilidad es `L`).
- **Integrar un componente de terceros en el FE** — mapa embebido, editor WYSIWYG, date-range picker, tabla avanzada, reCAPTCHA, recorte de imagen.
- **Webhook saliente simple** — enviar un payload a un tercero cuando ocurre un evento.
- **Login social (OAuth) o recuperación de contraseña** sobre una autenticación que ya existe.
- **Importación simple** sin motor avanzado de validación o conciliación.
- **Tema claro / oscuro (theming)** — ligero pero **transversal**.
- **Configurar / parametrizar una regla de negocio antes fija en el código** — UI para administrarla (→ `L` si es un panel de configuración completo).
- **Generalizar una operación (crear/editar/eliminar) del caso base a N casos o modelos** — creación en cascada (→ `L` si obliga a un motor completo).
- **Multidioma (i18n)** — **transversal**.
- **Chat en vivo / mensajería en tiempo real** — piso `M`; sube a `L` según alcance (presencia, bots/IA, archivos, historial persistente).
- **Firma dibujada en canvas / aceptación en pantalla** — trazo sobre canvas o botón "acepto" con evidencia (≠ firma certificada `XL`, ≠ posicionar firmas en PDF `XL`).
- **Generación / lectura de códigos QR o de barras** — generar el código es simple; escanear con cámara sube dentro de `M` o a `L` según el flujo.
- **Actualización en vivo de una vista puntual** — polling o un websocket acotado para refrescar un dato (≠ *sincronización en tiempo real* transversal, `XL`).
- **Multi-moneda / conversión de divisas** — mostrar y calcular montos en más de una moneda con tasa administrable.
- **Vencimientos / renovaciones con alertas** — fechas de expiración de contratos, membresías o documentos + recordatorio (suma *Tarea programada*).
- **Términos y condiciones con aceptación versionada / consentimientos** — registrar quién aceptó qué versión y cuándo (Habeas Data básico).
- **Exportación de datos del usuario / portabilidad** — "descargar mis datos" en un formato legible.
- **Sesiones activas / cierre remoto / bloqueo por inactividad** — listar dispositivos, cerrar sesión a distancia, timeout.
- **Impersonación ("ingresar como usuario") para admins** — con evidencia de auditoría y salida segura.
- **Rate limiting / anti-abuso / captcha** en formularios o endpoints públicos.
- **Cifrado de campos sensibles / anonimización puntual** — proteger columnas específicas (≠ *medidas de seguridad extensas*, `XL`).
- **Tarea técnica no funcional pedida como requerimiento** — actualizar framework, migrar hosting, SSL/dominio, optimización puntual: se clasifica y cotiza aparte del roadmap funcional.

_Rondando el borde:_ favoritos/guardados · recordatorios/snooze · manejo de zona horaria/locale.

---

## 🟢 BAJO-MEDIO — nivel base `S` · 2 pts

> **Definición.** Cambio **visible para el usuario pero de alcance reducido**: interacción de UI o feedback puntual, sin tocar el modelo de datos ni la lógica de negocio.

- Cambios de **estilo (UI) o de plantilla** / ajustes menores a tarjetas, tablas, botones o formularios.
- **Diálogo de confirmación** (antes de una acción destructiva).
- **Toast / alerta efímera** de éxito, error o advertencia.
- **Búsqueda / filtro / orden client-side** sobre datos ya cargados (incl. *typeahead* sobre un endpoint existente).
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
- **Temporizadores o monitoreo simple.**
- **Script de terceros simple** — pixel, Hotjar, Google Analytics.
- **Ajuste responsive puntual** de una sección (el responsive completo es un modificador).
- **Meta tags / Open Graph / favicon por página** — títulos, descripciones e imagen de compartir.
- **Animaciones / micro-interacciones puntuales** — transiciones, hover, feedback visual.
- **Paginación client-side simple** sobre datos ya cargados.
- **Deep links / anclas** — enlazar directo a una sección o estado de una vista existente.

_Rondando el borde:_ breadcrumbs · contador de caracteres/límites en input.

---

## ⚪ BAJO — nivel base `XS` · 1 pt

> **Definición.** Cambio **puntual y aislado** que no toca estructura, modelo de datos, flujo, permisos amplios ni lógica de negocio.

- **Cambio de copy** — texto, etiqueta, título, placeholder, mensaje de validación o typo (sin lógica).
- **Cambio visual puntual** — color, ícono, imagen estática, espaciado, tamaño, variable CSS / theming menor.
- **Cambiar el valor por defecto** de un campo.
- **Marcar un campo requerido/opcional** o cambiar un límite (maxlength/rango) · validación básica.
- **Agregar / quitar una opción estática** a un select o enum existente.
- **Ocultar / mostrar un elemento existente** (por rol o condición simple).
- Agregar un **checkbox/toggle** o un **enlace simple** / cambiar una ruta o redirección.
- **Ajustar un permiso puntual** — dar acceso de una vista a un rol.
- **Cambiar formato de visualización** — fecha, moneda, número — o el orden por defecto.
- **Reordenar campos o columnas** / cambiar el criterio de un filtro fijo.
- **Activar / desactivar** un feature flag o configuración ya construida.
- **Actualizar una variable de entorno** / API key / URL (staging → producción).
- **Cambio de logo / favicon / imagen de marca** (reemplazar el asset, sin rediseño).
- **Ajuste de textos legales existentes** (actualizar el contenido de una página ya construida).

---

## Modificadores y reglas de ajuste

No definen el nivel por sí solos: lo **ajustan** por encima o por debajo.

| Modificador | Efecto |
|---|---|
| Pantalla nueva (frontend que hoy no existe) | `+15–25%` |
| Modelo de datos / migraciones (tablas, campos, relaciones) | `+10–20%` |
| Transversal (toca muchas pantallas o documentos) | `×1,4–1,8` |
| Motor nuevo (PDF de reportes, plantillas de correo, etiquetas) | `+30–80%` (o `+1 nivel` si es pesado) |
| Concurrencia / atomicidad (bloqueos, stock atómico) | `+20–40%` |
| Tarea programada / cron (Huey) | `+8–16 h` |
| Aplica también a la PWA contratada | `+30%` al esfuerzo |
| Diseño UI/UX **no** entregado por el cliente | `+15–30%` |
| Responsive completo (móvil + tablet + desktop) | `+15–35%` |
| Permisos por campo o por acción (granular, sobre algo existente) | `+20–40%` |
| Carga inicial / *backfill* de datos al desplegar (≠ crear el modelo nuevo) | `+10–30%` |
| Volumen alto de datos | `+20–50%` |
| Pruebas con múltiples roles | `+10–25%` |
| Trazabilidad de errores / logs exigida | `+10–20%` |
| Tests automatizados / cobertura mínima exigida | `+10–25%` |
| Código legacy sin tests / deuda técnica | `+%` por fricción |
| Dependencia de tercero externo (mal documentado o sandbox inestable) | `+15–40%` (riesgo) |
| Despliegue / operación en producción (dominios, correos, variables, backups, CI/CD, monitoreo, colas nuevas) | `+10–30%` o ítem aparte |
| Accesibilidad (WCAG) o SEO/SSR como requisito explícito | `+%` (refactor total de la plataforma = `XL`) |
| Datos semilla / fake data para demo o capacitación | `+5–10%` (o ítem aparte si es un dataset grande) |
| Documentación / manual de usuario exigido como entregable | `+10–20%` |
| Hardware o pruebas en sitio (visitas, dispositivos físicos) | `+%` por riesgo y logística |
| **Extiende algo ya existente** — agregar un filtro, una columna, un drag-and-drop o una opción a algo que ya existe | Baja el nivel: como **no** se construye el feature completo, **rara vez es `L`** → suele quedar en `M` o menos. Rompe el supuesto "desde cero"; **debe estar declarado** (si no, preguntar). |

### Condiciones de bloqueo (no son porcentaje)

- **Requerimiento ambiguo o con reglas sin definir** → **no cerrar precio fijo** hasta aclarar. Es una decisión comercial, no un ajuste de tamaño.
- **Bloqueo externo** → depende de que el cliente o un tercero entregue credenciales, accesos o datos. Afecta el cronograma, no el tamaño.

---

## Señales espejo (misma palabra, distinto nivel)

El diferenciador es *desde cero vs. sobre lo existente* y *volumen / motor*.

| Familia | `XS`–`S` | `M` | `L` | `XL` |
|---|---|---|---|---|
| Búsqueda | client-side sobre datos cargados | server-side en un listado | buscador facetado con autocompletado | full-text con indexación |
| Importación | — | simple sin validación | masiva con validaciones | migración / ETL desde legacy |
| Notificaciones | toast efímero | por evento (in-app/correo) | centro / bandeja in-app | orquestación multicanal |
| Datos / visualización | badge de estado | métricas o reporte parametrizable | dashboard desde cero | motor de BI sobre volumen |
| Autenticación | — | OAuth / recuperación sobre lo existente | módulo completo o 2FA/MFA | SSO corporativo |
| Permisos | ajuste puntual (XS) | permisos / visibilidad | panel RBAC granular | seguridad empresarial |
| Documentos | descarga estática | adjuntar a una entidad | gestor documental | firma certificada / PDF complejo |
| Drag-and-drop | — | agregar DnD a una lista existente | constructor / Kanban desde cero | — |
| Validación | requerido/límite (XS), regex (S) | de negocio (cross-field) | — | cumplimiento regulatorio |
| Geo / mapas | — | — | mapa con pines y rutas | tracking en vivo / georreferenciación |
| Tiempo real | refresco manual / botón actualizar | polling o websocket en una vista | chat / feed en vivo acotado | sincronización transversal / colaborativa |
| Firma | — | dibujada en canvas / aceptación | posicionada en un PDF propio | certificada PKI / validez legal |
| Pagos | — | — | link de pago de pasarela | checkout integrado / suscripciones |
| Correo | plantilla básica texto plano | correo con branding / por evento | centro de plantillas administrable | campañas masivas / deliverability |
| IA | — | llamada a API con prompt fijo | feature con IA + UI (RAG típico) | fine-tuning / modelo propio |
| Móvil | responsive puntual (S) | responsive completo (modificador) | PWA (modificador +30%) | app nativa / tiendas |
| Media / archivos | descarga estática | upload con procesamiento | galería / gestor multimedia | video transcodificado / streaming |
| Encuestas / formularios | — | encuesta fija simple | constructor con resultados agregados | motor de formularios (form builder) |

---

## Notas de clasificación

- **`M` vs `L` — la pregunta clave.** `L` = construir un **feature completo BE+FE desde cero**, integral y autocontenido. `M` = **agregar o ajustar sobre algo que ya existe**, o una pieza que no llega a feature completo. Ante la duda de si la base existe, **preguntar**: si no existe, primero hay que construirla (eso sí es `L`) y el ajuste viene después.
- **`XL` = se parte.** Si un requerimiento da `XL`, no se cotiza entero: se descompone en requerimientos `S` / `M` / `L`.
- **Personalización = escalón, no salto.** Volver configurable algo fijo en código suele quedar en `M`; solo es `L` si el espacio de configuración es en sí un feature completo.
- **Generalización = escalón.** "Que funcione para todos los casos, no solo el base" tiende a `M`; pasa a `L` cuando obliga a construir un **motor** (ver *Motor nuevo*).
- **Integraciones: nunca por debajo de `L`.** El piso sube según autenticación, volumen, bidireccionalidad y criticidad del dato.
- **IA: primero alcance, luego precio.** Piso `M`, tiende a `L`; modelo propio o fine-tuning es `XL`.
- **Presentación con marca.** Un PDF o correo deja de ser básico (`S`) apenas pide membrete o identidad → `M`; solo llega a `XL` con firmas, posicionamiento preciso o contenido dinámico complejo.
- **Operación en producción no es gratis.** Despliegue, dominios, correos, backups, ambientes y monitoreo se cobran como modificador o ítem aparte.
- **Lo técnico también se cotiza.** Upgrades de framework, migraciones de hosting y optimizaciones son requerimientos por derecho propio (`M`–`L` según alcance), no favores implícitos.
- **Hardware = riesgo físico.** Cualquier dispositivo físico agrega pruebas en sitio, drivers y variables fuera del control del software: nunca subestimarlo.

---

## Qué cambió en esta versión (v1.1)

**Ampliación de blindaje** — señales agregadas para cubrir dominios que la v1.0 no contemplaba:

- **XL (9 nuevas):** app móvil nativa / tiendas · integración con hardware físico · nómina / liquidación laboral colombiana · envío masivo de correos / campañas · edición colaborativa concurrente · pipeline de video (upload + transcodificación) · API pública para terceros · open banking / integración bancaria · checkout e-commerce completo.
- **L (10 nuevas):** OCR / extracción de datos de documentos · chatbot IA sobre datos propios (RAG) · motor de cotizaciones / precios / descuentos / comisiones · constructor de encuestas con resultados · CMS / portal público administrable · gamificación · estructura organizacional (sedes/equipos) · recepción y parseo de correo entrante · galería / biblioteca multimedia · portal de autoservicio del cliente final.
- **M (12 nuevas):** firma en canvas / aceptación en pantalla · códigos QR / barras · actualización en vivo de una vista (polling/websocket puntual) · multi-moneda · vencimientos / renovaciones con alertas · T&C con aceptación versionada / consentimientos · exportación / portabilidad de datos del usuario · sesiones activas / cierre remoto · impersonación de admins · rate limiting / captcha · cifrado de campos sensibles · tarea técnica no funcional (upgrade, hosting, SSL).
- **S (4 nuevas):** meta tags / Open Graph / favicon por página · animaciones / micro-interacciones · paginación client-side simple · deep links / anclas.
- **XS (2 nuevas):** cambio de logo / favicon / imagen de marca · ajuste de textos legales existentes.
- **Señales espejo (7 familias nuevas):** tiempo real · firma · pagos · correo · IA · móvil · media/archivos (+ encuestas/formularios).
- **Modificadores (3 nuevos):** datos semilla / fake data (`+5–10%`) · documentación / manual de usuario (`+10–20%`) · hardware o pruebas en sitio (`+%` riesgo).
- **Notas nuevas:** "lo técnico también se cotiza" y "hardware = riesgo físico".
