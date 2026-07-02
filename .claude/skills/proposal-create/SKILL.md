---
name: proposal-create
description: "Generate a business-proposal JSON artifact from a brief. Loads the live section schema from the backend (DB-free), fills every section following the seller prompt, builds Functional Requirements and the Technical Document in depth, audits completeness, saves to proposal-artifacts/, and optionally creates the proposal in the panel."
disable-model-invocation: true
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
argument-hint: "<brief/contexto: cliente, empresa, sector, alcance, inversión, módulos, idioma>"
---

# Proposal Create — Generar el artefacto JSON de una propuesta de negocio

Reemplaza el paso manual de "copiar template+prompt al chat de Claude". Recibe el **brief**
de la propuesta en `$ARGUMENTS`, vuelca el esquema vivo de secciones desde el backend, lo
puebla siguiendo el seller prompt, **construye en profundidad los Requerimientos Funcionales y
el Detalle Técnico**, **audita la completitud**, lo guarda en `proposal-artifacts/`, y
opcionalmente crea la propuesta directamente.

> **Cómo invocar**
> - `/proposal-create Cliente: Pastelería Dulce Hogar (Bogotá, repostería artesanal). Quiere e-commerce con pagos PSE/Nequi y reportes de ventas por WhatsApp. Inversión: 6.500.000 COP. Idioma: es.`
> - El brief libre va en `$ARGUMENTS`. Mientras más contexto (sector, ciudad, alcance,
>   inversión, contacto, módulos deseados), mejor la personalización.
> - Idioma: incluir `es` o `en` en el brief; default `es`.

**Output primario:** un archivo `proposal-artifacts/<cliente>_<dd_mm_yyyy>.json` con el shape
exacto que importa el panel (`/panel/proposals/create` → pestaña JSON). La creación directa de
la propuesta es una **fase final opcional y confirmada**.

**Regla de oro (por qué existe la auditoría):** el JSON es grande y es fácil "creer que terminó"
dejando secciones a medias — sobre todo el **Detalle Técnico**, que arranca vacío y el backend
NO valida. **No reportes "terminado" hasta que la auditoría mecánica de la Fase 8 dé
`AUDIT_PASS`.**

**Fuente canónica del prompt comercial:** `backend/content/views/proposal.py` (`_seller_prompt`
dentro de `get_proposal_json_template`). Las instrucciones de las Fases 2-6 son el espejo
operativo de ese objeto — si el prompt del backend cambia, re-sincronizar este skill.

**Espejos de las reglas de trazabilidad comercial↔técnica:** las reglas de ids de items
(`item-<grupo>-<slug>`), `linked_item_ids` y la convención épica-por-tarjeta viven en 4 lugares
que deben contar la misma historia: `frontend/composables/useSellerPrompt.js`,
`frontend/composables/useTechnicalPrompt.js`, el `_seller_prompt` del backend y este skill.
Si cambias una, re-sincroniza las otras tres.

---

## Fase 0 — Setup & volcar el esquema vivo (DB-free)

Resolver paths y volcar el **esquema camelCase** de las 17 secciones. Usa
`ProposalService.get_hardcoded_defaults()` → **no consulta la DB**, así que corre tanto en la
dev machine como en el VPS sin migraciones.

```bash
REPO_ROOT="$(pwd)"
PY="$REPO_ROOT/.venv/bin/python"
MANAGE="$REPO_ROOT/backend/manage.py"
[ -x "$PY" ] || PY="$REPO_ROOT/backend/venv/bin/python"   # fallback fleet venv layout
[ -f "$MANAGE" ] || { echo "❌ No encuentro backend/manage.py — corré la skill desde la raíz del repo"; exit 1; }

# Idioma: 'en' si el brief lo pide explícitamente, si no 'es'.
LANG_CODE="es"   # ajustar a 'en' si $ARGUMENTS lo indica

mkdir -p "$REPO_ROOT/proposal-artifacts"
SCHEMA_FILE="$REPO_ROOT/proposal-artifacts/.schema_${LANG_CODE}.json"

"$PY" "$MANAGE" shell -c "
import json
from content.services.proposal_service import ProposalService
from content.serializers.proposal import SECTION_TYPE_TO_KEY
# get_hardcoded_defaults() ya devuelve un deepcopy → no re-copiar por sección.
secs = ProposalService.get_hardcoded_defaults('${LANG_CODE}')
tpl = {}
for cfg in secs:
    st = cfg['section_type']
    tpl[SECTION_TYPE_TO_KEY.get(st, st)] = cfg['content_json']
tpl['_meta'] = {
    'optional_metadata': {
        'title': '', 'client_email': '', 'client_phone': '', 'client_company': '',
        'project_type': '', 'market_type': '', 'language': '${LANG_CODE}',
        'total_investment': 0, 'currency': 'COP',
    }
}
open('${SCHEMA_FILE}', 'w').write(json.dumps(tpl, ensure_ascii=False, indent=2))
print('SCHEMA_WRITTEN', '${SCHEMA_FILE}', 'sections', len([k for k in tpl if not k.startswith('_')]))
" 2>&1 | grep -E "SCHEMA_WRITTEN|Error|Traceback" 
echo "LANG_CODE=$LANG_CODE  SCHEMA_FILE=$SCHEMA_FILE"
```

Luego **Read** `proposal-artifacts/.schema_<lang>.json` para tener a la vista el shape exacto
de cada sección (las claves que hay que poblar). Este archivo es el **scaffold** que vas a
llenar; está bajo `proposal-artifacts/` (gitignored).

