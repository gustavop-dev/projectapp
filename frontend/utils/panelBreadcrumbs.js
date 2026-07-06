/**
 * Breadcrumb + browser-title resolution for the admin layout.
 *
 * Labels derive from panelNav (single source of route knowledge), so any
 * route added to the sidebar automatically gets a breadcrumb. This module
 * only keeps:
 *  - Spanish display overrides where the short title differs from the nav
 *    label (nav labels are English; titles are pinned in Spanish by
 *    e2e/admin/admin-layout-title-mapping.spec.js), and
 *  - dynamic `:id/edit` routes, which cannot live in the nav.
 */
import { isPanelNavItemActive, stripLocalePrefix } from '~/utils/panelNavActive'

export const PANEL_BREADCRUMB_LABELS = {
  '/panel/proposals': 'Propuestas',
  '/panel/proposals/create': 'Nueva prop.',
  '/panel/proposals/email-deliverability': 'Entregabilidad',
  '/panel/proposals/email-templates': 'Plantillas',
  '/panel/proposals/defaults': 'Prop. defaults',
  '/panel/diagnostics': 'Diagnósticos',
  '/panel/diagnostics/create': 'Nuevo diag.',
  '/panel/diagnostics/defaults': 'Diag. defaults',
  '/panel/blog/calendar': 'Calendario',
  '/panel/blog/create': 'Nuevo post',
  '/panel/portfolio/create': 'Nuevo item',
  '/panel/documents': 'Documentos',
  '/panel/documents/create': 'Nuevo doc.',
  '/panel/clients': 'Clientes',
  '/panel/views': 'Mapa',
  '/panel/admins': 'Admins',
  '/panel/accounting': 'Resumen',
  '/panel/accounting/incomes': 'Ingresos',
  '/panel/accounting/expenses': 'Gastos',
  '/panel/accounting/pocket': 'Bolsillo',
  '/panel/accounting/recurring': 'Recurrentes',
  '/panel/accounting/cards': 'Tarjetas',
  '/panel/accounting/history': 'Historial',
  '/panel/accounting/settings': 'Config. contable',
}

// Dynamic :id/edit routes carry only their display label; the breadcrumb
// SECTION comes from the closest nav ancestor (e.g. /panel/blog), so a
// section rename in panelNav propagates here without edits.
export const PANEL_BREADCRUMB_DYNAMIC = [
  { re: /^\/panel\/proposals\/[^/]+\/edit/, label: 'Edit. propuesta' },
  { re: /^\/panel\/diagnostics\/[^/]+\/edit/, label: 'Edit. diagnóstico' },
  { re: /^\/panel\/blog\/[^/]+\/edit/, label: 'Edit. post' },
  { re: /^\/panel\/portfolio\/[^/]+\/edit/, label: 'Edit. portfolio' },
  { re: /^\/panel\/documents\/[^/]+\/edit/, label: 'Edit. documento' },
]

function cleanPath(path) {
  return stripLocalePrefix(path || '').replace(/\/$/, '') || '/'
}

function bestNavMatch(path, sections) {
  // Longest matching nav href wins, so /panel/proposals/create resolves to
  // the "New proposal" item rather than the "Proposals" prefix.
  let best = null
  for (const section of sections || []) {
    for (const item of section.items || []) {
      if (item.divider || item.external) continue
      if (!isPanelNavItemActive(path, item)) continue
      const href = cleanPath(item.href)
      if (!best || href.length > best.href.length) {
        best = { item, section, href }
      }
    }
  }
  return best
}

/**
 * Resolve `{ label, section }` for a panel route, or `null` when the route
 * has no breadcrumb (unknown paths keep the plain "Project App" title).
 *
 * @param {string} routePath - Full path from vue-router (may include locale prefix).
 * @param {Array<{ label: string, items: Array }>} sections - Output of getPanelNavSections().
 */
export function resolvePanelBreadcrumb(routePath, sections) {
  const path = cleanPath(routePath)

  for (const { re, label } of PANEL_BREADCRUMB_DYNAMIC) {
    if (re.test(path)) {
      const ancestor = bestNavMatch(path, sections)
      return { label, section: ancestor ? ancestor.section.label : null }
    }
  }

  const best = bestNavMatch(path, sections)

  // Direct overrides also cover sub-routes that have no nav item of their
  // own (create pages, redirect stubs); their section comes from the
  // closest nav ancestor.
  const direct = PANEL_BREADCRUMB_LABELS[path]
  if (direct) {
    return { label: direct, section: best ? best.section.label : null }
  }

  if (!best) return null
  const label = PANEL_BREADCRUMB_LABELS[best.href] ?? best.item.label
  return { label, section: best.section.label }
}
