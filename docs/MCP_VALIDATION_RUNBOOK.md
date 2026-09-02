# Guion de validación y mantenimiento de MCP

Las carpetas del conector de Documentos declaran `folder_kind`, proyecto y
estado. `create_folder` hereda la asociación de su padre y `rename_folder`
rechaza raíces automáticas de proyecto; estas protecciones se validan junto
con los contratos de modelo antes de publicar cambios del gestor.

Última revisión integral: 2026-09-02.

Este documento es el procedimiento repetible para validar los conectores MCP de
ProjectApp. Cubre el transporte compartido, las catorce herramientas de
Comunicaciones, el ciclo recuperable de observaciones en Documentos y la
paridad de los ocho conectores preexistentes. La fuente
ejecutable del inventario está en `backend/content/views/mcp_blog.py`; la
clasificación de campos vive en `backend/content/mcp/contracts.py`.

## Invariantes

- Cada conector usa `/api/mcp/<slug>/<token>/`, un token propio almacenado sólo
  como hash, el mismo control de Origin, throttle, actor y registro de actividad.
- Un conector nuevo nace inactivo y sin token. Activarlo y emitir la URL es una
  decisión explícita del superusuario en `/panel/mcps`.
- Los handlers MCP reutilizan serializers y servicios del panel. Una regla que
  impide una acción en la interfaz también la impide por conversación.
- Las carpetas con `system_key` pertenecen al archivado automático. El MCP puede
  listarlas para orientar al operador, pero no crearlas debajo, renombrarlas ni
  usarlas como destino de un documento markdown.
- Ninguna descripción puede prometer un dato que el handler descarte o una
  acción que el servidor no realiza.
- `DocumentState.description` es una lectura clasificada del contrato MCP. Para
  estados de proyecto, la descripción administrable no sustituye el
  `operational_effect` ni la ayuda de consecuencias derivada por el sistema.
- `UserProfile.document_navigation_mode` es una preferencia de presentación del
  panel y permanece clasificada como perfil/plataforma: no altera ni se expone
  en las herramientas MCP de clientes o Documentos.
- Todo `Project` pertenece a los catálogos de Documentos y Comunicaciones; no
  existe un opt-out por módulo. `DocumentFolder.managed_project` identifica su
  única raíz documental canónica. El MCP puede seguir referenciando proyectos
  existentes, pero no adopta carpetas históricas ni provisiona raíces por esa
  vía.
- `DocumentFolder.managed_client` es el equivalente para clientes y se comporta
  igual desde el MCP: read-only, sin adopción ni provisión por esa vía. Con él
  `folder_kind` tiene **tres** valores (`project` / `client` / `manual`), que es
  lo que declara la descripción de `list_folders`. Dos asimetrías respecto de
  proyectos, deliberadas: la raíz de cliente **no** se crea sola con el cliente
  (se adopta), y **sí** se puede renombrar —el nombre lo pone el operador, no un
  módulo externo—, así que `rename_folder` la acepta.
- **Archivado de clientes.** `UserProfile.archived_at` (antes `deactivated_at`)
  es el eje de ciclo de vida del cliente, con el mismo vocabulario que el bucket
  no activo de proyectos. `list_clients` devuelve **sólo activos** salvo que se
  pida `archived=true`: devolverlos mezclados es como el conector termina
  proponiendo trabajo sobre un cliente que se archivó a propósito. `archived_at`
  es read-only y `archived_by` está excluido como auditoría interna, junto a
  `created_by` — archivar **no** es una operación del MCP, porque suspende los
  proyectos del cliente y cancela su facturación futura, y eso exige la vista
  previa del panel. El archivado de un hilo de comunicaciones sólo cambia su
  visibilidad y sí está expuesto mediante una acción de dominio específica.
- `update_message` edita sólo un borrador saliente activo;
  `delete_draft` aplica la misma condición; `mark_message_sent` registra un
  hecho externo. Ninguna herramienta envía correo ni WhatsApp.