Si el comando falla con `Error/Traceback`, reportá el error y detené la skill.

---

## Fase 1 — Extraer metadata del brief (`$ARGUMENTS`)

Del brief, identificar y fijar en `_meta.optional_metadata`:

- `title` — p.ej. `Propuesta de E-commerce — Dulce Hogar` (si no hay, `Propuesta — <cliente>`).
- `client_email`, `client_phone`, `client_company` — si el brief los trae.
- `project_type` — uno de los choices del modelo (website, ecommerce, webapp, landing,
  redesign, …); `market_type` — (b2b, b2c, saas, retail, services, health, …). Si no calza
  ninguno, dejar vacío (el seller lo ajusta en el panel).
- `language` — `es`/`en`.
- `total_investment` (número, sin formato) y `currency` (`COP`/`USD`).
  - **Precio 0 por defecto:** si el brief NO da precio, `total_investment = 0`,
    `investment.totalInvestment = ''`, y el ROI (Fase 3) va por **metodología/productividad**,
    no anclado a precio. El seller fija el monto luego en el panel.

Además fijar en la sección `general`: `clientName` (nombre del cliente/empresa) y
`proposalTitle` = `title`.

**CRITICAL_metadata:** NO agregar claves a `_meta.optional_metadata` fuera de las listadas.
**Nunca** agregar `expires_at` — la expiración la fija el backend desde el default del panel.

---

## Fase 2 — Auto-selección de módulos (`functionalRequirements`)

Escanear el brief y, para cada módulo en `functionalRequirements.additionalModules` del
scaffold, decidir si los requerimientos describen esa capacidad. Mapa de detección:

| Keyword en el brief | module id |
|---|---|
| DIAN, facturación electrónica, e-invoicing, Siigo, Alegra | `integration_electronic_invoicing` |
| PSE, Wompi, PayU, ePayco, Nequi, Daviplata, Bancolombia | `integration_regional_payments` |
| Stripe, PayPal, pagos internacionales / cross-border | `integration_international_payments` |
| PWA, app instalable, offline, push notifications | `pwa_module` |
| IA, chatbot, asistentes, automatización inteligente | `ai_module` |
| Meta/Facebook Ads, Google Ads, CAPI, ROAS, Enhanced Conversions | `integration_conversion_tracking` |
| Reportes/alertas por email/WhatsApp, alertas de ventas/stock | `reports_alerts_module` |
| Email marketing, Mailchimp, Brevo, SendGrid, captura de leads | `email_marketing_module` |
| Multi-idioma, i18n, varios países, precios por país | `i18n_module` |
| Chat en vivo, soporte en tiempo real | `live_chat_module` |
| Dark mode, cambio de tema | `dark_mode_module` |
| Verificación biométrica, KYC, reconocimiento facial, validación de cédula, antifraude | `biometric_verification_module` |
| QR, código QR, menú digital, código de mesa, link tree | `qr_generator_module` |
| Generación de contenido / blog AI, calendario editorial, programación de publicaciones | `content_generator_module` |

> Espejo de `_seller_prompt.CRITICAL_additionalModules_autoselect` (`proposal.py:1343-1382`) —
> si el backend agrega módulos o keywords, re-sincronizar esta tabla.

Para cada módulo que matchee: fijar **`default_selected: true` Y `selected: true`**, y adaptar
su `description` y reordenar/reescribir sus `items` para reflejar la terminología y proveedores
del brief (p.ej. si pide "reportes por WhatsApp", el item de WhatsApp lidera la lista). Si no
hay match, dejar `default_selected: false`. **No inventar matches.**

Los módulos que marques `selected` aquí definen el **ALCANCE**: las Fases 4 (Requerimientos
Funcionales) y 5 (Detalle Técnico) deben reflejarlos de forma coherente.

**CRITICAL_functionalRequirements:** NO remover ni reordenar grupos (`groups`) ni módulos
(`additionalModules`); NO mover módulos entre arrays; NO cambiar `id`, `icon`, `price_percent`,
`is_invite` ni su posición. Solo modificar contenido (title/description/items) y marcar
selección. El seller borra manualmente lo que sobre después de crear la propuesta. Si el
scaffold trae anotaciones `_do_not_remove`, son recordatorios — podés dejarlas o quitarlas, no
afectan el import.

---

## Fase 3 — Investigar y construir la proyección ROI (`roiProjection`)

La sección ancla el valor del negocio y va **antes** de `investment` en la narrativa.

- **EXACTAMENTE 3 KPIs** en `kpis` (la UI renderiza 3 cards; con más/menos se rompe). Elegir 3
  que empujen la decisión de compra, mezclando ángulos: (1) urgencia/contexto de mercado,
  (2) magnitud de la oportunidad/dolor, (3) dolor directo que esta inversión resuelve.
- **Sourcing (HARD RULE — no inventar):** cada KPI lleva `source` con un reporte/estudio/ley
  real + organización + año, **en español**, priorizando **Colombia / LATAM** (DANE, Banco de la
  República, MinTIC, Confecámaras, superintendencias, ministerios sectoriales, gremios como
  Fenalco/ANDI/Camacol, Cámaras de Comercio, universidades con observatorios, medios económicos
  citando un estudio, CEPAL/BID, leyes/decretos). Verificá las 3 fuentes **en paralelo** con
  **WebSearch/WebFetch** (una sola tanda): si pegando el `source` en Google no aparece nada que
  respalde la cifra, no es válido. **No inventes cifras ni fuentes:** sin fuente real con año NO
  es un KPI — es una promesa; descártalo. Prohibido "Benchmark sectorial", "Estudio interno",
  "Datos del mercado". Internacional solo si no existe equivalente local, máximo 1 vez por
  bloque, marcando "referente internacional aplicable".
