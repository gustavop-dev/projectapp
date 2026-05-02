/**
 * Resolve the admin "publish mode" UI state from a blog post payload.
 *
 * Returns one of:
 *   { mode: 'now',      scheduledIso: null,  overdue: false }
 *   { mode: 'schedule', scheduledIso: '...', overdue: false }   // future
 *   { mode: 'schedule', scheduledIso: '...', overdue: true  }   // past, awaiting safety-net
 *   { mode: 'draft',    scheduledIso: null,  overdue: false }
 *
 * The "overdue" branch exists so the UI can show the post as
 * "Programado pendiente" instead of "Borrador" while the periodic
 * Huey safety-net catches up (typically <60s).
 *
 * @param {{ is_published?: boolean, published_at?: string | null }} data
 * @param {Date} [now=new Date()]  Injectable for tests.
 */
function _toLocalISO(date) {
  const pad = n => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function resolveBlogPublishMode(data, now = new Date()) {
  if (data?.is_published) {
    return { mode: 'now', scheduledIso: null, overdue: false };
  }
  if (data?.published_at) {
    const at = new Date(data.published_at);
    const iso = _toLocalISO(at);
    if (at > now) {
      return { mode: 'schedule', scheduledIso: iso, overdue: false };
    }
    return { mode: 'schedule', scheduledIso: iso, overdue: true };
  }
  return { mode: 'draft', scheduledIso: null, overdue: false };
}
