# Videos explicativos + estándar de presentación de vistas públicas — diseño

Fecha: 2026-09-04 · Módulos: Módulos adicionales y Financiación · Estado: implementado en `feat/04092026-explainer-videos`.

## Decisión

Cada vista pública de módulo abre con un **video explicativo de un minuto** como
primer recurso visual bajo el título, seguido de un **tour guiado** que empieza
en ese video. Los videos se producen offline con HyperFrames (HTML + GSAP → MP4
determinista) a partir del contenido público real, y el panel muestra el mismo
video en una tarjeta compacta. El motor del tour es un componente genérico
compartido por todas las vistas públicas.

## Criterios

- El cliente entiende el módulo en ≤ 75 s sin leer el detalle; el video se
  entiende **sin sonido** (títulos + subtítulos en pantalla).
- Reproducción bajo demanda (poster + play) con sonido y controles nativos; sin
  autoplay silencioso ni modal.
- Contenido fiel a la vista: nombres, conteos e íconos vienen de la API pública;
  nunca se queman montos ni porcentajes de política configurables.
- Regenerable en tres comandos cuando el catálogo o el programa cambian.
- Sin nuevas páginas, endpoints ni modelos; sin dependencias nuevas en el frontend.

## Alcance

- Público: `/additional-modules`, `/additional-modules/share/<uuid>` (tarjeta
  hero bajo el subtítulo, paso 1 del tour de 8 pasos) y `/financing` (tarjeta
  hero en el hero, tour nuevo de 8 pasos con FAB de reinicio).
- Panel: `/panel/additional-modules` y `/panel/financing` (tarjeta compacta;
  la vista previa de financiación no repite el video ni monta el tour).
- Idioma: español. En `en-us` la tarjeta se oculta hasta tener render EN
  (la composición y el pipeline ya están parametrizados por idioma).

Fuera de alcance: render en inglés, propuesta comercial, analítica de
reproducción, players externos.

## Pipeline offline (`explainers/`)

`fetch-content` (API pública → `content/<video>.<lang>.js`) → `sync` (marca,
fuentes Ubuntu/Noto Emoji, GSAP a `<video>/assets/`) → `stage` (guion ESM →
`script.js`) → `lint`/`check --snapshots`/`snapshot` → `render` (intermedio
HyperFrames casi sin pérdida + una codificación ffmpeg con música y narración
opcional, `faststart`, presupuesto ≤ 12 MB) → `poster` → `export` a
`frontend/assets/{videos,images}/explainers/`. La composición es muda: el audio
se mezcla en post, así cambiar música o narración no re-renderiza.

Narración: opcional, voz masculina local (Kokoro `em_alex`/`em_santa`) generada
por escena y alineada a los tiempos del `index.html`; se decide por compuerta
del operador. Música: pad sintético de reemplazo hasta recibir una pista con
licencia.

## Integración frontend

- `useExplainerVideos.js`: descriptores por módulo e idioma (`null` = sin render).
- `ExplainerVideoCard.vue`: `idle → playing → error`; en error el player queda
  montado y se ofrece el archivo (el Chromium de Playwright no decodifica H.264).
- `PublicGuidedTour.vue`: motor extraído de `AdditionalModules/Onboarding.vue`
  sin cambios de comportamiento (props `steps`, `storageKey`, `testIdPrefix`,
  `labels`, `isDark`; expone `start`/`forceStart`; emite `complete`).
  `AdditionalModules/Onboarding.vue` y `Financing/Onboarding.vue` son wrappers
  con sus pasos e i18n.
- Assets por `import` (hash en `_nuxt/`, nginx con cache inmutable y `Range`);
  jest los stubbea antes de resolver el alias `~/`.

## Tests

Unit: tarjeta, composable, motor del tour, dos wrappers, `CatalogView`,
`ProgramView`. E2E (API mockeada, sin reproducción real): flows
`public-additional-modules-explainer`, `public-financing-explainer`,
`public-financing-guide`, `admin-additional-modules-explainer`,
`admin-financing-explainer`; guía del catálogo actualizada a 8 pasos.

## Riesgos aceptados

- +≈ 7 MB de binarios por idioma en el repo (convención vigente, sin LFS).
- Render en el VPS de producción con `nice` y un worker.
- El contenido del video envejece con el catálogo: regeneración documentada en
  `explainers/README.md`.
