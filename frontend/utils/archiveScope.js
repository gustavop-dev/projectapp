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

/**
 * Scope que define el ÁRBOL en que se mira, dado el scope que se está CONTANDO.
 *
 * Son dos ejes distintos y confundirlos es lo que rompe los contadores. El scope
 * de conteo dice qué documentos se suman; éste dice por qué carpetas se puede
 * bajar, y es el mismo con que `isRootInScope` decide qué fila queda en la cima.
 * Vive pegado a esa función porque son las dos mitades de una sola regla.
 *
 * Sólo el modo activo se mira en su propio árbol. Los otros dos se miran en el
 * árbol completo: una carpeta ACTIVA puede guardar documentos archivados (el
 * estado mixto que deja una restauración por cadena), y recorrer sólo carpetas
 * archivadas los dejaría sin contar en ninguna fila.
 *
 * El resultado es siempre superconjunto del scope de conteo — si no lo fuera,
 * habría carpetas cuyo contenido se cuenta pero por las que no se puede bajar.
 */
export function treeScopeFor(scope) {
  return normalizeScope(scope) === 'active' ? 'active' : 'all';
}
