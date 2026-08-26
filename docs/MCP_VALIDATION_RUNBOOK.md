# Guion de validación y mantenimiento de MCP

Última revisión integral: 2026-08-26.

Este documento es el procedimiento repetible para validar los conectores MCP de
ProjectApp. Cubre el transporte compartido, las cinco herramientas de
Comunicaciones y la paridad de los ocho conectores preexistentes. La fuente
ejecutable del inventario está en `backend/content/views/mcp_blog.py`; la
clasificación de campos vive en `backend/content/mcp/contracts.py`.

## Invariantes

- Cada conector usa `/api/mcp/<slug>/<token>/`, un token propio almacenado sólo
  como hash, el mismo control de Origin, throttle, actor y registro de actividad.
- Un conector nuevo nace inactivo y sin token. Activarlo y emitir la URL es una
  decisión explícita del superusuario en `/panel/mcps`.
- Los handlers MCP reutilizan serializers y servicios del panel. Una regla que
  impide una acción en la interfaz también la impide por conversación.
- Ninguna descripción puede prometer un dato que el handler descarte o una
  acción que el servidor no realiza.
- `mark_message_sent` registra un hecho externo. No envía correo ni WhatsApp.
- Nunca copiar tokens reales en tickets, fixtures, logs, commits o este guion.

## Inventario vigente

| Slug | Herramientas | Alcance |
|---|---:|---|
| `blog` | 7 | Plantilla, CRUD, apertura completa y calendario editorial |
| `documents` | 14 | Carpetas, markdown, cliente/proyecto, estados y observaciones |
| `clients` | 6 | Búsqueda, detalle, CRUD y regla de huérfano transversal |
| `communications` | 5 | Hilos y registro conversacional de mensajes |
| `tasks` | 17 | Tareas, archivo, comentarios, alertas y orden del tablero |
| `accounting` | 63 | Libros, hosting, pagos/abonos, bolsillo, tarjetas y extractos |
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
  "date_from": "2026-08-01",
  "date_to": "2026-08-31",
  "q": "aprobación",
  "page": 1,
  "page_size": 20
}
```

Verificar `results`, `count`, `page` y `num_pages`; cada fila debe incluir el
cliente/proyecto, actividad, conteos y preview vigente. Repetir por separado con
`client_id` y con `project_id` para probar ambos cortes.

Errores: `status/channel/direction/message_status` fuera de catálogo, fecha no
ISO, página cero y IDs no enteros deben producir `isError=true`. Una página
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

### 4. `create_message`

Saliente de correo con referencia documental:

```json
{
  "thread_id": 30,
  "channel": "email",
  "direction": "outgoing",
  "subject": "Acta de entrega",
  "content": "Adjunto el acta para aprobación.",
  "occurred_at": "2026-08-26T15:00:00Z",
  "document_ids": [40]
}
```

Debe quedar como `draft`: crear no equivale a enviar. Un mensaje entrante de
WhatsApp queda `received`, sin asunto. `reply_to_id` sólo acepta un mensaje
previo del mismo hilo y dirección opuesta. Deben fallar: hilo cerrado, email sin
asunto, WhatsApp con asunto, contenido vacío, documento de otro cliente,
documento inexistente, respuesta de otro hilo o de igual dirección. Cada fallo
debe dejar iguales los conteos de mensajes y referencias.

### 5. `mark_message_sent`

```json
{"message_id": 50, "occurred_at": "2026-08-26T15:05:00Z"}
```

Verificar transición `draft → sent`, fecha efectiva y actor. Repetir sin
`occurred_at` para conservar la fecha registrada. Deben fallar un mensaje
entrante, uno ya enviado, uno anulado, un ID inexistente y una fecha no ISO.
Confirmar que no se creó `EmailLog` ni se invocó ningún proveedor: la herramienta
sólo registra el envío realizado por fuera.

## Revalidación de conectores existentes

| Conector | Lectura que debe comprobarse | Escritura/acción que debe comprobarse | Error representativo |
|---|---|---|---|
| Blog | `get_blog_post` devuelve JSON bilingüe, fuentes, SEO, portada y LinkedIn | crear/editar conserva esos campos | post inexistente o payload incompleto |
| Documents | resumen/detalle y filtros muestran cliente, proyecto, estados y tags | crear/editar deriva cliente desde proyecto y desvincula proyecto al cambiar cliente | proyecto ajeno, archivado o ID inválido |
| Clients | métricas incluyen documentos, ingresos, hostings y comunicaciones | CRUD usa `proposal_client_service` | un hilo impide tratar/eliminar el cliente como huérfano |
| Tasks | detalle, comentarios y alertas reflejan el modelo actual | CRUD, archivo, orden y duplicación | comentario/alerta de otra tarea |
| Accounting | detalle incluye pagos, deducciones, cuenta de cobro y período de hosting | `settle_income` y `bulk_settle_incomes` crean pagos parciales/abonos por el servicio del panel | no esperado, repetido, excedido o ID perdido |
| Diagnostics | detalle expone slug, expiración y cliente | update permite esos campos y usa el serializer actual | slug duplicado o cliente inválido |
| Proposals | detalle expone metadata comercial completa | importación y duplicación conservan nacionalidad, tipos custom y modo de contrato | JSON incompleto o transición inválida |
| LinkedIn | estado de token/post y errores de publicación | borrador, programación, edición, borrado y publicación de texto | token ausente/expirado o post no publicable |

## Verificación automatizada

Desde `backend/`, con el virtualenv del clon principal y nunca con la suite
completa. Cada comando respeta el máximo de 20 tests; iniciar otro ciclo después
de tres comandos.

```bash
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_communications.py -q