- **Labels en lenguaje llano** (no MRR/LTV/CAC/churn/conv.): "De cada 100 visitas, 3 reservan
  clase" en vez de "3% de conversión".
- **`scenarios`: EXACTAMENTE 3** con nombres `conservative`/`realistic`/`optimistic` (labels
  Conservador/Realista/Optimista en ES). Cada uno 3-5 métricas con labels **paralelos** entre
  escenarios (comparables fila a fila). Marcar **exactamente UNA** métrica por escenario con
  `emphasis=true` (la más impactante, típicamente ingreso anual proyectado).
- **Mostrar el trabajo** (obligatorio): `methodology` (nivel sección, 2-3 frases en lenguaje
  llano: base verificable + supuesto clave + proyección a 12 meses); `assumptions` (array por
  escenario, 2-4 palancas que lo definen, paralelas entre escenarios); `basis` (string por
  métrica con la aritmética, p.ej. "≈ 6.500 clientes × $43.000 ticket promedio"; obligatorio en
  toda métrica `emphasis=true`). Todo debe cuadrar con `total_investment`.

---

## Fase 4 — Requerimientos Funcionales (construcción profunda)

Sección `functionalRequirements` — **acá se cierra el alcance funcional**. El cliente la escanea
para entender exactamente qué recibe. Dedicale esfuerzo: estructura escaneable (espíritu
`/human`: listas claras, orden lógico), lenguaje **no técnico**, y nivel de detalle que **cierre
cualquier gap de interpretación**.

Shape: `{index, title, intro, groups[], additionalModules[]}`. Cada `groups[].items[]` y
`additionalModules[].items[]` es un objeto **`{icon, name, description, id}`** (usa **`name`**,
no `title`; los 4 campos son obligatorios). Render real: cards de resumen → modal con grilla de
items, y cada item con requerimientos técnicos enlazados muestra "Ver requerimientos (N)".

> **`id` estable del item (obligatorio, regla estricta):** formato
> `item-<id_del_grupo>-<slug-del-nombre>`. Algoritmo del slug (aplicarlo EXACTAMENTE): minúsculas;
> tildes/diéresis eliminadas y ñ→n; toda secuencia fuera de `[a-z0-9]` → UN solo guion; sin
> guiones al inicio/fin. Ej.: "Registro de usuario" en `views` → `item-views-registro-de-usuario`.
> **Unicidad determinista** en toda la sección (groups + additionalModules): en colisión, la
> PRIMERA aparición en orden de documento conserva el slug base; las siguientes reciben `-2`,
> `-3`. **Estabilidad:** al editar una propuesta existente NUNCA regenerar un id ya asignado,
> aunque el `name` cambie (id≠slug(name) es un estado válido). Estos ids son el contrato con la
> Fase 5: los requerimientos técnicos los referencian vía `linked_item_ids`. Los ids dependen del
> idioma de la propuesta — no reutilizarlos entre versiones ES/EN.

### 4a — Definir el flujo lógico del usuario
Antes de redactar, mapeá el **recorrido de punta a punta** de un usuario de este proyecto/sector
(p.ej. e-commerce: descubre → explora catálogo → ve producto → agrega al carrito → paga →
recibe confirmación → gestiona su cuenta). Ese recorrido define el ORDEN de los items.

### 4b — Redactar cada grupo base (completo, ordenado, no técnico)
Para CADA uno de los 7 grupos base, redactá sus `items` completos, **en orden lógico** (el
lector escanea y entiende el paso a paso), 1 item = 1 pantalla/elemento/métrica. Cada item con un
`icon` (emoji) que señale visualmente de qué se trata, un `name` corto (**texto plano, sin HTML**),
y una `description` **rica, en DOS párrafos** separados por `<br><br>`:

> **Patrón de `description` (obligatorio en items de TODOS los grupos y de los módulos `selected`):**
> 1. **Párrafo 1 — describí el elemento** con detalle (qué es, qué muestra, para qué sirve). No
>    telegráfico: una descripción que el cliente entienda sin adivinar.
> 2. **Párrafo 2 — arrancá con «El usuario podrá …»** y enumerá lo que puede hacer ahí, **sin
>    repetir** literalmente lo del párrafo 1 (agrega, no duplica).
> 3. Resaltá **1-3 palabras o frases clave por párrafo con `<b>…</b>`** (nunca párrafos enteros).
>
> Encoding: usá `<b>…</b>` para negrita y `<br><br>` para separar párrafos — la web lo renderiza
> nativo y el PDF los honra. **NO** uses markdown (`**`) ni `<p>` (no se renderizan). El `name`
> queda en texto plano. Ejemplo:
> `"El <b>dashboard comercial</b> es la pantalla de inicio: muestra el estado del negocio de un
> vistazo — oportunidades activas, valor del pipeline y alertas del día.<br><br>El usuario podrá
> ver sus <b>indicadores en tiempo real</b>, detectar qué prospecto está caliente y entrar directo
> a lo que necesita atención hoy."`

