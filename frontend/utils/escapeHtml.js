// Canonical HTML escape for admin-authored text that later goes through
// v-html (after whitelisted transforms like linkify or **bold**). Keep this
// as the single copy — duplicated escape chains drift and drift is an XSS.
export function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
