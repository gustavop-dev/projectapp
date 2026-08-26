import { PANEL_VIEWPORTS } from './responsive.js';

const module = (label, paths, checklist) => Object.freeze({
  label,
  tag: `@responsive:${label.toLowerCase().replaceAll(' ', '-')}`,
  paths: Object.freeze(paths),
  checklist: Object.freeze(checklist),
});

/**
 * Permanent responsive acceptance matrix.
 *
 * `paths` controls the changed-module gate. `checklist` is the written user
 * journey that must remain useful at every viewport in PANEL_VIEWPORTS.
 */
export const RESPONSIVE_MODULES = Object.freeze({
  foundation: module('foundation', [
    'frontend/assets/styles/',
    'frontend/components/base/',
    'frontend/components/panel/PanelMobileDrawer.vue',
    'frontend/components/panel/PanelSidebar.vue',
    'frontend/composables/usePanelSidebar.js',
    'frontend/config/responsive.js',
    'frontend/layouts/admin.vue',
    'frontend/pages/panel/styleguide.vue',
    'frontend/tailwind.config.js',
  ], [
    'Abrir el menú y llegar a una vista del panel.',
    'Cambiar tabs/filtros y volver al contenido principal.',
    'Abrir y cerrar tabla, modal, acciones y selección de la guía.',
  ]),
  accounting: module('accounting', [
    'frontend/components/accounting/',
    'frontend/pages/panel/accounting/',
  ], [
    'Recorrer los doce tabs sin perder la navegación.',
    'Filtrar, ordenar y abrir una fila representativa.',
    'Abrir los modales largos y completar sus pasos.',
  ]),
  documents: module('documents', [
    'frontend/components/panel/documents/',
    'frontend/pages/panel/documents/index.vue',
    'frontend/pages/panel/documents/statuses.vue',
  ], [
    'Abrir y cerrar el selector de carpetas.',
    'Cambiar entre activos y archivados y operar una fila.',
    'Abrir las acciones de carpeta y documento y administrar el catálogo de estados.',
  ]),
  clients: module('clients', [
    'frontend/components/clients/',
    'frontend/components/platform/',
    'frontend/layouts/platform.vue',
    'frontend/pages/panel/clients/',
    'frontend/pages/platform/',
  ], [
    'Cambiar estado y filtros sin ocultar el primer cliente.',
    'Leer los datos prioritarios de una tarjeta de cliente.',
    'Abrir acciones y reasignación.',
  ]),
  projects: module('projects', [
    'frontend/components/panel/projects/',
    'frontend/pages/panel/projects/',
  ], [
    'Buscar y cambiar el alcance del listado.',
    'Crear o editar un proyecto.',
    'Revisar la vista previa del cambio de cliente.',
  ]),
  commercial: module('commercial', [
    'frontend/components/BusinessProposal/admin/',
    'frontend/components/WebAppDiagnostic/admin/',
    'frontend/components/proposals/',
    'frontend/pages/panel/defaults.vue',
    'frontend/pages/panel/diagnostics/',
    'frontend/pages/panel/hour-packages/',
    'frontend/pages/panel/proposals/',
  ], [
    'Buscar, filtrar y operar propuestas y diagnósticos.',
    'Usar selección múltiple y acciones por fila.',
    'Crear, editar y previsualizar una pieza comercial.',
    'Crear o editar un paquete de horas.',
  ]),
  emails: module('emails', [
    'frontend/components/email/',
    'frontend/pages/panel/emails/',
    'frontend/pages/panel/proposals/email-deliverability.vue',
    'frontend/pages/panel/proposals/email-templates.vue',
  ], [
    'Completar destinatario, asunto, contenido y adjuntos.',
    'Abrir la vista previa y volver al formulario.',
    'Consultar el historial y sus estados.',
  ]),
  communications: module('communications', [
    'frontend/pages/panel/communications/',
  ], [
    'Buscar y seleccionar un hilo sin perder el contexto del cliente.',
    'Leer mensajes entrantes y salientes con estado, fecha y adjuntos.',
    'Registrar un mensaje y completar las acciones de auditoría.',
  ]),
  canvas: module('canvas', [
    'frontend/components/panel/documents/DocumentEditor',
    'frontend/components/panel/documents/DocumentPreview',
    'frontend/pages/panel/documents/create.vue',
    'frontend/pages/panel/documents/[id]/edit.vue',
  ], [
    'Editar título, cliente, proyecto y contenido en orden de lectura.',
    'Alternar editor y vista previa.',
    'Guardar o salir mediante el guard de cambios.',
  ]),
  dashboard: module('dashboard', [
    'frontend/components/panel/dashboard/',
    'frontend/components/stats/',
    'frontend/pages/panel/admins/',
    'frontend/pages/panel/index.vue',
    'frontend/pages/panel/tasks/',
    'frontend/pages/panel/views.vue',
  ], [
    'Leer pulso, radar y secciones sin cifras truncadas.',
    'Abrir estadísticas y cambiar sus tabs.',
    'Llegar a las acciones rápidas y a las alertas.',
  ]),
  content: module('content', [
    'frontend/components/panel/qr-cards/',
    'frontend/pages/panel/blog/',
    'frontend/pages/panel/linkedin/',
    'frontend/pages/panel/linktrees/',
    'frontend/pages/panel/portfolio/',
    'frontend/pages/panel/qr-cards/',
  ], [
    'Recorrer blog, calendario, LinkedIn, portafolio, QR y linktrees.',
    'Crear o editar una pieza y alcanzar su acción principal.',
    'Abrir preview, menús y confirmaciones sin depender de hover.',
  ]),
  mcp: module('mcp', [
    'frontend/pages/panel/mcps/',
  ], [
    'Expandir un conector y consultar actividad y tools.',
    'Generar un token y cerrar su modal.',
    'Activar o desactivar el conector.',
  ]),
  public: module('public', [
    'frontend/components/BusinessProposal/',
    'frontend/components/Linktree/',
    'frontend/components/WebAppDiagnostic/public/',
    'frontend/components/home/',
    'frontend/components/landing/',
    'frontend/components/pages/',
    'frontend/layouts/default.vue',
    'frontend/pages/about-us.vue',
    'frontend/pages/blog/',
    'frontend/pages/contact',
    'frontend/pages/diagnostic/',
    'frontend/pages/index.vue',
    'frontend/pages/landing-',
    'frontend/pages/lk/',
    'frontend/pages/portfolio-works/',
    'frontend/pages/privacy-policy.vue',
    'frontend/pages/proposal/',
    'frontend/pages/terms-and-conditions.vue',
  ], [
    'Abrir home, landings, contacto, blog, portafolio y legales.',
    'Abrir un linktree y usar sus acciones principales.',
    'Recorrer una propuesta y un diagnóstico compartidos.',
    'Confirmar que controles flotantes no cubren el contenido.',
  ]),
});