| group id | qué cubrir | orden lógico |
|---|---|---|
| `views` 🖥️ | cada pantalla/sección del sitio | **orden de navegación real** del usuario |
| `components` 🧩 | elementos reutilizables (header, footer, tarjetas, buscador, formularios) | de lo global a lo específico |
| `features` ⚙️ | comportamientos/funcionalidades interactivas | por importancia / momento de uso |
| `admin_module` 🛠️ | gestión desde el panel (contenido, pedidos, usuarios) | flujo de trabajo del admin |
| `analytics_dashboard` 📊 | métricas **concretas del sector** (no genéricas) | de la métrica más accionable a la de contexto |
| `kpi_dashboard_module` 📊 | KPIs en tiempo real, gráficos, alertas | del KPI principal a los de apoyo |
| `manual_module` 📘 | manual/wiki interactivo no técnico | en el orden en que el usuario aprende |

- **Tailored al brief — no dejar los items genéricos del default.** Adaptá nombres,
  descripciones y orden al sector, ciudad y alcance del cliente. (La auditoría de la Fase 8
  marca `WARN` si un grupo quedó idéntico al default.)
- Sé preciso y completo: si una vista tiene sub-secciones relevantes, nómbralas en la
  `description`. La meta es que el cliente NO tenga que adivinar qué incluye.

### 4c — Adaptar los módulos auto-seleccionados (Fase 2)
Para cada módulo con `selected: true`, reescribí su `description` e `items` con la terminología y
proveedores exactos del brief (Wompi, PSE, DIAN, WhatsApp, etc.).

**Invariantes:** NO borrar/reordenar `groups` ni `additionalModules`; los `items` SÍ se redactan
y ordenan libremente. item usa `name` (no `title`).

---

## Fase 5 — Detalle Técnico (construcción profunda)

Sección `technicalDocument`. **Arranca como placeholder VACÍO** y el backend no la valida → es
la causa #1 del "dijo que terminó pero faltó". **Llenala de verdad**, definiendo el paso a paso
lógico y **conectándola con los Requerimientos Funcionales** (Fase 4) y los módulos seleccionados
(Fase 2). El render es casi todo **tablas** + las épicas como tabla con modal.

Shape: `{purpose, stack[], architecture{summary,patterns[],diagramNote}, dataModel{summary,
relationships,entities[]}, growthReadiness{summary,strategies[]}, epics[], apiSummary,
apiDomains[], integrations{included[],excluded[],notes}, environments[], environmentsNote,
security[], performanceQuality{metrics[],practices[]}, backupsNote,
quality{dimensions[],testTypes[],criticalFlowsNote}, decisions[]}`.

### 5a — Propósito y stack
- `purpose`: 1-2 párrafos sobre qué resuelve el proyecto técnicamente.
- `stack[]`: items `{layer, technology, rationale}`. Stack estándar de proyectos de cliente:
  Cliente/SSR (React + Next.js + Tailwind — App Router, componentes por sección, Zustand para
  estado global, hooks personalizados), API (Django 5 + DRF), Datos (MySQL 8), Tareas/colas
  (Huey), Infra (VPS + Nginx + Gunicorn). **No mencionar Redis, AWS, S3 ni servicios cloud** que
  no formen parte del proyecto real (regla del prompt técnico).

### 5b — Épicas y flujos (el núcleo) — convención épica-por-tarjeta (REGLA ESTRICTA)
`epics[]` espeja la sección `functionalRequirements` de la Fase 4: el cliente navega de cada
tarjeta comercial a su épica técnica, y cada item comercial a sus requerimientos. Cada épica:
`{epicKey, title, description, linked_module_ids[], requirements[]}`.
- **Exactamente UNA épica por tarjeta comercial:** `views`, `components`, `features`, cada
  módulo base (`admin_module`, `analytics_dashboard`, `kpi_dashboard_module`, `manual_module`) y
  cada módulo de `additionalModules` **contratado** (`selected`/`default_selected: true`).
  **PROHIBIDO crear épicas para módulos no contratados** (una épica sin links se muestra SIEMPRE
  en el modo técnico y le enseñaría al cliente alcance que no compró). Se permite una épica
  transversal extra al final (infraestructura/seguridad/calidad) si hace falta.
- `epicKey`: **id comercial EXACTO Y VERBATIM**, guiones bajos incluidos (`views`,
  `admin_module`, `pwa_module` — nunca `admin-module`). Único. La épica transversal usa un
  slug kebab propio (p.ej. `base-tecnica`).
- **Orden de `epics[]` = orden de las tarjetas comerciales** (groups en su orden, luego módulos
  contratados en su orden; transversal al final).
- `linked_module_ids` de la épica: **OBLIGATORIO** `["module-<id>"]` (canónico exacto) en épicas
  de módulos de `additionalModules`; omitido o `[]` en épicas de tarjetas base (alcance base).
- `requirements[]`: cada uno `{flowKey, title, description, configuration, usageFlow, priority,
  linked_module_ids[], linked_item_ids[]}`:
  - `flowKey`: **kebab-case, único GLOBAL** entre todas las épicas (p.ej. `flow-checkout-pse`).
  - `title`: **obligatorio**.
  - `usageFlow`: el **paso a paso** del usuario ("Carrito → datos de envío → pasarela → confirmación").
  - `priority`: `critical` | `high` | `medium` | `low`.
  - `linked_module_ids`: solo formatos canónicos `group-<id>` / `module-<id>`, y **consistente
    con el de su épica** (nunca apuntar a un módulo distinto del de la épica que lo contiene).
    **Un requisito que dependa de un módulo opcional debe linkearlo** para que solo aparezca si
    el cliente lo selecciona.
  - `linked_item_ids`: los `id` EXACTOS (carácter por carácter, de la Fase 4) de los items
    comerciales que este requerimiento implementa. **Cobertura OBLIGATORIA: todo item comercial
    de grupos visibles y módulos contratados DEBE quedar enlazado por AL MENOS un requerimiento**
    — alimenta el modal "Ver requerimientos" y el PDF. Solo requerimientos transversales pueden
    omitirlo o dejarlo `[]` (en cualquier épica).

