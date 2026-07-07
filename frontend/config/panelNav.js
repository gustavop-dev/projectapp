/**
 * Admin panel navigation: section definitions. Paths are i18n keys; resolve with localePath().
 * @param {(path: string) => string} localePath - Nuxt i18n localePath composable
 * @param {{ includeSuperuserOnly?: boolean }} [options] - pass the viewer's
 *   superuser flag to hide gated sections; defaults to including everything
 *   (label lookups in the admin layout need the full list).
 * @returns {Array<{ id: string, label: string, muted?: boolean, superuserOnly?: boolean, items: Array<NavItem> }>}
 */

/**
 * @typedef {Object} NavItem
 * @property {string} label
 * @property {string} href - Resolved URL (pass through localePath)
 * @property {string} icon - SidebarIcon name
 * @property {boolean} [matchExact] - Only exact path match (e.g. dashboard)
 * @property {boolean} [external] - Use <a> instead of NuxtLink
 * @property {boolean} [openInNewTab]
 */

export function getPanelNavSections(localePath, { includeSuperuserOnly = true } = {}) {
  const lp = localePath
  const sections = [
    {
      id: 'overview',
      label: 'General',
      items: [
        {
          label: 'Dashboard',
          href: lp('/panel'),
          icon: 'dashboard',
          matchExact: true,
        },
      ],
    },
    {
      id: 'tasks',
      label: 'Tareas',
      items: [
        { label: 'Kanban', href: lp('/panel/tasks'), icon: 'board' },
      ],
    },
    {
      id: 'commercial',
      label: 'Comercial',
      items: [
        { label: 'Defaults', href: lp('/panel/defaults'), icon: 'settings' },
        { label: 'Clientes', href: lp('/panel/clients'), icon: 'users' },
        { label: 'Entregabilidad email', href: lp('/panel/proposals/email-deliverability'), icon: 'mail' },
        { label: 'Propuestas', href: lp('/panel/proposals'), icon: 'folder' },
        { label: 'Nueva propuesta', href: lp('/panel/proposals/create'), icon: 'plus' },
        { divider: true },
        { label: 'Diagnósticos', href: lp('/panel/diagnostics'), icon: 'file' },
        { label: 'Nuevo diagnóstico', href: lp('/panel/diagnostics/create'), icon: 'plus' },
      ],
    },
    {
      id: 'site',
      label: 'Contenido ProjectApp',
      items: [
        { label: 'Blog', href: lp('/panel/blog'), icon: 'blog' },
        { label: 'Calendario del blog', href: lp('/panel/blog/calendar'), icon: 'calendar' },
        { label: 'Portafolio', href: lp('/panel/portfolio'), icon: 'portfolio' },
        { label: 'LinkedIn', href: lp('/panel/linkedin'), icon: 'linkedin' },
      ],
    },
    {
      id: 'emails',
      label: 'Emails',
      items: [
        { label: 'Emails', href: lp('/panel/emails'), icon: 'mail' },
      ],
    },
    {
      id: 'documents',
      label: 'Documentos',
      items: [
        { label: 'Documentos PDF', href: lp('/panel/documents'), icon: 'file' },
      ],
    },
    {
      id: 'accounting',
      label: 'Contabilidad',
      superuserOnly: true,
      items: [
        { label: 'Resumen', href: lp('/panel/accounting'), icon: 'credit-card', matchExact: true },
        { label: 'Ingresos', href: lp('/panel/accounting/incomes'), icon: 'plus' },
        { label: 'Gastos', href: lp('/panel/accounting/expenses'), icon: 'file' },
        { label: 'Hostings', href: lp('/panel/accounting/hostings'), icon: 'database' },
        { label: 'Bolsillo', href: lp('/panel/accounting/pocket'), icon: 'folder' },
        { label: 'Recurrentes', href: lp('/panel/accounting/recurring'), icon: 'refresh' },
        { label: 'Ads', href: lp('/panel/accounting/ads'), icon: 'portfolio' },
        { label: 'Tarjetas', href: lp('/panel/accounting/cards'), icon: 'credit-card' },
        { divider: true },
        { label: 'Historial', href: lp('/panel/accounting/history'), icon: 'calendar' },
        { label: 'Configuración', href: lp('/panel/accounting/settings'), icon: 'settings' },
      ],
    },
    {
      id: 'integrations',
      label: 'Integraciones',
      superuserOnly: true,
      items: [
        { label: 'MCPs', href: lp('/panel/mcps'), icon: 'settings' },
      ],
    },
    {
      id: 'reference',
      label: 'Referencia',
      items: [
        { label: 'Mapa de vistas', href: lp('/panel/views'), icon: 'sitemap' },
      ],
    },
    {
      id: 'system',
      label: 'Sistema',
      muted: true,
      items: [
        { label: 'Admins del panel', href: lp('/panel/admins'), icon: 'shield' },
        {
          label: 'Django Admin',
          href: '/admin/',
          icon: 'external',
          external: true,
          openInNewTab: true,
        },
        {
          label: 'Sitemap',
          href: '/sitemap.xml',
          icon: 'sitemap',
          external: true,
          openInNewTab: true,
        },
      ],
    },
  ]
  if (includeSuperuserOnly) return sections
  return sections.filter((section) => !section.superuserOnly)
}