export const RESPONSIVE_MODULE_NAMES = Object.freeze(Object.keys(RESPONSIVE_MODULES));
export const RESPONSIVE_VIEWPORT_NAMES = Object.freeze(Object.keys(PANEL_VIEWPORTS));

const ALL_MODULES_PATHS = Object.freeze([
  '.github/workflows/responsive-acceptance.yml',
  'frontend/config/responsiveAcceptance.js',
  'frontend/e2e/helpers/test.js',
  'frontend/playwright.config.js',
  'frontend/scripts/check-responsive-contract.mjs',
]);

const ALL_MODULES_PREFIXES = Object.freeze([
  'frontend/assets/styles/',
  'frontend/components/base/',
  'frontend/e2e/',
  'frontend/layouts/admin.vue',
  'frontend/tailwind.config.js',
]);

const UI_PREFIXES = Object.freeze([
  'frontend/components/',
  'frontend/layouts/',
  'frontend/pages/',
]);

export function modulesForChangedFiles(files) {
  const normalized = files.map((file) => file.replaceAll('\\', '/'));
  if (normalized.some((file) => (
    ALL_MODULES_PATHS.includes(file)
    || ALL_MODULES_PREFIXES.some((path) => file.startsWith(path))
  ))) {
    return [...RESPONSIVE_MODULE_NAMES];
  }

  const matched = RESPONSIVE_MODULE_NAMES.filter((name) => {
    const paths = RESPONSIVE_MODULES[name].paths;
    return normalized.some((file) => paths.some((path) => file.startsWith(path)));
  });

  // A new UI surface must never silently bypass responsive acceptance just
  // because its directory has not been added to the registry yet. The
  // contract job will force ownership for pages; this conservative fallback
  // protects new shared components and layouts too.
  if (matched.length === 0 && normalized.some((file) => UI_PREFIXES.some((path) => file.startsWith(path)))) {
    return [...RESPONSIVE_MODULE_NAMES];
  }

  return matched;
}

/** Every catalog view has one accountable responsive module or dependency. */
export function responsiveOwnerForView(sectionId, view) {
  const { file, url } = view;
  if (sectionId.startsWith('public-') || view.audience === 'public') return 'public';
  if (sectionId === 'panel-accounting') return 'accounting';
  if (sectionId === 'panel-mcps') return 'mcp';
  if (sectionId === 'client-platform') return 'clients';

  if (url === '/panel/login' || url === '/panel/styleguide') return 'foundation';
  if (url === '/panel/clients') return 'clients';
  if (url === '/panel/projects') return 'projects';
  if (url === '/panel/documents' || url === '/panel/documents/statuses') return 'documents';
  if (url === '/panel/communications') return 'communications';
  if (file === 'frontend/pages/panel/documents/create.vue' || file === 'frontend/pages/panel/documents/[id]/edit.vue') return 'canvas';
  if (url === '/panel/emails' || url.includes('/email-')) return 'emails';
  if (url.startsWith('/panel/proposals') || url.startsWith('/panel/diagnostics') || url.startsWith('/panel/hour-packages') || url === '/panel/defaults') return 'commercial';
  if (url.startsWith('/panel/blog') || url.startsWith('/panel/linkedin') || url.startsWith('/panel/portfolio') || url.startsWith('/panel/qr-cards') || url.startsWith('/panel/linktrees')) return 'content';
  if (url === '/panel' || url.startsWith('/panel/tasks') || url.startsWith('/panel/admins') || url === '/panel/views') return 'dashboard';
  return null;
}
