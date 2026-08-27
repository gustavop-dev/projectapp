import { viewCatalogSections } from './viewCatalog.js'

const feature = (id, label, summary, value, viewUrls, options = {}) => ({
  id,
  kind: 'feature',
  label,
  summary,
  value,
  viewUrls,
  actors: options.actors || ['client'],
  stage: options.stage || 'Operación',
  secondary: options.secondary === true,
})

const capability = (id, label, summary, value, children, options = {}) => ({
  id,
  kind: 'capability',
  label,
  summary,
  value,
  children,
  actors: options.actors || ['client', 'team'],
  stage: options.stage || 'Operación',
})

const shallowDomain = (id, label, summary, value) => ({
  id,
  kind: 'domain',
  sectionId: id,
  label,
  summary,
  value,
  children: [],
  isDeep: false,
})

const platformCapabilities = [
  capability(
    'platform-access-account',
    'Acceso y cuenta',
    'Entrada segura, verificación de identidad y administración del perfil.',
    'Acompaña al usuario desde su primer ingreso hasta una cuenta lista para operar.',
    [
      feature(
        'platform-secure-entry',
        'Ingresar de forma segura',
        'Permite entrar, validar el código de acceso y completar el perfil inicial.',
        'Reduce fricción en el onboarding sin perder control sobre la identidad.',
        ['/platform', '/platform/login', '/platform/verify', '/platform/complete-profile'],
        { stage: 'Ingreso' },
      ),
      feature(
        'platform-account-recovery',
        'Recuperar el acceso',
        'Guía la recuperación de contraseña y la verificación de códigos.',
        'Ayuda al cliente a volver a operar sin depender de soporte manual.',
        [
          '/platform/admin-login',
          '/platform/forgot-password',
          '/platform/reset-password',
          '/platform/verify-code',
        ],
        { stage: 'Ingreso' },
      ),
      feature(
        'platform-profile-management',
        'Mantener el perfil al día',
        'Centraliza los datos personales y la configuración de la cuenta.',
        'Mantiene la experiencia y las comunicaciones vinculadas a la persona correcta.',
        ['/platform/profile'],
        { stage: 'Cuenta' },
      ),
    ],
    { stage: 'Ingreso' },
  ),
  capability(
    'platform-client-projects',
    'Clientes y proyectos',
    'Panorama de clientes, proyectos activos y contexto de cada iniciativa.',
    'Convierte cada proyecto en un espacio operativo con una visión compartida.',
    [
      feature(
        'platform-project-portfolio',
        'Consultar los proyectos',
        'Permite recorrer el portafolio y entrar al resumen de una iniciativa.',
        'Da una lectura clara de qué se está construyendo y dónde continuar.',
        ['/platform/projects', '/platform/projects/:id', '/platform/dashboard'],
        { stage: 'Proyecto' },
      ),
      feature(
        'platform-client-administration',
        'Administrar clientes',
        'Permite al equipo consultar clientes y abrir su contexto operativo.',
        'Relaciona cada iniciativa con la persona y organización responsables.',
        ['/platform/clients', '/platform/clients/:id'],
        { actors: ['team'], stage: 'Administración' },
      ),
    ],
    { stage: 'Proyecto' },
  ),
  capability(
    'platform-work-tracking',
    'Seguimiento del trabajo',
    'Tablero, solicitudes, bugs y estructura funcional reunidos por proyecto.',
    'Hace visible el avance y ordena las conversaciones sobre lo que falta por resolver.',
    [
      feature(
        'platform-project-board',
        'Seguir el avance',
        'Presenta el tablero de trabajo dentro del contexto del proyecto.',
        'Permite entender prioridades, estado y próximos movimientos.',
        ['/platform/projects/:id/board', '/platform/board'],
        { stage: 'Seguimiento' },
      ),
      feature(
        'platform-bug-follow-up',
        'Reportar y seguir bugs',
        'Concentra los problemas reportados y su evolución.',
        'Da trazabilidad a los incidentes sin dispersarlos en conversaciones externas.',
        ['/platform/projects/:id/bugs', '/platform/bugs'],
        { stage: 'Soporte' },
      ),
      feature(
        'platform-change-requests',
        'Gestionar solicitudes de cambio',
        'Organiza nuevas solicitudes y decisiones fuera del alcance inicial.',
        'Separa los cambios del trabajo acordado y facilita priorizarlos.',
        ['/platform/projects/:id/changes', '/platform/changes'],
        { stage: 'Seguimiento' },
      ),
      feature(
        'platform-data-model',
        'Comprender la estructura funcional',
        'Expone el modelo de datos asociado al proyecto cuando está disponible.',
        'Ayuda a conversar sobre la información del producto en un mismo contexto.',
        ['/platform/projects/:id/data-model'],
        { actors: ['client', 'team'], stage: 'Planeación' },
      ),
    ],
    { stage: 'Seguimiento' },
  ),
  capability(
    'platform-deliverables',
    'Entregables y recursos',
    'Materiales, versiones y resultados compartidos durante el proyecto.',
    'Mantiene las entregas localizables y conectadas con el trabajo que las produjo.',
    [
      feature(
        'platform-deliverable-library',
        'Consultar entregables',
        'Permite revisar la biblioteca del proyecto y abrir el detalle de cada entrega.',
        'Ofrece un punto estable para encontrar y validar los recursos recibidos.',
        [
          '/platform/projects/:id/deliverables',
          '/platform/projects/:id/deliverables/:deliverableId',
          '/platform/deliverables',
        ],
        { stage: 'Entrega' },
      ),
    ],
    { stage: 'Entrega' },
  ),
  capability(
    'platform-documents',
    'Documentos y aprobaciones',
    'Contratos y anexos disponibles para consulta, descarga y aceptación.',
    'Reduce pasos manuales en la entrega documental y deja una aprobación trazable.',
    [
      feature(
        'platform-document-portal',
        'Revisar y aprobar documentos',
        'Reúne documentos del cliente y el flujo de firma del documento principal.',
        'Facilita pasar de la lectura a una aprobación verificable en el mismo portal.',
        ['/platform/documents'],
        { stage: 'Aprobación' },
      ),
    ],
    { stage: 'Aprobación' },
  ),
  capability(
    'platform-commercial-operations',
    'Pagos, hosting y cobros',
    'Estado comercial del proyecto, pagos y documentos de cobro.',
    'Da transparencia sobre compromisos económicos y continuidad operativa.',
    [
      feature(
        'platform-project-payments',
        'Consultar pagos y hosting',
        'Presenta la operación de pagos asociada al proyecto.',
        'Ayuda al cliente a entender obligaciones, cobertura y continuidad del servicio.',
        ['/platform/projects/:id/payments', '/platform/payments'],
        { stage: 'Cobro' },
      ),
      feature(
        'platform-collection-accounts',
        'Consultar cuentas de cobro',
        'Reúne las cuentas vinculadas al proyecto y sus accesos anteriores.',
        'Mantiene los soportes de cobro dentro del contexto comercial correcto.',
        [
          '/platform/projects/:id/collection-accounts',
          '/platform/collection-accounts',
          '/platform/collection-accounts/:id',
        ],
        { stage: 'Cobro' },
      ),
    ],
    { stage: 'Cobro' },
  ),
  capability(
    'platform-notifications',
    'Comunicación y notificaciones',
    'Novedades relevantes de la relación y de los proyectos.',
    'Mantiene al usuario enterado sin obligarlo a revisar cada espacio por separado.',
    [
      feature(
        'platform-notification-center',
        'Revisar novedades',
        'Agrupa las notificaciones que requieren atención del usuario.',
        'Funciona como bandeja operativa para regresar al contexto indicado.',
        ['/platform/notifications'],
        { stage: 'Comunicación' },
      ),
    ],
    { stage: 'Comunicación' },
  ),
  capability(
    'platform-access-management',
    'Administración de accesos',
    'URLs y credenciales operativas disponibles exclusivamente para el equipo autorizado.',
    'Acelera el soporte y la operación sin exponer información sensible a clientes.',
    [
      feature(
        'platform-project-access',
        'Abrir accesos operativos',
        'Centraliza accesos del proyecto y conserva el enlace global anterior.',
        'Permite al equipo llegar rápidamente a los entornos necesarios para operar.',
        ['/platform/projects/:id/access', '/platform/access'],
        { actors: ['team'], stage: 'Administración' },
      ),
    ],
    { actors: ['team'], stage: 'Administración' },
  ),
]