/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_contracts.py -q

/home/ryzepeck/webapps/projectapp/backend/venv/bin/python -m pytest \
  content/tests/views/test_mcp_parity_refresh.py -q
```

Luego ejecutar una regresión mínima de los handlers compartidos modificados y:

```bash
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python manage.py check
/home/ryzepeck/webapps/projectapp/backend/venv/bin/python manage.py makemigrations --check --dry-run
python3 scripts/test_quality_gate.py --repo-root . \
  --report-path test-results/test-quality-audit-report.json
```

No ejecutar `manage.py migrate` desde un worktree: su `.env` enlazado apunta a
producción. La migración de datos `content.0212_seed_communications_mcp` se
valida mediante tests/migration graph y se aplica únicamente durante deploy.

## Contrato anti-deriva

Todo cambio futuro de modelo/serializer/servicio en un módulo expuesto debe, en
la misma entrega:

1. Revisar `MCP_MODEL_CONTRACTS` y clasificar cada campo agregado o cambiado.
2. Comparar handlers con la vista, serializer y servicio vigentes del panel.
3. Actualizar descripción, schema, filtros y payload real de cada tool afectada.
4. Agregar una prueba observable de éxito y otra de error cuando cambie una
   regla; actualizar este guion si cambia la operación manual.
5. Ejecutar los tres archivos MCP anteriores y la regresión compartida mínima.

`test_mcp_contracts.py` falla ante campos sin clasificar, nombres duplicados,
descripciones demasiado vagas o schemas que dejan de ser objetos. Esa falla es
una solicitud de revisión: nunca se resuelve ocultando el campo sin explicar por
qué queda fuera del MCP.

## Criterio de cierre

- Los nueve conectores aparecen en el registro y `tools/list` coincide con este
  inventario.
- Comunicaciones cubre las cinco operaciones mínimas y todos sus rechazos dejan
  la base consistente.
- Los MCP existentes devuelven y aceptan los campos descritos en su contrato.
- No se alteraron tokens ni estados activos de conectores existentes durante la
  migración; Comunicaciones sigue inactivo/sin token hasta activación manual.
- Tests focales, regresión, Django check, migraciones sin drift y quality gate
  backend focal quedan verdes y anotados en la entrega; el CI confirma los gates
  globales con las dependencias frontend instaladas.

## Ejecución de referencia — 2026-08-26

| Verificación | Resultado |
|---|---|
| Communications MCP | 13/13 tests verdes |
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
