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
export function resolveBlogPublishMode(data, now = new Date()) {
  if (data?.is_published) {
    return { mode: 'now', scheduledIso: null, overdue: false };
  }
  if (data?.published_at) {
    const at = new Date(data.published_at);
    const iso = at.toISOString().slice(0, 16);
    if (at > now) {
      return { mode: 'schedule', scheduledIso: iso, overdue: false };
    }
    return { mode: 'schedule', scheduledIso: iso, overdue: true };
  }
  return { mode: 'draft', scheduledIso: null, overdue: false };
}