export const viewCapabilityCatalog = {
  id: 'projectapp',
  kind: 'root',
  label: 'Ecosistema ProjectApp',
  summary: 'Una vista de alto nivel de las capacidades que conectan venta, operación y entrega.',
  value: 'Permite explicar la aplicación desde lo que hace por el negocio, no desde su arquitectura.',
  children: [
    shallowDomain(
      'public-site',
      'Presencia digital',
      'Marketing, contenido y puntos de contacto públicos.',
      'Atrae oportunidades y presenta la experiencia de ProjectApp.',
    ),
    shallowDomain(
      'public-proposals',
      'Propuestas comerciales',
      'Experiencias compartidas para presentar y cerrar una propuesta.',
      'Convierte una propuesta estática en una conversación medible.',
    ),
    shallowDomain(
      'public-diagnostics',
      'Diagnósticos',
      'Lecturas ejecutivas y técnicas del estado de una iniciativa.',
      'Ayuda a priorizar oportunidades de mejora antes de ejecutar.',
    ),
    shallowDomain(
      'admin-panel',
      'Operación interna',
      'Herramientas del equipo para ventas, contenido, clientes y documentos.',
      'Centraliza el trabajo administrativo que sostiene la relación comercial.',
    ),
    shallowDomain(
      'panel-accounting',
      'Control financiero',
      'Ingresos, egresos, cobros, hosting y seguimiento contable.',
      'Hace visible la operación financiera y sus compromisos.',
    ),
    shallowDomain(
      'panel-mcps',
      'Automatización asistida',
      'Conectores que acercan capacidades del panel a asistentes autorizados.',
      'Reduce trabajo repetitivo manteniendo los controles del producto.',
    ),
    {
      id: 'client-platform',
      kind: 'domain',
      sectionId: 'client-platform',
      label: 'Plataforma de clientes',
      summary: 'El espacio donde clientes y equipo siguen la ejecución y sus entregas.',
      value: 'Conecta el proyecto, la comunicación y la operación comercial en una sola experiencia.',
      children: platformCapabilities,
      isDeep: true,
      relations: [
        { from: 'platform-access-account', to: 'platform-client-projects', label: 'habilita la operación' },
        { from: 'platform-client-projects', to: 'platform-work-tracking', label: 'organiza el trabajo' },
        { from: 'platform-work-tracking', to: 'platform-deliverables', label: 'conduce a entregas' },
        { from: 'platform-client-projects', to: 'platform-documents', label: 'da contexto documental' },
        { from: 'platform-client-projects', to: 'platform-commercial-operations', label: 'conecta compromisos' },
        { from: 'platform-documents', to: 'platform-access-account', label: 'requiere identidad' },
        { from: 'platform-work-tracking', to: 'platform-notifications', label: 'genera novedades' },
        { from: 'platform-commercial-operations', to: 'platform-notifications', label: 'comunica vencimientos' },
        { from: 'platform-client-projects', to: 'platform-access-management', label: 'habilita la operación interna' },
      ],
    },
  ],
}