- `CommunicationThread.managed_project` / `managed_client` identifican la
  **comunicación madre** de un proyecto o un cliente, en paralelo con
  `DocumentFolder.managed_project` / `managed_client`. Son read-only para el MCP:
  la madre de proyecto se provisiona sola al crearse el proyecto, la de cliente
  sólo por adopción revisada, y ninguna se marca desde una herramienta.
  `thread_kind` toma tres valores (`project` / `client` / `manual`).
- El **archivado** de hilos (`is_archived`/`archived_at`) es un eje de visibilidad
  ortogonal a `status` (`open`/`closed`): cerrar bloquea la escritura, archivar
  saca de la vista. Esos campos son read-only: el MCP sólo puede cambiarlos con
  `archive_thread`/`unarchive_thread`, que reutilizan el servicio del panel; una
  comunicación madre no se puede archivar. `list_threads` expone
  `scope=active|archived|all` y conserva `active` como valor por defecto.
- Los hilos entre documentos (`DocumentThread` / `DocumentThreadItem`) sí forman
  parte del conector `documents`. Tres reglas los gobiernan y ninguna se puede
  relajar desde una herramienta:
  - **La edición de miembros es incremental.** El PATCH del panel reemplaza la
    lista completa y disuelve el hilo cuando queda un solo miembro; un conector
    que reconstruyera esa lista destruiría la historia al olvidar una entrada.
    Por eso `update_document_thread` expone `link` / `unlink_document_ids`, se
    rechaza antes de bajar de dos documentos, y disolver es una herramienta
    aparte.
  - **Enlazar acepta sólo documentos markdown activos**, la misma regla del
    resto del conector. Leer y desenlazar aceptan cualquier miembro, porque un
    hilo armado desde el panel puede contener una cuenta de cobro o un
    documento archivado.
  - **Las cuentas de cobro emitidas siguen excluidas del contrato documental
    MCP.** Su `generated_file`, hash/procedencia y datos contables son artefactos
    comerciales de sólo lectura en el panel; `list_documents`/`read_document`
    continúan operando únicamente Markdown y no prometen vista previa, descarga
    ni reemplazo del PDF. Esta exclusión no impide leer una cuenta que ya sea
    miembro de un hilo creado desde el panel.
  - **`position` es derivada** de la cronología: el conector envía fechas y el
    servidor mantiene el orden estable. Es la única exclusión del contrato.
  - **La fila del listado es una sola.** `list_document_threads` y el índice de
    hilos del panel (`GET /api/document-threads/`) comparten
    `DocumentThreadListSerializer` sobre `thread_list_queryset`, igual que ya
    compartían la consulta. Al tocar esa fila hay que verificar ambas
    superficies: las fechas se serializan con `isoformat()` (`+00:00`), no con
    los campos de fecha de DRF, que emitirían `Z` y romperían al conector.
  `dissolve_document_thread` es irreversible —se pierde `linked_by`/`linked_at`—
  y por eso devuelve el hilo completo previo más `released_document_ids`, con lo
  que se puede recrear con `create_document_thread`.
- Nunca copiar tokens reales en tickets, fixtures, logs, commits o este guion.

## Inventario vigente

| Slug | Herramientas | Alcance |
|---|---:|---|
| `blog` | 7 | Plantilla, CRUD, apertura completa y calendario editorial |
| `documents` | 22 | Carpetas manuales, markdown, cliente/proyecto, estados, observaciones recuperables e hilos entre documentos; jerarquías generadas visibles pero protegidas |
| `clients` | 6 | Búsqueda, detalle, CRUD y regla de huérfano transversal |
| `communications` | 14 | Consulta y ciclo de vida de hilos; creación, edición, eliminación de borradores, envío confirmado, anulación y corrección de mensajes |
| `tasks` | 17 | Tareas, archivo, comentarios, alertas y orden del tablero |
| `accounting` | 69 | Libros, hosting, pagos/abonos, recurrentes, bolsillo, tarjetas y extractos |
| `diagnostics` | 13 | Diagnósticos, metadatos, secciones, estados y envíos |
| `proposals` | 11 | Propuestas JSON, ciclo, duplicación, envío y enlaces |
| `linkedin-personal` | 7 | Conexión, borradores, programación y publicación de texto |