### 5c — Modelo de datos
`dataModel`: `summary`, `relationships` (texto), `entities[]` con `{name, description, keyFields}`.
Derivá las entidades de las épicas/flujos (p.ej. Product, Order, User…) — que sean coherentes con
lo prometido en la Fase 4.

### 5d — Arquitectura, API e integraciones
- `architecture`: `{summary, patterns[]({component,pattern,description}), diagramNote}`.
- `apiSummary` + `apiDomains[]` (`{domain, summary}`).
- `integrations`: `included[]` (`{service, provider, connection, dataExchange, accountOwner}`) =
  los proveedores reales del brief (Wompi/PSE/DIAN/etc.); `excluded[]` (`{service, reason,
  availability}`) = lo fuera de alcance + cuándo se haría; `notes`.

### 5e — Operación y calidad
Completá `environments[]`, `environmentsNote`, `security[]`, `performanceQuality{metrics[],
practices[]}`, `backupsNote`, `quality{dimensions[],testTypes[],criticalFlowsNote}`,
`decisions[]` (`{decision, alternative, reason}`), `growthReadiness{summary,strategies[]}`.

**Reglas duras:** NO dejar `technicalDocument` como el placeholder vacío; `epicKey` = id
comercial verbatim (guiones bajos permitidos) y único; `flowKey` kebab-case y único global;
una épica por tarjeta contratada y ninguna de módulos no contratados; todo item comercial
cubierto por ≥1 requerimiento vía `linked_item_ids`; mantener consistencia con el alcance de la
Fase 4 y los módulos seleccionados (Fase 2).

---

## Fase 6 — Redactar el resto de las secciones

Poblar el `content_json` de las secciones restantes respetando su shape del scaffold: `general`,
`executiveSummary`, `contextDiagnostic`, `conversionStrategy`, `designUX`, `creativeSupport`,
`valueAddedModules`, `developmentStages`, `processMethodology`, `investment`, `timeline`,
`proposalSummary`, `finalNote`, `nextSteps`. (ROI ya se hizo en la Fase 3; FR y técnico en 4-5.)

- **Tono:** orientado a negocio pero cercano, sin jerga técnica, hablándole al decisor.
- **Personalización:** mencionar siempre cliente y empresa; referenciar sector/mercado; incluir
  2-3 métricas del sector con fuente.
- **Narrativa que enamora (sin inventar):** donde aplique (`executiveSummary`, `conversionStrategy`,
  `designUX`, `finalNote`, y `growthReadiness` del técnico) transmití que el producto es
  **escalable** y dejá al cliente **imaginar/visualizar lo que podrá hacer con él** — listá
  capacidades concretas y el camino de crecimiento. **Ancla todo al alcance real**: nunca inventes
  features, cifras, integraciones ni clientes/casos que no existan. Si algo es futuro, decí
  explícitamente que es una fase siguiente.
- **Investment anchoring:** presentar valor/ROI antes del precio; enmarcar como decisión de
  negocio; comparar con el costo de no actuar. En `investment`: `totalInvestment` como string
  formateado (p.ej. `$6.500.000 COP`) y `currency` consistente con `_meta`.
- **Bold (`<b>…</b>`):** resaltar palabras/frases clave (beneficios, métricas, verbos de acción)
  — nunca párrafos enteros. Obligatorio en: `executiveSummary` (paragraphs, highlights),
  `contextDiagnostic` (paragraphs, issues, opportunity), `conversionStrategy` (intro, bullets,
  result), `designUX` (paragraphs, focusItems, objective), `creativeSupport` (paragraphs,
  includes, closing), y las **descripciones de items de `functionalRequirements`** (ver Fase 4).
- **Bilingüe:** si `language=en`, redactar en inglés (no traducción literal del español).

---

## Fase 7 — Ensamblar y escribir el artefacto (borrador)

Construir el artefacto final (shape de template: secciones camelCase en la raíz + `_meta`) y
**escribirlo con Write** en `proposal-artifacts/<client-slug>_<dd_mm_yyyy>.json`. No incluir
`_seller_prompt` (lo ignora el import y solo lo infla); conservar `_meta`.

Obtener el nombre con:

```bash
CLIENT_NAME="<clientName tal como quedó en general.clientName>"   # completar
CLIENT_SLUG="$(echo "$CLIENT_NAME" | iconv -t ascii//TRANSLIT 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
[ -n "$CLIENT_SLUG" ] || CLIENT_SLUG="propuesta"
echo "ARTIFACT=$(pwd)/proposal-artifacts/${CLIENT_SLUG}_$(date +%d_%m_%Y).json"
```

Se llama "borrador" porque la Fase 8 lo audita y, si falla, lo corregís **en el mismo archivo**
antes de darlo por terminado.

---

## Fase 8 — Auditoría de completitud (GATE — no saltar)

Dos capas. **No reportes "terminado" hasta `AUDIT_PASS`.**

### 8a — Auditoría mecánica (determinista, DB-free)
Corre sobre el archivo escrito. No depende de que el modelo "diga" que terminó.

