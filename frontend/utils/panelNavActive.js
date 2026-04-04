/**
 * Panel navigation helpers: locale-prefixed paths and active-state matching.
 */

const LOCALE_PREFIX_RE = /^\/[a-z]{2}(-[a-z]{2})?(?=\/)/

/**
 * @param {string} path
 * @returns {string}
 */
export function stripLocalePrefix(path) {
  if (!path) return ''
  /* c8 ignore next */
  return path.replace(LOCALE_PREFIX_RE, '') || path
}

/**
 * Whether the current route should highlight a nav item.
 * @param {string} routePath - Full path from vue-router (may include locale prefix).
 * @param {{ href: string, matchExact?: boolean, external?: boolean }} item - Resolved item with final href.
 * @returns {boolean}
 */
export function isPanelNavItemActive(routePath, item) {
  if (item.external) return false
  const cleanPath = stripLocalePrefix(routePath).replace(/\/$/, '') || '/'
  const cleanHref = stripLocalePrefix(item.href).replace(/\/$/, '') || '/'
  if (item.matchExact) {
    return cleanPath === cleanHref
  }
  return cleanPath === cleanHref || cleanPath.startsWith(`${cleanHref}/`)
}
