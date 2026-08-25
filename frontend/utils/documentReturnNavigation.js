const DOCUMENTS_PATH = '/panel/documents';
const LOCALE_PREFIX = /^\/[a-z]{2}(?:-[a-z]{2})?(?=\/)/i;

function firstQueryValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

function normalizedDocumentsPath(path) {
  return String(path || '').replace(LOCALE_PREFIX, '').replace(/\/$/, '') || '/';
}

function positiveInteger(value) {
  const number = Number(firstQueryValue(value));
  return Number.isInteger(number) && number > 0 ? number : null;
}

/**
 * Resolves the editor's `from` query without allowing it to become an open
 * redirect. Only the locale-aware Documents list route is a valid origin.
 */
export function resolveDocumentReturn(rawOrigin, router, fallback) {
  const origin = firstQueryValue(rawOrigin);
  if (typeof origin !== 'string' || !origin.startsWith('/') || origin.startsWith('//')) {
    return { target: fallback, query: {}, hasOrigin: false };
  }

  try {
    const resolved = router.resolve(origin);
    if (normalizedDocumentsPath(resolved.path) !== DOCUMENTS_PATH) {
      return { target: fallback, query: {}, hasOrigin: false };
    }
    return { target: resolved.fullPath, query: resolved.query || {}, hasOrigin: true };
  } catch {
    return { target: fallback, query: {}, hasOrigin: false };
  }
}

/** Adds the row/card to restore without mutating the live list URL. */
export function documentOriginWithFocus(route, router, documentId) {
  const query = { ...route.query, focus: String(documentId) };
  return router.resolve({ path: route.path, query }).fullPath;
}

function shortenedSearch(value) {
  const term = String(firstQueryValue(value) || '').trim();
  if (!term) return '';
  return term.length > 60 ? `${term.slice(0, 57)}…` : term;
}

function scopeSuffix(scope) {
  if (scope === 'archived') return ' (archivados)';
  if (scope === 'all') return ' (activos y archivados)';
  return '';
}

/** Human-readable destination for the editor backlink. */
export function documentReturnLabel({ hasOrigin, query, folderById }) {
  if (!hasOrigin) return 'Volver a Documentos';

  const search = shortenedSearch(query.q);
  if (search) return `Volver a resultados de «${search}»`;

  const scope = firstQueryValue(query.scope) || 'active';
  const folder = firstQueryValue(query.folder);
  const folderId = positiveInteger(folder);
  if (folderId) {
    const name = folderById?.(folderId)?.name;
    if (name) return `Volver a «${name}»${scopeSuffix(scope)}`;
    return `Volver a la carpeta${scopeSuffix(scope)}`;
  }
  if (folder === 'none') return `Volver a Sin carpeta${scopeSuffix(scope)}`;
  if (folder === 'root' || scope === 'archived') return 'Volver a Archivados';
  if (scope === 'all') return 'Volver a activos y archivados';

  const hasFilters = ['tags', 'client', 'project'].some(
    (key) => firstQueryValue(query[key]) != null,
  );
  if (hasFilters) return 'Volver a documentos filtrados';
  return 'Volver a Todos los documentos';
}
