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
      id: 'commercial',
      label: 'Sales',
      items: [
        { label: 'Proposals', href: lp('/panel/proposals'), icon: 'folder' },
        { label: 'New proposal', href: lp('/panel/proposals/create'), icon: 'plus' },
        { label: 'Clients', href: lp('/panel/clients'), icon: 'users' },
        { label: 'Proposal defaults', href: lp('/panel/proposals/defaults'), icon: 'settings' },
        { label: 'Email deliverability', href: lp('/panel/proposals/email-deliverability'), icon: 'mail' },
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
