/**
 * Admin panel navigation: section definitions. Paths are i18n keys; resolve with localePath().
 * @param {(path: string) => string} localePath - Nuxt i18n localePath composable
 * @returns {Array<{ id: string, label: string, muted?: boolean, items: Array<NavItem> }>}
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

export function getPanelNavSections(localePath) {
  const lp = localePath
  return [
    {
      id: 'overview',
      label: 'Overview',
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
      label: 'Tasks',
      items: [
        { label: 'Kanban', href: lp('/panel/tasks'), icon: 'board' },
      ],
    },
    {
      id: 'commercial',
      label: 'Sales',
      items: [
        { label: 'Defaults', href: lp('/panel/defaults'), icon: 'settings' },
        { label: 'Clients', href: lp('/panel/clients'), icon: 'users' },
        { label: 'Email deliverability', href: lp('/panel/proposals/email-deliverability'), icon: 'mail' },
        { label: 'Proposals', href: lp('/panel/proposals'), icon: 'folder' },
        { label: 'New proposal', href: lp('/panel/proposals/create'), icon: 'plus' },
        { divider: true },
        { label: 'Diagnostics', href: lp('/panel/diagnostics'), icon: 'file' },
        { label: 'New diagnostic', href: lp('/panel/diagnostics/create'), icon: 'plus' },
      ],
    },
    {
      id: 'site',
      label: 'Website content',
      items: [
        { label: 'Blog', href: lp('/panel/blog'), icon: 'blog' },
        { label: 'Blog calendar', href: lp('/panel/blog/calendar'), icon: 'calendar' },
        { label: 'Portfolio', href: lp('/panel/portfolio'), icon: 'portfolio' },
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
      label: 'Documents',
      items: [
        { label: 'PDF documents', href: lp('/panel/documents'), icon: 'file' },
      ],
    },
    {
      id: 'accounting',
      label: 'Accounting',
      superuserOnly: true,
      items: [
        { label: 'Overview', href: lp('/panel/accounting'), icon: 'credit-card', matchExact: true },
        { label: 'Incomes', href: lp('/panel/accounting/incomes'), icon: 'plus' },
        { label: 'Expenses', href: lp('/panel/accounting/expenses'), icon: 'file' },
        { label: 'Hostings', href: lp('/panel/accounting/hostings'), icon: 'database' },
        { label: 'Pocket', href: lp('/panel/accounting/pocket'), icon: 'folder' },
        { label: 'Recurring', href: lp('/panel/accounting/recurring'), icon: 'refresh' },
        { label: 'Ads', href: lp('/panel/accounting/ads'), icon: 'portfolio' },
        { divider: true },
        { label: 'History', href: lp('/panel/accounting/history'), icon: 'calendar' },
        { label: 'Settings', href: lp('/panel/accounting/settings'), icon: 'settings' },
      ],
    },
    {
      id: 'reference',
      label: 'Reference',
      items: [
        { label: 'View map', href: lp('/panel/views'), icon: 'sitemap' },
      ],
    },
    {
      id: 'system',
      label: 'System',
      muted: true,
      items: [
        { label: 'Panel admins', href: lp('/panel/admins'), icon: 'shield' },
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
}
