/**
 * Eje de estado del gestor de documentos: activo, archivado o los dos.
 *
 * Vive aparte de los stores porque lo consultan los dos (documentos y carpetas)
 * y la página, y porque «qué está en la cima del listado» es una sola regla que
 * no debe reimplementarse por tipo de fila.
 */

export const DOCUMENT_SCOPES = ['all', 'active', 'archived'];

export const DEFAULT_SCOPE = 'active';

/** Normaliza un scope desconocido a `active`, que es el estado en reposo. */
export function normalizeScope(value) {
  return DOCUMENT_SCOPES.includes(value) ? value : DEFAULT_SCOPE;
}

/** ¿La fila pertenece al scope pedido? `all` acepta todo. */
export function matchesScope(entity, scope) {
  if (!entity) return false;
  if (scope === 'all') return true;
  return !!entity.is_archived === (scope === 'archived');
}

/**
 * ¿El elemento está en la cima del listado actual?
 *
 * Lo está cuando su contenedor no existe, no se encuentra, o **no pertenece al
 * scope actual** — es decir, cuando no hay ninguna fila de carpeta encima suyo
 * donde pudiera vivir. Ese tercer caso es también la red de seguridad del
 * invariante: lo que se salga de scope aflora en la raíz en vez de desaparecer.
 *
 * @param {number|null} containerId  id de la carpeta contenedora
 * @param {Function} findContainer   (id) => carpeta | null
 * @param {string} scope             'all' | 'active' | 'archived'
 */
export function isRootInScope(containerId, findContainer, scope) {
  if (containerId == null) return true;
  const container = findContainer(containerId);
  if (!container) return true;
  return !matchesScope(container, scope);
}
