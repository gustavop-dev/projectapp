/**
 * Client-side slug helper matching Django's `slugify` semantics closely
 * enough for previews and admin-side regeneration (strip diacritics,
 * lowercase, collapse non-alphanumerics to single dashes, trim dashes,
 * apply a max length and a fallback).
 *
 * The canonical slug the server accepts is still what `django.utils.text.slugify`
 * produces; this helper is only used for UI previews and live regeneration.
 */
export function toSlug(value, { maxLength = 120, fallback = '' } = {}) {
  const raw = String(value ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, maxLength);
  return raw || fallback;
}