```bash
PY="$(pwd)/.venv/bin/python"; [ -x "$PY" ] || PY="$(pwd)/backend/venv/bin/python"
MANAGE="$(pwd)/backend/manage.py"
ARTIFACT="$(pwd)/proposal-artifacts/<archivo>.json"   # completar con el nombre real

"$PY" "$MANAGE" shell -c "
import json, re
from content.services.proposal_service import ProposalService
from content.serializers.proposal import SECTION_TYPE_TO_KEY

art = json.load(open('${ARTIFACT}'))
lang = ((art.get('_meta') or {}).get('optional_metadata') or {}).get('language') or 'es'
secs = ProposalService.get_hardcoded_defaults(lang)
defaults = {SECTION_TYPE_TO_KEY.get(c['section_type'], c['section_type']): c['content_json'] for c in secs}

fails, warns = [], []
def FAIL(loc, msg): fails.append((loc, msg))
def WARN(loc, msg): warns.append((loc, msg))
kebab = re.compile(r'[a-z0-9]+(-[a-z0-9]+)*')
def is_kebab(s): return bool(kebab.fullmatch(s))
# epicKey espeja el id comercial verbatim -> permite guiones bajos ademas de guiones
epickey_re = re.compile(r'[a-z0-9_]+([-_][a-z0-9_]+)*')
def is_epic_key(s): return bool(epickey_re.fullmatch(s))
item_id_re = re.compile(r'item-[a-z0-9_-]+')
def is_item_id(s): return bool(item_id_re.fullmatch(s))

# 1) las 17 secciones presentes
for k in defaults:
    if k not in art: FAIL('sections', 'falta seccion: ' + k)

# 2) ROI
roi = art.get('roiProjection') or {}
kpis = roi.get('kpis') or []
if len(kpis) != 3: FAIL('roi.kpis', str(len(kpis)) + ' (deben ser 3)')
BAD = {'', 'benchmark sectorial', 'estudio interno', 'datos del mercado', 'fuente', 'todo', 'tbd', 'n/a', '-'}
for i, k in enumerate(kpis):
    s = (k.get('source') or '').strip()
    if not s or s.lower() in BAD: FAIL('roi.kpis[%d].source' % i, 'placeholder/vacio: %r' % s)
    elif not any(c.isdigit() for c in s): WARN('roi.kpis[%d].source' % i, 'sin anio visible: %r' % s)
scen = roi.get('scenarios') or []
if len(scen) != 3: FAIL('roi.scenarios', str(len(scen)) + ' (deben ser 3)')
for i, sc in enumerate(scen):
    emph = [m for m in (sc.get('metrics') or []) if m.get('emphasis')]
    if len(emph) != 1: FAIL('roi.scenarios[%d]' % i, '%d metricas emphasis (debe ser 1)' % len(emph))
if not (roi.get('methodology') or '').strip(): FAIL('roi.methodology', 'vacio')

# 3) functionalRequirements
fr = art.get('functionalRequirements') or {}
frd = defaults.get('functionalRequirements') or {}
def_ids = [g.get('id') for g in (frd.get('groups') or [])]
groups = fr.get('groups') or []
modules = fr.get('additionalModules') or []
ids = [g.get('id') for g in groups]
if ids[:len(def_ids)] != def_ids: FAIL('fr.groups', 'grupos base alterados/reordenados: %s' % ids)
all_item_ids, sel_item_ids = set(), set()
for g in groups + modules:
    gid = g.get('id')
    is_module = g in modules
    is_selected = bool(g.get('selected') or g.get('default_selected'))
    for j, it in enumerate(g.get('items') or []):
        iid = (it.get('id') or '').strip()
        if not iid: FAIL('fr.%s.items[%d].id' % (gid, j), 'item sin id')
        elif not is_item_id(iid): FAIL('fr.%s.items[%d].id' % (gid, j), 'formato invalido: %r' % iid)
        elif iid in all_item_ids: FAIL('fr.%s.items[%d].id' % (gid, j), 'id duplicado: %r' % iid)
        else:
            all_item_ids.add(iid)
            # cobertura exigible: items de grupos visibles + modulos contratados
            if (not is_module and g.get('is_visible') is not False) or (is_module and is_selected):
                sel_item_ids.add(iid)
for g in groups:
    gid = g.get('id'); items = g.get('items') or []
    if len(items) < 2: FAIL('fr.%s.items' % gid, 'solo %d items' % len(items))
    for j, it in enumerate(items):
        if not ((it.get('name') or '').strip() and (it.get('description') or '').strip()):
            FAIL('fr.%s.items[%d]' % (gid, j), 'name/description vacio')
    gd = next((x for x in (frd.get('groups') or []) if x.get('id') == gid), None)
    if gd is not None and g.get('items') == gd.get('items'):
        WARN('fr.%s' % gid, 'items identicos al default (no personalizado)')
# ids de modulos NO contratados (una epica de estos seria alcance no comprado)
unselected_module_ids = {
    m.get('id') for m in modules
    if not (m.get('selected') or m.get('default_selected'))
}

# 4) technicalDocument
td = art.get('technicalDocument') or {}
purpose = (td.get('purpose') or '').strip()
epics = td.get('epics') or []
if not purpose and not epics:
    FAIL('technicalDocument', 'vacio (sin purpose ni epics) - placeholder sin llenar')
else:
    if not purpose: WARN('technicalDocument.purpose', 'vacio')
    if not epics: FAIL('technicalDocument.epics', 'sin epicas')
    se, sf, linked_items = set(), set(), set()
    for e in epics:
        ek = (e.get('epicKey') or '').strip()
        if ek and not is_epic_key(ek): FAIL('epicKey ' + ek, 'formato invalido (minusculas, numeros, - y _)')
        if ek and ek in se: FAIL('epicKey ' + ek, 'duplicado')
        se.add(ek)
        if ek in unselected_module_ids:
            FAIL('epicKey ' + ek, 'epica de modulo NO contratado (alcance no comprado)')
        elif ek and ek.endswith('_module') and ek not in {g.get('id') for g in groups + modules}:
            WARN('epicKey ' + ek, 'no coincide con ningun id comercial')
        epic_mods = set(e.get('linked_module_ids') or [])
        if ek in {m.get('id') for m in modules} and 'module-%s' % ek not in epic_mods:
            FAIL('epic ' + ek, 'epica de modulo sin linked_module_ids canonico ["module-%s"]' % ek)
        reqs = e.get('requirements') or []
        if not reqs: WARN('epic ' + (ek or '?'), 'sin requirements')
        for r in reqs:
            fk = (r.get('flowKey') or '').strip()
            if fk and not is_kebab(fk): FAIL('flowKey ' + fk, 'no es kebab-case')
            if fk and fk in sf: FAIL('flowKey ' + fk, 'duplicado global')
            sf.add(fk)
            other = any((r.get(x) or '').strip() for x in ('description', 'configuration', 'usageFlow'))
            if other and not (r.get('title') or '').strip(): FAIL('requirement ' + (fk or '?'), 'title faltante')
            for iid in (r.get('linked_item_ids') or []):
                iid = (iid or '').strip()
                if iid and iid not in all_item_ids:
                    FAIL('req %s.linked_item_ids' % (fk or '?'), 'id inexistente en fr: %r' % iid)
                elif iid:
                    linked_items.add(iid)
            req_mods = set(r.get('linked_module_ids') or [])
            if epic_mods and req_mods and not req_mods <= epic_mods:
                FAIL('req %s.linked_module_ids' % (fk or '?'), 'apunta a modulo distinto del de su epica')
    # cobertura obligatoria: todo item exigible enlazado por >=1 requerimiento
    uncovered = sorted(sel_item_ids - linked_items)
    for iid in uncovered:
        FAIL('trazabilidad', 'item sin requerimiento tecnico enlazado: %s' % iid)
    # una epica por tarjeta contratada
    expected_epics = [g.get('id') for g in groups if g.get('is_visible') is not False]
    expected_epics += [m.get('id') for m in modules if m.get('selected') or m.get('default_selected')]
    for ek in expected_epics:
        if ek not in se: FAIL('epics', 'falta epica de la tarjeta comercial: %s' % ek)

print('AUDIT_FAIL', len(fails)) if fails else print('AUDIT_PASS')
for loc, msg in fails: print('  FAIL', loc + ':', msg)
for loc, msg in warns: print('  WARN', loc + ':', msg)
" 2>&1 | grep -E "AUDIT_PASS|AUDIT_FAIL|FAIL|WARN|Error|Traceback"
```

