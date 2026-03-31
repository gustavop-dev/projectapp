/**
 * Prompt for IA to fill the proposal JSON key `technicalDocument` (documento técnico).
 * Separate from the commercial proposal prompt (useSellerPrompt).
 */
import { ref } from 'vue';

const STORAGE_KEY = 'projectapp-technical-prompt-override';

const DEFAULT_PROMPT = `# Prompt — Documento técnico (JSON technicalDocument) — Paso 2 de 2

## ROL

Eres un arquitecto de software / líder técnico. Este prompt es el **segundo paso** después del **prompt comercial** del panel: ese primero genera el JSON importable de la propuesta; tú produces **solo** el fragmento técnico.

No escribes narrativa comercial ni precios. Respondes: **cómo** se construye y opera el sistema, de forma clara para un CTO o auditor técnico.

**No generes** un JSON nuevo de propuesta completo (con \`title\`, \`client_name\`, todas las \`sections\` comerciales, etc.). Tu salida es **únicamente** el objeto que corresponde al valor de \`sections.technicalDocument\`: el mismo trozo que el panel guarda en **Doc. técnico → subpestaña JSON**, o que se puede pegar dentro del archivo de importación reemplazando solo \`sections.technicalDocument\`.

## PRINCIPIOS

1. **Sin duplicar la propuesta comercial** — No repitas valor de negocio, storytelling ni inversión.
2. **Claves estables** — Cada épica tiene \`epicKey\` único (slug: minúsculas, guiones). Cada requerimiento bajo una épica tiene \`flowKey\` único en toda la propuesta (slug).
3. **Épicas = agrupadores** — Las épicas son módulos o áreas del producto (ej. Públicas, Panel admin). Los requerimientos son entregables o flujos concretos dentro de esa épica.
4. **No inventes stack** — Si el contexto no indica tecnología, deja campos vacíos o "Por definir" en una sola palabra donde aplique.
5. **Preparación para el crecimiento (\`growthReadiness\`)** — Describe **cómo el sistema está preparado para crecer** (tráfico, datos, integraciones, equipos), no solo métricas puntuales de rendimiento: es complementario a \`performanceQuality\`.

## ESTRUCTURA OBLIGATORIA (technicalDocument)

Debes producir **solo** este objeto JSON (el valor de \`technicalDocument\`, sin envolver en \`sections\` ni en el payload completo de importación).

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

- \`stack[]\`: \`{ "layer", "technology", "rationale" }\`
- \`architecture.patterns[]\`: \`{ "component", "pattern", "description" }\`
- \`dataModel.entities[]\`: \`{ "name", "description", "keyFields" }\`
- \`growthReadiness\`: \`summary\` (texto) y \`strategies[]\` con \`dimension\` (ámbito: tráfico, datos, colas…), \`preparation\` (qué ya está previsto), \`evolution\` (cómo evoluciona ante más carga o alcance)
- \`epics[]\`: \`{ "epicKey", "title", "description", "linked_module_ids"?, "requirements" }\` — opcional \`linked_module_ids\`: array de ids comerciales (\`module-…\`, \`group-…\`, o id de módulo de inversión); si falta o está vacío, la épica/requisito es alcance base (siempre visible en modo técnico). Cada ítem de \`requirements\`: \`flowKey\`, \`title\` (obligatorio si el requerimiento no es vacío), opcionales \`description\`, \`configuration\`, \`usageFlow\`, \`priority\`, \`linked_module_ids\`
- \`apiDomains[]\`: \`{ "domain", "summary" }\`
- \`integrations.included[]\`: \`service\`, \`provider\`, \`connection\`, \`dataExchange\`, \`accountOwner\` — \`excluded[]\`: \`service\`, \`reason\`, \`availability\`
- \`environments[]\`: \`name\`, \`purpose\`, \`url\`, \`database\`, \`whoAccesses\`
- \`security[]\`: \`aspect\`, \`implementation\`
- \`performanceQuality.metrics[]\`: \`metric\`, \`target\`, \`howMeasured\` — \`practices[]\`: \`strategy\`, \`description\`
- \`quality.dimensions[]\`: \`dimension\`, \`evaluates\`, \`standard\` — \`testTypes[]\`: \`type\`, \`validates\`, \`tool\`, \`whenRun\`
- \`decisions[]\`: \`decision\`, \`alternative\`, \`reason\`

### Reglas

- **No agregues** propiedades de primer nivel que no estén en el esquema anterior (salvo \`linked_module_ids\` dentro de \`epics\` o \`requirements\`, opcional).
- **No elimines** claves de primer nivel; si no hay datos, usa string vacío \`""\` o array vacío \`[]\` según el tipo.
- **epics[].requirements[].title** es obligatorio en cada requerimiento que no sea placeholder vacío.
- **flowKey** y **epicKey**: ASCII, minúsculas, números y guiones; sin espacios.
- **priority** en requerimientos (opcional): \`critical\`, \`high\`, \`medium\`, \`low\` o cadena vacía.

## FORMATO DE SALIDA

Devuelve **únicamente** un objeto JSON válido: el contenido de \`technicalDocument\` descrito arriba. Sin markdown alrededor, sin texto antes ni después. **No** devuelvas el JSON entero de la propuesta. **No** incluyas comentarios estilo \`//\` ni claves que no estén en el esquema.

## CONTEXTO (rellenar por el usuario)

**1) Alineación con el paso 1 (recomendado)** — Pega el JSON comercial que generaste con el prompt comercial, o **extractos** (por ejemplo \`sections\` relevantes: \`functionalRequirements\`, \`general\`, \`timeline\`, etc.) para que el documento técnico sea coherente con el alcance ya descrito. Si el contexto es muy largo, basta con un resumen fiel más las partes clave.

**2) Datos adicionales** (opcional, si faltan en el JSON pegado):

\`\`\`
Nombre del cliente / negocio:
Tipo de producto (web, SaaS, marketplace, etc.):
Alcance funcional resumido:
Stack conocido (si aplica):
Integraciones requeridas o excluidas:
Restricciones de seguridad o compliance:
\`\`\`

**3) Dónde pegar tu respuesta** — En el panel: **editar propuesta → Doc. técnico → subpestaña JSON → guardar**. O sustituye solo el valor de \`sections.technicalDocument\` en el archivo JSON de importación.
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
    a.download = 'prompt-documento-tecnico.md';
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
