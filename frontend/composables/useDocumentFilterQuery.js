import { watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { DEFAULT_SCOPE, DOCUMENT_SCOPES } from '~/utils/archiveScope';

/**
 * Sincroniza los ejes del gestor de documentos con la URL:
 * `?folder=` (dónde), `?scope=` (en qué estado) y `?client=` / `?project=`
 * (de quién — el salto desde /panel/clients entra por aquí).
 *
 * Sin esto, F5 devolvía siempre a Todos/activos y no existían deep links —
 * el resto del panel ya persiste su contexto con `?tab=` (useProposalFilters).
 *
 * Reglas:
 * - Los defaults ('all' / 'active') no se escriben: la URL limpia es la vista
 *   de reposo.
 * - La URL manda en los dos sentidos. Es la regla que faltaba: el store sobrevivía
 *   a salir del módulo y volver por el menú dejaba una carpeta vieja seleccionada
 *   bajo una URL que decía «Todos», y atrás/adelante movían la barra de
 *   direcciones sin mover la vista.
 * - `router.replace`, nunca `push`: navegar carpetas no debe llenar el
 *   historial del navegador.
 * - Mientras hay una búsqueda activa NO se toca nada: la búsqueda mueve el
 *   scope a 'all' de forma transitoria y persistirlo dejaría la URL mintiendo
 *   al limpiar el término.
 *
 * @param {object} documentStore
 * @param {object}   [options]
 * @param {import('vue').Ref<boolean>} [options.isSearching]
 * @param {Function} [options.onNavigate]  se llama cuando la URL cambió la vista
 *                                         por fuera del store (atrás/adelante).
 */
export function useDocumentFilterQuery(documentStore, { isSearching, onNavigate } = {}) {
  const route = useRoute();
  const router = useRouter();

  function parseFolder(raw) {
    if (raw === undefined || raw === null || raw === '') return null;
    if (raw === 'all' || raw === 'root' || raw === 'none') return raw;
    const id = Number(raw);
    return Number.isInteger(id) && id > 0 ? id : null;
  }

  function parseScope(raw) {
    return DOCUMENT_SCOPES.includes(raw) ? raw : null;
  }

  // Ejes de asociación (?client= / ?project=): null (sin filtro), 'none'
  // (sin asociar) o un id. Basura cae a null, mismo criterio permisivo que
  // parseFolder: un deep link roto no debe romper la vista.
  function parseAssociation(raw) {
    if (raw === undefined || raw === null || raw === '') return null;
    if (raw === 'none') return 'none';
    const id = Number(raw);
    return Number.isInteger(id) && id > 0 ? id : null;
  }

  /**
   * Vuelca el query al store. Debe correr ANTES del primer fetch para que la
   * carga inicial ya pida la carpeta/scope del deep link (un solo fetch).
   *
   * Asigna SIEMPRE, también cuando el param falta: un valor ausente en la URL
   * significa «el default», no «deja lo que hubiera». Con la asignación
   * condicional, volver al módulo con la URL limpia conservaba la carpeta de la
   * visita anterior y la vista contradecía a la barra de direcciones.
   *
   * @returns {boolean} si la vista cambió.
   */
  function applyQueryToStore() {
    const folder = parseFolder(route.query.folder) ?? 'all';
    const scope = parseScope(route.query.scope) ?? DEFAULT_SCOPE;
    const client = parseAssociation(route.query.client);
    const project = parseAssociation(route.query.project);
    const changed = documentStore.activeFolderId !== folder
      || documentStore.archiveScope !== scope
      || documentStore.activeClientId !== client
      || documentStore.activeProjectId !== project;
    documentStore.activeFolderId = folder;
    documentStore.archiveScope = scope;
    documentStore.activeClientId = client;
    documentStore.activeProjectId = project;
    // Normaliza lo que se haya escrito a mano (`?scope=active`, basura): la URL
    // tiene que reproducir la vista, ni más ni menos.
    syncQuery();
    return changed;
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
    const client = documentStore.activeClientId;
    const project = documentStore.activeProjectId;
    if (folder === 'all' || folder == null) delete query.folder;
    else query.folder = String(folder);
    if (scope === 'active') delete query.scope;
    else query.scope = scope;
    if (client == null) delete query.client;
    else query.client = String(client);
    if (project == null) delete query.project;
    else query.project = String(project);
    if (
      query.folder === route.query.folder && query.scope === route.query.scope
      && query.client === route.query.client && query.project === route.query.project
    ) return;
    router.replace({ query });
  }

  watch(() => [
    documentStore.activeFolderId, documentStore.archiveScope,
    documentStore.activeClientId, documentStore.activeProjectId,
  ], syncQuery);

  // El otro sentido: atrás/adelante del navegador cambian la URL sin pasar por
  // el store. Converge porque volcar valores que ya están puestos no dispara el
  // watcher de arriba, y `syncQuery` no reescribe un query que ya es el suyo.
  watch(() => [
    route.query.folder, route.query.scope,
    route.query.client, route.query.project,
  ], () => {
    if (isSearching?.value) return;
    if (applyQueryToStore()) onNavigate?.();
  });

  return { applyQueryToStore, validateFolder };
}