- Si imprime **`AUDIT_FAIL`** → leé cada `FAIL`, volvé a la fase correspondiente, **corregí el
  archivo** (Write/Edit) y **re-corré la auditoría**. Repetir hasta `AUDIT_PASS`.
- Los `WARN` (p.ej. grupo FR idéntico al default) no bloquean, pero revisalos: casi siempre
  conviene personalizar.

### 8b — Revisión semántica (modelo)
Con `AUDIT_PASS` mecánico, además:
- **ROI:** re-verificá que las 3 `source` existen de verdad (WebSearch) — **ninguna inventada**.
- **FR:** releé los grupos como si fueras el cliente: ¿se lee como un flujo lógico y cierra el
  alcance sin ambigüedad?
- **Técnico:** ¿las épicas/flujos enganchan con los módulos seleccionados (`linked_module_ids`) y
  son coherentes con lo prometido en la Fase 4?

### 8c — Validar JSON y limpiar
```bash
PY="$(pwd)/.venv/bin/python"; [ -x "$PY" ] || PY="$(pwd)/backend/venv/bin/python"
"$PY" -m json.tool "proposal-artifacts/<archivo>.json" >/dev/null \
  && echo "✅ JSON válido" || echo "❌ JSON inválido"
rm -f proposal-artifacts/.schema_*.json   # limpiar el/los scaffold(s) (gitignored)
```

Presentar al usuario un resumen breve: cliente, inversión, módulos auto-seleccionados, los 3
KPIs con sus fuentes, # de épicas/flujos del técnico, resultado de auditoría, y la ruta del
archivo.

---

## Fase 9 — Importación opcional (gated)

Preguntar al usuario: **¿Creo la propuesta ahora, o preferís subir el archivo en el panel?**

- **Opción A (manual, recomendada por defecto):** subir
  `proposal-artifacts/<archivo>.json` en `/panel/proposals/create` → pestaña **JSON** →
  "Subir archivo" → revisar y crear. Usa el importador existente (selector de cliente, merge de
  defaults, validaciones). El import apunta a la DB del entorno donde está el panel.

- **Opción B (directa, solo si el usuario confirma):** crear la propuesta vía `manage.py shell`,
  reusando el view real `create_proposal_from_json` (misma lógica que el panel: cliente FK,
  `expires_at` default, merge de `functionalRequirements`, changelog).
  **Requiere correr donde la DB real es alcanzable** (VPS staging/prod con `settings_prod` +
  MySQL) y que exista un usuario staff. **No** crear contra la SQLite dev sin migrar.