## Preparación segura

1. Ejecutar en una base de test o staging. Producción sólo admite consultas
   read-only hasta que el operador autorice una mutación concreta.
2. Confirmar que existe un superusuario activo: las escrituras MCP quedan
   atribuidas a ese actor y fallan de forma explícita si no existe.
3. Generar un token temporal para el conector bajo prueba y activarlo.
4. Inicializar con `initialize`, consultar `tools/list` y comparar nombres,
   descripciones y schemas con el inventario esperado.
5. Al terminar, desactivar el conector y rotar/revocar el token temporal.

Petición base para una llamada manual (sustituir los marcadores localmente):

```bash
curl -sS -X POST 'https://<host>/api/mcp/<slug>/<token>/' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://claude.ai' \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Para invocar una herramienta:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": {}
  }
}
```

Toda llamada válida responde HTTP 200. Un error de negocio también usa HTTP
200, con `result.isError=true` y texto accionable. Token o slug inválido e
inactividad responden 404 para no revelar conectores.

## Comunicaciones: guion por herramienta

Usar dos clientes, un proyecto de cada cliente, un documento markdown de cada
cliente y un superusuario. Conservar los IDs que devuelve cada paso.

`list_threads` y el endpoint del panel comparten
`communication_query_service.py`. Los argumentos escalares del conector se
normalizan como una selección de un valor y conservan su contrato; el REST puede
enviar valores repetidos o separados por coma para la selección múltiple del
panel. En ambos caminos, canal, dirección, estado del mensaje y fechas deben
coincidir en un mismo mensaje, no en mensajes distintos del mismo hilo. El
argumento `q` busca por título del hilo, cliente, nombre de proyecto, asunto o
contenido del mensaje en ambos caminos.

`CommunicationPanelPreference` queda excluido deliberadamente del conector:
sus campos personalizan la interfaz de una cuenta y no forman parte del registro
conversacional que MCP consulta o modifica.

### 1. `list_threads`

Lectura exitosa:

```json
{
  "client_id": 10,
  "project_id": 20,
  "status": "open",
  "channel": "email",
  "direction": "outgoing",
  "message_status": "draft",
  "reply_status": "unanswered",
  "date_from": "2026-08-01",
  "date_to": "2026-08-31",
  "q": "Portal Boreal",
  "order": "recent",
  "scope": "active",
  "page": 1,
  "page_size": 20
}
```

Verificar `results`, `count`, `page` y `num_pages`; cada fila debe incluir
cliente/proyecto, actividad, conteos y preview vigente. `reply_status` acepta
`answered` o `unanswered` y evalúa mensajes salientes enviados no anulados
mediante su relación explícita de respuesta. Repetir por separado con
`client_id`, con `project_id` y con `q` igual a una parte del nombre del proyecto
para probar los cortes estructurados y la búsqueda legible.

Errores: filtros, `order` o `scope` fuera de catálogo, fecha no ISO, página cero
e IDs no enteros deben producir `isError=true`. Una página
posterior al final puede normalizarse a la última página, como `Paginator`.

### 2. `get_thread`

```json
{"thread_id": 30}
```

Verificar mensajes cronológicos completos, estados, `reply_to`, documentos y
correcciones de fecha. Un ID inexistente, vacío, cero o no entero debe fallar sin
crear ni modificar registros.

### 3. `create_thread`

```json
{"client_id": 10, "project_id": 20, "title": "Aprobación de entrega"}
```

Verificar que nace `open`, vacío y atribuido al actor MCP. Casos de error:
cliente omitido/inexistente, título vacío, perfil no cliente y proyecto de otro
cliente. Ningún rechazo puede dejar un hilo parcial.

### 4. `update_thread`

```json
{"thread_id": 30, "title": "Aprobación final", "project_id": null}
```

Verificar que corrige sólo los campos enviados, conserva cliente e historial y
permite asociar o desasociar un proyecto del mismo cliente. Deben fallar: hilo
cerrado, proyecto ajeno, título vacío, ausencia de campos editables y cualquier
campo no declarado. Ningún rechazo puede producir una actualización parcial.

