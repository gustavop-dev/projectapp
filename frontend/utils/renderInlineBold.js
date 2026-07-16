import { escapeHtml } from '~/utils/escapeHtml';

// Minimal **bold** renderer for admin-authored text shown via v-html.
// The PDF pipeline already parses **x** (pdf_utils bullet lists); this keeps
// the web rendering consistent with a single source text. ALL HTML is escaped
// first, so the produced markup can only ever contain <strong> tags.
export function renderInlineBold(text) {
  return escapeHtml(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}