```bash
REPO_ROOT="$(pwd)"
PY="$REPO_ROOT/.venv/bin/python"; [ -x "$PY" ] || PY="$REPO_ROOT/backend/venv/bin/python"
MANAGE="$REPO_ROOT/backend/manage.py"
ARTIFACT="$REPO_ROOT/proposal-artifacts/<archivo>.json"   # completar con el nombre real

# Resolver el settings de prod para NO pegarle a la SQLite dev (igual que deploy-and-check):
# 1º del unit systemd de gunicorn, 2º de backend/.env; si no resuelve, manage.py usa *_dev.
SVC="projectapp"   # ajustar al gunicorn_service del proyecto si difiere
DJANGO_SETTINGS_MODULE=$(systemctl show "$SVC" -p Environment --value 2>/dev/null \
    | tr ' ' '\n' | grep '^DJANGO_SETTINGS_MODULE=' | head -1 | cut -d= -f2-)
[ -z "$DJANGO_SETTINGS_MODULE" ] && DJANGO_SETTINGS_MODULE=$(grep -hE '^DJANGO_SETTINGS_MODULE=' \
    "$REPO_ROOT/backend/.env" 2>/dev/null | head -1 | cut -d= -f2-)
export DJANGO_SETTINGS_MODULE
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-<unset → manage.py default *_dev>}"

"$PY" "$MANAGE" shell -c "
import json
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from content.views.proposal import create_proposal_from_json

art = json.load(open('${ARTIFACT}'))
meta = (art.get('_meta') or {}).get('optional_metadata', {})

# Reproducir la transformación del panel (create.vue:handleJsonSubmit):
sections = {k: v for k, v in art.items() if k not in ('_meta', '_seller_prompt')}
client_name = (sections.get('general') or {}).get('clientName', '') or meta.get('client_name', '')
inv = sections.get('investment') or {}
title = meta.get('title') or (sections.get('general') or {}).get('proposalTitle') or ('Propuesta — ' + client_name)

payload = {
    'title': title,
    'client_name': client_name,
    'client_email': meta.get('client_email', ''),
    'client_phone': meta.get('client_phone', ''),
    'client_company': meta.get('client_company', ''),
    'project_type': meta.get('project_type', ''),
    'market_type': meta.get('market_type', ''),
    'language': meta.get('language', 'es'),
    'total_investment': meta.get('total_investment', 0) or 0,
    'currency': meta.get('currency', inv.get('currency', 'COP')),
    'reminder_days': 10, 'urgency_reminder_days': 15, 'discount_percent': 0,
    'sections': sections,
}

staff = get_user_model().objects.filter(is_staff=True).first()
if not staff:
    print('NO_STAFF_USER — no puedo autenticar el import'); raise SystemExit(1)
req = APIRequestFactory().post('/_/', payload, format='json')
force_authenticate(req, user=staff)
resp = create_proposal_from_json(req)
print('STATUS', resp.status_code)
if resp.status_code in (200, 201):
    d = resp.data
    print('ID', d.get('id'), 'UUID', d.get('uuid'), 'SLUG', d.get('slug'))
    print('PUBLIC_URL', d.get('public_url') or '')
else:
    print('ERROR', json.dumps(resp.data, ensure_ascii=False)[:800])
" 2>&1 | grep -E "STATUS|ID |PUBLIC_URL|ERROR|NO_STAFF_USER|Traceback"
```

Reportar `id`/`uuid`/`slug` + URL pública. El artefacto queda en `proposal-artifacts/` como
respaldo (sirve para borrar/recrear la propuesta con el mismo JSON).

---

## Output final

Reportar siguiendo [[_output-protocol]]. Plantilla específica de `/proposal-create`:

```markdown
🟢 proposal-create OK — <cliente> (<archivo>.json)

| Dimensión | Estado | Detalle |
|---|---|---|
| Fase 0 — Esquema vivo | ✅ | get_hardcoded_defaults(<lang>) → 17 secciones |
| Fase 1 — Metadata | ✅ | <cliente>, <project_type>/<market_type>, <inversión> <moneda> |
| Fase 2 — Módulos | ✅ | auto-seleccionados: <ids o "ninguno"> |
| Fase 3 — ROI | ✅ | 3 KPIs con fuente (org+año) verificada, 3 escenarios |
| Fase 4 — Req. Funcionales | ✅ | 7 grupos personalizados, items en orden lógico |
| Fase 5 — Detalle Técnico | ✅ | <N> épicas / <M> flujos, dataModel, integraciones |
| Fase 6 — Resto secciones | ✅ | secciones pobladas, bold aplicado |
| Fase 8 — Auditoría | ✅ | AUDIT_PASS (0 FAIL, <w> WARN) |
| Fase 9 — Import | ⏭️/✅ | manual (panel) / creada id=<id> |

## Next steps
- (manual, panel) Subir `proposal-artifacts/<archivo>.json` en /panel/proposals/create → JSON
- o (VPS) correr el snippet de import de la Fase 9 contra la DB real
```

Si la auditoría de la Fase 8 reporta `AUDIT_FAIL`, **NO** reportes "terminado": volvé a la fase
indicada por cada `FAIL`, corregí el archivo y re-auditá hasta `AUDIT_PASS`. Marcá la fila de
auditoría 🔴 solo si quedó algún `FAIL` sin resolver.