### 5–6. `close_thread` / `reopen_thread`

```json
{"thread_id": 30}
```

`close_thread` debe registrar estado, fecha y actor. Mientras el hilo está
cerrado, crear mensajes, editar su cabecera o confirmar un borrador enviado debe
fallar. `reopen_thread` revierte esa condición sin tocar archivo ni historial.
Cerrar uno ya cerrado o reabrir uno abierto debe ser un error explícito.

### 7–8. `archive_thread` / `unarchive_thread`

```json
{"thread_id": 30}
```

Archivar retira el hilo del `scope=active`, lo incorpora a `archived` y lo
mantiene en `all`; restaurar hace el movimiento inverso sin alterar `status`.
Una comunicación madre de proyecto o cliente no se puede archivar. Repetir la
misma transición debe fallar sin modificar fechas ni actor.

### 9. `create_message`

Saliente de correo con referencia documental:

```json
{
  "thread_id": 30,
  "channel": "email",
  "direction": "outgoing",
  "subject": "Acta de entrega",
  "content": "Adjunto el acta para aprobación.",
  "occurred_at": "2026-09-02T15:00:00Z",
  "document_ids": [40]
}
```

Debe quedar como `draft`: crear no equivale a enviar. Un mensaje entrante de
WhatsApp queda `received`, sin asunto. `reply_to_id` sólo acepta un mensaje
previo del mismo hilo y dirección opuesta. Deben fallar: hilo cerrado, email sin
asunto, WhatsApp con asunto, contenido vacío, documento de otro cliente,
documento inexistente, respuesta de otro hilo o de igual dirección. Cada fallo
debe dejar iguales los conteos de mensajes y referencias.

### 10. `update_message`

```json
{
  "message_id": 50,
  "subject": "Acta de entrega corregida",
  "content": "Texto corregido.",
  "document_ids": [40],
  "reply_to_id": null
}
```

Verificar que se conserva ID, hilo, canal y dirección, se reemplazan —no se
acumulan— documentos y queda una revisión append-only con el diff suministrado.
Sólo un borrador saliente activo es editable. Mensajes enviados, recibidos,
fallidos o anulados, documentos ajenos y respuestas de otro hilo deben fallar
sin cambiar el registro.

### 11. `delete_draft`

```json
{"message_id": 50}
```

Verificar eliminación física del borrador y retorno de `deleted`, `id` y
`thread_id`. Sólo aplica a borradores salientes activos; la evidencia enviada,
recibida, fallida o anulada debe preservarse y producir `isError=true`.

### 12. `mark_message_sent`

```json
{"message_id": 50, "occurred_at": "2026-09-02T15:05:00Z"}
```

Verificar transición `draft → sent`, fecha efectiva y actor. Repetir sin
`occurred_at` para conservar la fecha registrada. Deben fallar un mensaje
entrante, uno ya enviado, uno anulado, un hilo cerrado, un ID inexistente y una
fecha no ISO. Confirmar que no se creó `EmailLog` ni se invocó ningún proveedor:
la herramienta sólo registra el envío realizado por fuera.

### 13. `void_message`

```json
{"message_id": 51, "reason": "Registro duplicado"}
```

Verificar que el mensaje histórico permanece visible con fecha, motivo y actor
de anulación. Sólo se anulan mensajes enviados, recibidos o fallidos; un
borrador, una segunda anulación o un motivo vacío deben rechazarse.

### 14. `correct_message_date`

```json
{
  "message_id": 51,
  "occurred_at": "2026-09-01T18:30:00Z",
  "reason": "Corrección contra evidencia externa"
}
```

Verificar la nueva fecha y una corrección append-only con valor anterior, valor
nuevo, motivo y actor. Sólo aplica a mensajes históricos no anulados; borradores,
fecha idéntica, formato inválido o motivo vacío deben fallar sin crear auditoría.

## Documentos: eliminación recuperable de observaciones

Usar un documento markdown con dos observaciones, una pendiente enlazada a un
episodio **Solucionar bug** con `origin=note` y otra resuelta o descartada. Las
herramientas reutilizan el mismo servicio transaccional que el panel.