export function flattenCapabilityCatalog(root = viewCapabilityCatalog) {
  const result = []
  const visit = (node, parentId = null) => {
    result.push({ ...node, parentId })
    for (const child of node.children || []) visit(child, node.id)
  }
  visit(root)
  return result
}

export function findCapabilityNode(nodeId, root = viewCapabilityCatalog) {
  if (!nodeId || nodeId === root.id) return root
  return flattenCapabilityCatalog(root).find((node) => node.id === nodeId) || null
}

export function capabilityNodePath(nodeId, root = viewCapabilityCatalog) {
  const nodes = flattenCapabilityCatalog(root)
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const path = []
  let current = byId.get(nodeId || root.id)
  while (current) {
    path.unshift(current)
    current = current.parentId ? byId.get(current.parentId) : null
  }
  return path.length > 0 ? path : [root]
}

export function capabilityViewRecords(node, sections = viewCatalogSections) {
  const entriesByUrl = new Map(
    sections.flatMap((section) => section.views.map((view) => [view.url, view])),
  )
  return (node?.viewUrls || []).map((url) => entriesByUrl.get(url)).filter(Boolean)
}

export function capabilityCatalogFindings(
  root = viewCapabilityCatalog,
  sections = viewCatalogSections,
) {
  const findings = []
  const nodes = flattenCapabilityCatalog(root)
  const sectionById = new Map(sections.map((section) => [section.id, section]))
  const nodeCounts = new Map()

  for (const node of nodes) {
    nodeCounts.set(node.id, (nodeCounts.get(node.id) || 0) + 1)
    if (!node.label?.trim() || !node.summary?.trim() || !node.value?.trim()) {
      findings.push(`Nodo operativo incompleto: ${node.id}`)
    }
    if (node.sectionId && !sectionById.has(node.sectionId)) {
      findings.push(`Sección inexistente en nodo operativo: ${node.id}:${node.sectionId}`)
    }
  }

  for (const [nodeId, count] of nodeCounts) {
    if (count > 1) findings.push(`ID operativo duplicado: ${nodeId}`)
  }

  const allCatalogUrls = new Set(sections.flatMap((section) => section.views.map((view) => view.url)))
  const taxonomyUrls = nodes.flatMap((node) => node.viewUrls || [])
  for (const url of taxonomyUrls) {
    if (!allCatalogUrls.has(url)) findings.push(`Vista operativa inexistente: ${url}`)
  }

  const platformUrls = sectionById.get('client-platform')?.views.map((view) => view.url) || []
  const platformCounts = new Map()
  for (const url of taxonomyUrls) platformCounts.set(url, (platformCounts.get(url) || 0) + 1)
  for (const url of platformUrls) {
    const count = platformCounts.get(url) || 0
    if (count === 0) findings.push(`Vista de Plataforma sin capacidad: ${url}`)
    if (count > 1) findings.push(`Vista de Plataforma repetida entre capacidades: ${url}`)
  }

  for (const node of nodes) {
    const childIds = new Set((node.children || []).map((child) => child.id))
    for (const relation of node.relations || []) {
      if (!childIds.has(relation.from) || !childIds.has(relation.to)) {
        findings.push(`Relación funcional rota en ${node.id}: ${relation.from} -> ${relation.to}`)
      }
    }
  }

  return findings
}
