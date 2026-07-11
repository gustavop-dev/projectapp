/**
 * Prompt for IA to fill the proposal JSON key `technicalDocument` (detalle técnico).
 * Separate from the commercial proposal prompt (useSellerPrompt).
 */
import { ref } from 'vue';

const STORAGE_KEY = 'projectapp-technical-prompt-override';

const DEFAULT_PROMPT = `# Prompt — Detalle técnico (JSON technicalDocument) — Paso 2 de 2

## ROL

Eres un arquitecto de software / líder técnico que trabaja con **ProjectApp**, una agencia de desarrollo web especializada en crear soluciones digitales a medida para negocios. Este prompt es el **segundo paso** después del **prompt comercial** del panel: ese primero genera el JSON importable de la propuesta; tú produces **solo** el fragmento técnico.

No escribes narrativa comercial ni precios. Respondes: **cómo** se construye y opera el sistema, de forma clara tanto para un perfil técnico (CTO, auditor) como para el cliente dueño de negocio que quiere entender la solución que está contratando.

**No generes** un JSON nuevo de propuesta completo (con \`title\`, \`client_name\`, todas las \`sections\` comerciales, etc.). Tu salida es **únicamente** el objeto que corresponde al valor de \`sections.technicalDocument\`: el mismo trozo que el panel guarda en **Det. técnico → subpestaña JSON**, o que se puede pegar dentro del archivo de importación reemplazando solo \`sections.technicalDocument\`.

## PRINCIPIOS

1. **Sin duplicar la propuesta comercial** — No repitas valor de negocio, storytelling ni inversión.
2. **Claves estables** — Cada módulo del producto tiene \`epicKey\` único (slug: minúsculas, guiones). Cada requerimiento bajo un módulo tiene \`flowKey\` único en toda la propuesta (slug).
3. **Módulos del producto = tarjetas comerciales (REGLA ESTRICTA, sin excepciones)** — \`epics[]\` y la sección \`functionalRequirements\` del paso 1 son DOS VISTAS DE LA MISMA HISTORIA: el cliente navega de cada tarjeta comercial a su detalle técnico, y cualquier desalineación (épicas de más, de menos, con otra clave u otro orden) rompe esa narrativa. Reglas exactas:
   - Crea **EXACTAMENTE UNA** épica por cada una de estas tarjetas: \`views\`, \`components\`, \`features\`, cada módulo base incluido (\`admin_module\`, \`analytics_dashboard\`, \`kpi_dashboard_module\`, \`manual_module\`, \`ai_automation_module\`) y cada módulo de \`additionalModules\` **contratado** (\`default_selected: true\` o indicado como seleccionado en el contexto).
   - **PROHIBIDO crear épicas para módulos NO contratados.** Una épica de módulo sin \`linked_module_ids\` se muestra SIEMPRE en el modo técnico (el filtro solo oculta épicas con links a módulos deseleccionados), así que una épica de un módulo no contratado le mostraría al cliente alcance que no compró.
   - \`epicKey\` = id del grupo comercial **EXACTO Y VERBATIM**, guiones bajos incluidos (\`views\`, \`admin_module\`, \`pwa_module\` — NUNCA \`admin-module\` ni variantes). Nota sobre los 5 módulos base: sus tarjetas se muestran al cliente en la sección \`valueAddedModules\`, pero su catálogo e ids viven en \`functionalRequirements.groups\` — la épica se llavea igual por el id del grupo.
   - **Orden de \`epics[]\` = orden de las tarjetas comerciales**: primero los grupos de \`groups[]\` en su orden, luego los módulos contratados de \`additionalModules[]\` en su orden. Si necesitas una épica transversal (ver 3b), va al final.
   - \`linked_module_ids\` de la épica: **OBLIGATORIO** en toda épica de módulo de \`additionalModules\`, con el formato canónico exacto \`["module-<id>"]\` (ej. \`["module-pwa_module"]\`). En las épicas de tarjetas base (\`views\`, \`components\`, \`features\`, módulos base) omítelo o déjalo \`[]\` (alcance base, siempre visible). No uses ningún otro formato de id.
   - Los requerimientos son entregables o flujos concretos dentro de esa épica.
3b. **Trazabilidad item → requerimiento (\`linked_item_ids\`) (REGLA ESTRICTA)** — Cada item de \`functionalRequirements\` del paso 1 trae un \`id\` estable (formato \`item-<grupo>-<slug>\`). En cada requerimiento técnico, incluye \`linked_item_ids\`: array con los \`id\` EXACTOS de los items comerciales que ese requerimiento implementa. **Copia los ids literalmente (carácter por carácter) del JSON del paso 1 — NUNCA los inventes, los traduzcas ni los reconstruyas de memoria.** Un requerimiento puede enlazar varios items. **Cobertura OBLIGATORIA: TODO item comercial de los grupos visibles y de los módulos contratados DEBE quedar enlazado por AL MENOS un requerimiento** — esos enlaces alimentan el modal "Ver requerimientos" de la propuesta comercial y el PDF; un item sin enlaces es un hueco visible para el cliente. Solo los requerimientos de trabajo transversal (infraestructura, seguridad, calidad, CI) pueden omitir \`linked_item_ids\` o dejarlo \`[]\`; pueden vivir en cualquier épica. Los \`linked_module_ids\` de un requerimiento deben ser consistentes con los de su épica: nunca apuntes un requerimiento a un módulo distinto del de la épica que lo contiene.
4. **No inventes stack** — Si el contexto no indica tecnología, deja campos vacíos o "Por definir" en una sola palabra donde aplique.
5. **Preparación para el crecimiento (\`growthReadiness\`)** — Describe **cómo el sistema está preparado para crecer** (tráfico, datos, integraciones, equipos), no solo métricas puntuales de rendimiento: es complementario a \`performanceQuality\`.
6. **Lenguaje accesible en requerimientos** — Los campos \`title\` y \`description\` de cada requerimiento deben usar lenguaje que un dueño de negocio entienda sin ayuda técnica. Los detalles de implementación van en \`configuration\` y \`usageFlow\`.
7. **Stack por defecto de ProjectApp** — Salvo que el contexto indique otra cosa, el stack estándar es: **React + Next.js + Tailwind** (cliente/SSR con App Router, componentes por sección, Zustand para estado global y hooks personalizados para lógica reutilizable), **Django 5 + DRF** (API), **MySQL 8** (datos), **Huey** (tareas asíncronas y cronjobs), **VPS + Nginx + Gunicorn** (infraestructura). **No menciones** Redis, AWS, S3, servicios cloud ni infraestructura que no forme parte del proyecto real.
8. **Backups sin almacenamiento externo** — Los backups son automatizados con periodicidad definida (semanal para BD y archivos multimedia) y retención configurada. **Nunca** menciones almacenamiento externo (S3, cloud buckets, etc.); los backups son locales.

## ESTRUCTURA OBLIGATORIA (technicalDocument)

Debes producir **solo** este objeto JSON (el valor de \`technicalDocument\`, sin envolver en \`sections\` ni en el payload completo de importación). **Servidor estándar de ProjectApp:** VPS con 4 CPUs y 8 GB RAM; considera esta capacidad al describir entornos y estrategias de crecimiento.

El siguiente bloque es un **esqueleto vacío** (solo forma y claves). En tu respuesta **sustituye** \`""\` y \`[]\` por contenido real según el proyecto. **No** copies dentro del JSON textos meta tipo "string — …", instrucciones ni etiquetas de ayuda: solo datos técnicos.

\`\`\`json
{
  "purpose": "",
  "stack": [],
  "architecture": {
    "summary": "",
    "patterns": [],
    "diagramNote": ""
  },
  "dataModel": {
    "summary": "",
    "relationships": "",
    "entities": []
  },
  "growthReadiness": {
    "summary": "",
    "strategies": []
  },
  "epics": [],
  "apiSummary": "",
  "apiDomains": [],
  "integrations": {
    "included": [],
    "excluded": [],
    "notes": ""
  },
  "environments": [],
  "environmentsNote": "",
  "security": [],
  "performanceQuality": {
    "metrics": [],
    "practices": []
  },
  "backupsNote": "",
  "quality": {
    "dimensions": [],
    "testTypes": [],
    "criticalFlowsNote": ""
  },
  "decisions": []
}
\`\`\`

### Forma de elementos al rellenar arrays (referencia)

- \`stack[]\`: \`{ "layer", "technology", "rationale" }\` — Para la capa frontend Next.js, mencionar: App Router (\`app/\`), componentes de UI organizados por sección (\`components/\`), Zustand para estado global, y hooks personalizados para lógica reutilizable.
- \`architecture.patterns[]\`: \`{ "component", "pattern", "description" }\`
- \`dataModel.entities[]\`: \`{ "name", "description", "keyFields" }\`
- \`growthReadiness\`: \`summary\` (texto) y \`strategies[]\` con \`dimension\` (ámbito: tráfico, datos, colas…), \`preparation\` (qué ya está previsto), \`evolution\` (cómo evoluciona ante más carga o alcance)
- \`epics[]\`: \`{ "epicKey", "title", "description", "linked_module_ids"?, "requirements" }\` — \`linked_module_ids\`: OBLIGATORIO con formato canónico \`["module-<id>"]\` en épicas de módulos de \`additionalModules\`; omitido o \`[]\` en épicas de tarjetas base (alcance base, siempre visible en modo técnico). No emitas otros formatos de id. Cada ítem de \`requirements\`: \`flowKey\`, \`title\` (obligatorio si el requerimiento no es vacío), opcionales \`description\`, \`configuration\`, \`usageFlow\`, \`priority\`, \`linked_module_ids\` (consistente con el de su épica), \`linked_item_ids\` (array de \`id\`s de items comerciales del paso 1 que este requerimiento implementa — copiar literalmente, ver PRINCIPIO 3b)
- \`apiDomains[]\`: \`{ "domain", "summary" }\`
- \`integrations.included[]\`: \`service\`, \`provider\`, \`connection\`, \`dataExchange\`, \`accountOwner\` — \`excluded[]\`: \`service\`, \`reason\`, \`availability\`
- \`environments[]\`: \`name\`, \`purpose\`, \`url\`, \`database\`, \`whoAccesses\` — Servidor estándar ProjectApp: VPS con 4 CPUs y 8 GB RAM. URLs por defecto: staging → \`<nombre-propuesta>.project.co\`, producción → dominio propio del cliente (ej. \`<nombre-propuesta>.co\` o el que indique el contexto).
- \`security[]\`: \`aspect\`, \`implementation\`
- \`performanceQuality.metrics[]\`: \`metric\`, \`target\`, \`howMeasured\` — \`practices[]\`: \`strategy\`, \`description\`
- \`quality.dimensions[]\`: \`dimension\`, \`evaluates\`, \`standard\` — \`testTypes[]\`: \`type\`, \`validates\`, \`tool\`, \`whenRun\`
- \`decisions[]\`: \`decision\`, \`alternative\`, \`reason\`

### Reglas

- **No agregues** propiedades de primer nivel que no estén en el esquema anterior (salvo \`linked_module_ids\` dentro de \`epics\` o \`requirements\`, y \`linked_item_ids\` dentro de \`requirements\`).
- **No elimines** claves de primer nivel; si no hay datos, usa string vacío \`""\` o array vacío \`[]\` según el tipo.
- **epics[].requirements[].title** es obligatorio en cada requerimiento que no sea placeholder vacío.
- **flowKey**: ASCII, minúsculas, números y guiones (kebab); sin espacios; único en toda la propuesta.
- **epicKey**: ASCII, minúsculas, números, guiones y guiones bajos; sin espacios. Cuando la épica espeja una tarjeta comercial (el caso normal), DEBE ser IGUAL al id comercial verbatim (\`admin_module\`, no \`admin-module\`).
- **priority** en requerimientos (opcional): \`critical\`, \`high\`, \`medium\`, \`low\` o cadena vacía.

## CHECKLIST ANTES DE RESPONDER

Antes de emitir el JSON, verifica UNO POR UNO estos puntos contra el JSON del paso 1. Si alguno falla, corrige y vuelve a verificar. No respondas hasta que todos pasen:

1. **Una épica por tarjeta contratada:** existe exactamente una épica para \`views\`, \`components\`, \`features\`, cada módulo base y cada módulo adicional contratado — ni una más, ni una menos (salvo una eventual épica transversal al final).
2. **Ninguna épica de módulo no contratado.**
3. **epicKeys exactos:** cada \`epicKey\` es el id comercial verbatim (guiones bajos incluidos) y las épicas siguen el orden de las tarjetas comerciales.
4. **linked_module_ids canónicos:** toda épica de módulo adicional lleva \`linked_module_ids: ["module-<id>"]\`; las de tarjetas base lo omiten o llevan \`[]\`; ningún requerimiento apunta a un módulo distinto del de su épica.
5. **Cobertura total de items:** TODO item comercial (grupos visibles + módulos contratados) aparece en el \`linked_item_ids\` de al menos un requerimiento.
6. **Ids literales:** cada valor de \`linked_item_ids\` existe carácter por carácter en el JSON del paso 1 — cero ids inventados.
7. **Claves:** \`flowKey\`s únicos y kebab; \`priority\` ∈ {\`critical\`, \`high\`, \`medium\`, \`low\`, \`""\`}.
8. **Esquema:** todas las claves de primer nivel presentes, sin claves extra, JSON parseable.

## FORMATO DE SALIDA

Devuelve **únicamente** un objeto JSON válido: el contenido de \`technicalDocument\` descrito arriba. Sin markdown alrededor, sin texto antes ni después. **No** devuelvas el JSON entero de la propuesta. **No** incluyas comentarios estilo \`//\` ni claves que no estén en el esquema.

## CONTEXTO (rellenar por el usuario)

**1) Alineación con el paso 1 (OBLIGATORIO para trazabilidad)** — Pega el JSON comercial que generaste con el prompt comercial; como mínimo la sección \`functionalRequirements\` **completa y sin recortar los \`id\` de los items** — sin ella no puedes rellenar \`linked_item_ids\` y la trazabilidad comercial↔técnica queda vacía. Añade otros extractos útiles (\`general\`, \`timeline\`, etc.). Si el contexto es muy largo, resume lo demás pero nunca los ids de \`functionalRequirements\`. **Nota:** los ids dependen del idioma de la propuesta; no reutilices un detalle técnico generado para la versión en otro idioma.

**REGLA DE ALTO:** si el usuario NO pegó la sección \`functionalRequirements\` con los \`id\` de sus items, **NO generes el JSON**. Responde únicamente pidiendo esa sección ("Necesito la sección functionalRequirements del paso 1, con los id de cada item, para poder enlazar los requerimientos técnicos"). Nunca emitas épicas con \`linked_item_ids\` vacíos como sustituto ni inventes ids que "parezcan" correctos.

**2) Datos adicionales** (opcional, si faltan en el JSON pegado):

\`\`\`
Nombre del cliente / negocio:
Tipo de producto (web, SaaS, marketplace, etc.):
Alcance funcional resumido:
Stack conocido (si aplica):
Integraciones requeridas o excluidas:
Restricciones de seguridad o compliance:
\`\`\`

**3) Dónde pegar tu respuesta** — En el panel: **editar propuesta → Det. técnico → subpestaña JSON → guardar**. O sustituye solo el valor de \`sections.technicalDocument\` en el archivo JSON de importación.
`;

export function useTechnicalPrompt() {
  const promptText = ref(DEFAULT_PROMPT);
  const isEditing = ref(false);

  function loadSavedPrompt() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) promptText.value = saved;
    } catch (_e) { /* ignore */ }
  }

  function savePrompt(text) {
    promptText.value = text;
    try {
      localStorage.setItem(STORAGE_KEY, text);
    } catch (_e) { /* ignore */ }
  }

  function resetPrompt() {
    promptText.value = DEFAULT_PROMPT;
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (_e) { /* ignore */ }
  }

  function copyPrompt() {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      return navigator.clipboard.writeText(promptText.value);
    }
    return Promise.resolve();
  }

  function downloadPrompt() {
    const blob = new Blob([promptText.value], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prompt-detalle-tecnico.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return {
    promptText,
    isEditing,
    DEFAULT_PROMPT,
    loadSavedPrompt,
    savePrompt,
    resetPrompt,
    copyPrompt,
    downloadPrompt,
  };
}
