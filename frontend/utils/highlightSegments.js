/**
 * Split `text` into segments marking the case-insensitive occurrences of
 * `query`. Returns [{ text, hit }] — consumers render `hit` segments
 * highlighted (see components/ui/HighlightText.vue).
 */
export function highlightSegments(text, query) {
  const source = String(text ?? '');
  const needle = String(query ?? '').trim();
  if (!source || !needle) {
    return [{ text: source, hit: false }];
  }
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`(${escaped})`, 'gi');
  return source
    .split(pattern)
    .filter((part) => part !== '')
    .map((part) => ({
      text: part,
      hit: part.toLowerCase() === needle.toLowerCase(),
    }));
}
