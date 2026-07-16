// Minimal **bold** renderer for admin-authored text shown via v-html.
// The PDF pipeline already parses **x** (pdf_utils bullet lists); this keeps
// the web rendering consistent with a single source text. ALL HTML is escaped
// first, so the produced markup can only ever contain <strong> tags.
export function renderInlineBold(text) {
  const escaped = String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
  return escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}
