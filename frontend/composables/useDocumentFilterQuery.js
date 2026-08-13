import { watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const SCOPES = ['active', 'archived', 'all'];

/**
 * Sincroniza los dos ejes del gestor de documentos con la URL:
 * `?folder=` (dónde) y `?scope=` (en qué estado).
 *
 * Sin esto, F5 devolvía siempre a Todos/activos y no existían deep links —
 * el resto del panel ya persiste su contexto con `?tab=` (useProposalFilters).
 *
 * Reglas:
 * - Los defaults ('all' / 'active') no se escriben: la URL limpia es la vista
 *   de reposo.
 * - `router.replace`, nunca `push`: navegar carpetas no debe llenar el
 *   historial del navegador.
 * - Mientras hay una búsqueda activa NO se escribe: la búsqueda mueve el
 *   scope a 'all' de forma transitoria y persistirlo dejaría la URL mintiendo
 *   al limpiar el término.
 */
export function useDocumentFilterQuery(documentStore, { isSearching } = {}) {
  const route = useRoute();
  const router = useRouter();

  function parseFolder(raw) {
    if (raw === undefined || raw === null || raw === '') return null;
    if (raw === 'all' || raw === 'root' || raw === 'none') return raw;
    const id = Number(raw);
    return Number.isInteger(id) && id > 0 ? id : null;
  }

  function parseScope(raw) {
    return SCOPES.includes(raw) ? raw : null;
  }

  /**
   * Vuelca el query inicial al store. Debe correr ANTES del primer fetch para
   * que la carga inicial ya pida la carpeta/scope del deep link (un solo fetch).
   */
  function applyQueryToStore() {
    const folder = parseFolder(route.query.folder);
    const scope = parseScope(route.query.scope);
    if (folder !== null) documentStore.activeFolderId = folder;
    if (scope) documentStore.archiveScope = scope;
  }

  /**
   * Tras cargar el árbol: un id de carpeta que ya no existe cae a 'all'.
   * Devuelve true si hubo caída (el caller decide si refetchear).
   */
  function validateFolder(folderStore) {
    const id = documentStore.activeFolderId;
    if (typeof id === 'number' && !folderStore.folderById(id)) {
      documentStore.activeFolderId = 'all';
      return true;
    }
    return false;
  }

  function syncQuery() {
    if (isSearching?.value) return;
    const query = { ...route.query };
    const folder = documentStore.activeFolderId;
    const scope = documentStore.archiveScope;
    if (folder === 'all' || folder == null) delete query.folder;
    else query.folder = String(folder);
    if (scope === 'active') delete query.scope;
    else query.scope = scope;
    if (query.folder === route.query.folder && query.scope === route.query.scope) return;
    router.replace({ query });
  }

  watch(() => [documentStore.activeFolderId, documentStore.archiveScope], syncQuery);

  return { applyQueryToStore, validateFolder };
}