### 1. `delete_document_notes`

```json
{"document_id": 40, "note_ids": [70, 71]}
```

Verificar que una sola llamada elimina lógicamente toda la selección, devuelve
`deleted_note_ids` y no deja resultados parciales. Las observaciones salen de
`read_document`, de la lista activa y de los conteos. Si la selección contenía
la última pendiente de un episodio originado por observaciones, ese episodio se
cierra como `removed`; un estado manual nunca se cierra por esta regla.

Deben fallar sin modificar nada: selección vacía, IDs repetidos, observación de
otro documento, ID inexistente y observación ya eliminada. Se puede eliminar
una observación pendiente, resuelta o descartada; una copia enviada antes por
correo o mensaje permanece fuera del sistema.

### 2. `list_deleted_document_notes`

```json
{"document_id": 40}
```

Verificar que sólo devuelve la papelera recuperable con contenido, estado,
`deleted_at` y actor. La lectura normal del documento debe seguir ocultando esas
filas. El historial técnico de eliminación es distinto: registra actor y fecha,
pero no crea una copia del título o contenido.

### 3. `restore_document_note`

```json
{"document_id": 40, "note_id": 70}
```

Verificar que la observación vuelve al alcance activo. Si era pendiente y su
eliminación había cerrado el episodio enlazado, la restauración reabre o
reutiliza **Solucionar bug** y vuelve a enlazarla. Una incompatibilidad de
estados o un estado retirado debe revertir toda la operación y conservar la
observación en la papelera. Restaurar una fila activa o de otro documento debe
fallar de forma explícita.

## Documentos: hilos entre documentos

Usar tres documentos markdown activos en carpetas distintas —el punto del hilo
es que la historia cruza carpetas, clientes y proyectos— y un cuarto que ya
pertenezca a otro hilo. Las herramientas reutilizan `document_thread_service`,
el mismo servicio transaccional que el modal del panel.

### 1. `create_document_thread`

```json
{"title": "Etapa 2 · Conteo Diario",
 "items": [{"document_id": 138, "occurred_on": "2026-08-16"},
           {"document_id": 146, "occurred_on": "2026-08-24"}]}
```

Verificar que el hilo nace con los documentos ordenados **por fecha**, no por el
orden en que se enviaron, y que `occurred_on` omitido cae en `issue_date` o en
el día Bogotá de `created_at`. Sin `title`, el nombre es el del primer documento.

Deben fallar sin crear nada: un solo documento, un documento repetido, uno que
ya pertenece a otro hilo (el mensaje nombra el hilo dueño), una cuenta de cobro,
un documento archivado y una fecha que no sea `YYYY-MM-DD`.

### 2. `get_document_thread` y `list_document_threads`

```json
{"document_id": 146}
```

Verificar que un documento suelto responde `thread: null` —no un error— y que
`thread_id` abre el mismo hilo. En el listado, comprobar `document_count`,
`first_occurred_on`, `last_occurred_on`, `latest_item` y que `search` encuentra
el hilo tanto por su nombre como por el título de cualquiera de sus documentos.

### 3. `update_document_thread`

```json
{"thread_id": 4, "link": [{"document_id": 162, "occurred_on": "2026-08-27"}]}
```

**La verificación que importa**: los miembros no mencionados siguen ahí. Un
`link` agrega o re-fecha; `unlink_document_ids` retira sin borrar el documento.
La operación que dejaría el hilo con menos de dos documentos debe rechazarse y
el hilo quedar intacto — ésa es la diferencia con el PATCH del panel, que ahí sí
disuelve. Renombrar y mover miembros en la misma llamada es atómico: si el
nombre falla, la membresía tampoco cambia.

### 4. `dissolve_document_thread`

```json
{"thread_id": 4}
```

Verificar que los documentos sobreviven y quedan disponibles para otro hilo, que
la respuesta trae el hilo completo previo y `released_document_ids`, y que un
documento antes enlazado ya se puede eliminar (el `PROTECT` lo bloqueaba).

