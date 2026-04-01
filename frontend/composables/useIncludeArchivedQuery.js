/**
 * Build relative API path with optional include_archived=1 (admin-only lists on backend).
 * @param {string} path - e.g. `projects/1/deliverables/`
 * @param {Record<string, string|number|boolean|undefined|null>} [params]
 * @param {boolean} [includeArchived]
 */
export function buildPlatformListUrl(path, params = {}, includeArchived = false) {
  const sp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== '') {
      sp.set(key, String(value))
    }
  }
  if (includeArchived) {
    sp.set('include_archived', '1')
  }
  const qs = sp.toString()
  if (!qs) return path
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}${qs}`
}