## Revalidación de conectores existentes

| Conector | Lectura que debe comprobarse | Escritura/acción que debe comprobarse | Error representativo |
|---|---|---|---|
| Blog | `get_blog_post` devuelve JSON bilingüe, fuentes, SEO, portada y LinkedIn | crear/editar conserva esos campos | post inexistente o payload incompleto |
| Documents | resumen/detalle y filtros muestran cliente, proyecto, estados, tags y sólo observaciones activas | crear/editar mantiene asociaciones; eliminar/restaurar observaciones reconcilia estados y papelera en una transacción | proyecto ajeno, archivado, selección de observaciones mezclada o restauración incompatible |
| Clients | métricas incluyen documentos, ingresos, hostings y comunicaciones | CRUD usa `proposal_client_service` | un hilo impide tratar/eliminar el cliente como huérfano |
| Communications | hilo completo incluye ciclo de vida, mensajes, documentos, correcciones y revisiones; listado separa activos/archivados | cabecera y ciclo del hilo más crear/editar/eliminar borrador, confirmar envío, anular y corregir fecha convergen en `communication_service` sin enviar por el canal | transición repetida, comunicación madre, mensaje no editable, proyecto/documento ajeno o respuesta de otro hilo |
| Tasks | detalle, comentarios y alertas reflejan el modelo actual | CRUD, archivo, orden y duplicación | comentario/alerta de otra tarea |
| Accounting | detalle incluye pagos, deducciones, cuenta de cobro, período de hosting y ciclo de vida de recurrentes | `settle_income`/`bulk_settle_incomes` crean pagos; las seis tools de recurrentes preparan duplicado, cambian estado, archivan/restauran, silencian avisos y aplican lote por el mismo servicio del panel | no esperado, repetido, excedido, ID perdido o intento de activar/silenciar un recurrente archivado |
| Diagnostics | detalle expone slug, expiración y cliente | update permite esos campos y usa el serializer actual | slug duplicado o cliente inválido |
| Proposals | detalle expone metadata comercial completa | importación y duplicación conservan nacionalidad, tipos custom y modo de contrato; `update_proposal` con `technicalDocument` exige que cada ítem de los requerimientos funcionales quede referenciado en algún `linked_item_ids` | JSON incompleto, transición inválida o detalle técnico que deja ítems sin trazar (`technical_item_coverage_incomplete`) |
| LinkedIn | estado de token/post y errores de publicación | borrador, programación, edición, borrado y publicación de texto | token ausente/expirado o post no publicable |

## Verificación automatizada

Desde `backend/`, con el virtualenv del clon principal y nunca con la suite
completa. Cada comando respeta el máximo de 20 tests; iniciar otro ciclo después
de tres comandos.

```bash
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_communication_admin_actions.py -q

/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_communication_update.py -q

/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_contracts.py -q -k 'not tool_metadata'
```

En el ciclo siguiente, ejecutar `test_mcp_contracts.py -k tool_metadata`, la
regresión focal de `test_mcp_communications.py`, el servicio afectado —si hubo
cambios allí— y `test_mcp_parity_refresh.py`; no agrupar archivos si la
selección resultante supera 20 casos.

Para cambios en observaciones de Documentos, agregar el archivo focal sin
superar 20 tests por ejecución:

```bash
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_documents.py::TestDocumentsMcpToolList \
  content/tests/views/test_mcp_documents.py::TestDocumentsMcpWorkflow -q
```

Luego ejecutar una regresión mínima de los handlers compartidos modificados y:

```bash
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python manage.py check
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python manage.py makemigrations --check --dry-run
python3 scripts/test_quality_gate.py --repo-root . \
  --report-path test-results/test-quality-audit-report.json
```

No ejecutar `manage.py migrate` desde un worktree: su `.env` enlazado apunta a
producción. Las migraciones de datos `content.0212_seed_communications_mcp` y
`content.0239_expand_communications_mcp_parity` se validan mediante tests y el
grafo de migraciones, y se aplican únicamente durante deploy. La segunda cambia
sólo la descripción: conserva token, prefijo, actividad y fecha de último uso.

## Contrato anti-deriva

Todo cambio futuro de modelo/serializer/servicio en un módulo expuesto debe, en
la misma entrega:

1. Revisar `MCP_MODEL_CONTRACTS` y clasificar cada campo agregado o cambiado.
2. Comparar handlers con la vista, serializer y servicio vigentes del panel.
3. Actualizar descripción, schema, filtros y payload real de cada tool afectada.
4. Agregar una prueba observable de éxito y otra de error cuando cambie una
   regla; actualizar este guion si cambia la operación manual.
5. Ejecutar los archivos MCP anteriores y la regresión compartida mínima.

`test_mcp_contracts.py` falla ante campos sin clasificar, nombres duplicados,
descripciones demasiado vagas o schemas que dejan de ser objetos. Esa falla es
una solicitud de revisión: nunca se resuelve ocultando el campo sin explicar por
qué queda fuera del MCP.

## Criterio de cierre

- Los nueve conectores aparecen en el registro y `tools/list` coincide con este
  inventario.
- Comunicaciones cubre las catorce operaciones vigentes y todos sus rechazos dejan
  la base consistente.
- Los MCP existentes devuelven y aceptan los campos descritos en su contrato;
  Documentos expone 22 herramientas y conserva paridad para borrar, listar la
  papelera, restaurar observaciones y operar hilos entre documentos.
- No se alteraron tokens, prefijos, estados activos ni `last_used_at` de
  conectores existentes durante la migración; una instalación nueva conserva
  la activación manual definida por la migración semilla.
- Tests focales, regresión, Django check, migraciones sin drift y quality gate
  backend focal quedan verdes y anotados en la entrega; el CI confirma los gates
  globales con las dependencias frontend instaladas.

## Ejecución de referencia — 2026-08-26

| Verificación | Resultado |
|---|---|
| Communications MCP | 15/15 tests verdes |
| Contrato de nueve conectores | 19/19 tests verdes |
| Paridad de módulos existentes | 17/17 tests verdes |
| Regresión compartida Propuestas/Contable + catálogos | 31/31 tests verdes |
| Django system check | 0 issues |
| `makemigrations --check --dry-run` | sin cambios detectados |
| Quality gate de los tres archivos MCP nuevos | 91/100, 0 errores, 0 warnings |

El gate global local puntuó 97/100, pero no pudo ejecutar sus dos puentes AST de
frontend porque este worktree backend-only no instala `frontend/node_modules`
(`@babel/parser` ausente). No fue un hallazgo de los cambios MCP; el workflow de
CI, que instala las dependencias frontend, conserva la validación global final.

## Ejecución focal — 2026-08-31

| Verificación | Resultado |
|---|---|
| Edición MCP de borradores | 19/19 tests verdes |
| Servicio y auditoría de revisiones | 14/14 tests verdes |
| Regresión `tools/list` / creación / envío | 3/3 tests verdes |
| Contratos MCP | 20/20 tests verdes |
| Django system check | 0 issues |
| `makemigrations --check --dry-run` | sin cambios detectados |
| Quality gate focal | 0 errores; warnings históricos no bloqueantes |

## Ejecución focal — 2026-09-02

| Verificación | Resultado |
|---|---|
| Acciones administrativas MCP | 20/20 tests verdes |
| Edición MCP de borradores | 19/19 tests verdes |
| Catálogo, creación, consulta y envío confirmado | 19/19 tests verdes |
| Contratos de campos y metadata (dos lotes) | 23/23 tests verdes |
| Paridad transversal de conectores | 17/17 tests verdes |
| Django system check | 0 issues |
| `makemigrations --check --dry-run` | sin cambios detectados |
| Quality gate focal | 93/100, 0 errores, 0 junk; 1 warning de infraestructura (`ruff` ausente) |

El cambio es backend/MCP y no altera modelos, relaciones, reglas de fake data ni
un flujo humano del frontend; por eso no requiere refresh de datos ni cambios en
USER_FLOW_MAP/E2E. El CI, que instala su toolchain de lint, conserva la última
validación del warning local.
