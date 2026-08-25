import { nextTick, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { DEFAULT_SCOPE, DOCUMENT_SCOPES } from '~/utils/archiveScope';

const CONTROLLED_QUERY_KEYS = [
  'folder', 'scope', 'tags', 'client', 'project', 'q', 'order', 'view', 'page', 'focus',
];

function firstQueryValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

function positiveInteger(value) {
  const number = Number(firstQueryValue(value));
  return Number.isInteger(number) && number > 0 ? number : null;
}

function sameIds(left, right) {
  const normalizedLeft = [...left].map(Number).sort((a, b) => a - b);
  const normalizedRight = [...right].map(Number).sort((a, b) => a - b);
  return normalizedLeft.length === normalizedRight.length
    && normalizedLeft.every((id, index) => id === normalizedRight[index]);
}

function sameQueryValue(left, right) {
  return JSON.stringify(left ?? null) === JSON.stringify(right ?? null);
}

/**
 * Hace que la URL sea la fuente reproducible del listado de documentos.
 *
 * Además de los ejes de datos (`folder`, `scope`, asociaciones y etiquetas),
 * conserva búsqueda, orden, presentación, página y la fila/tarjeta a recuperar.
 * Así un enlace al editor puede llevar una dirección completa en `from` y el
 * historial del navegador puede reconstruir la misma vista sin memoria global.
 */
export function useDocumentFilterQuery(documentStore, {
  searchQuery,
  viewMode,
  currentPage,
  focusedDocumentId,
  onNavigate,
} = {}) {
  const route = useRoute();
  const router = useRouter();
  const isApplyingQuery = ref(false);

  function parseFolder(raw) {
    const value = firstQueryValue(raw);
    if (value === undefined || value === null || value === '') return null;
    if (value === 'all' || value === 'root' || value === 'none') return value;
    return positiveInteger(value);
  }

  function parseScope(raw) {
    const value = firstQueryValue(raw);
    return DOCUMENT_SCOPES.includes(value) ? value : null;
  }

  function parseAssociation(raw) {
    const value = firstQueryValue(raw);
    if (value === undefined || value === null || value === '') return null;
    if (value === 'none') return 'none';
    return positiveInteger(value);
  }

  function parseTags(raw) {
    const value = firstQueryValue(raw);
    if (typeof value !== 'string' || !value.trim()) return [];
    return [...new Set(value.split(',').map(positiveInteger).filter(Boolean))]
      .sort((left, right) => left - right);
  }

  function parseSearch(raw) {
    const value = firstQueryValue(raw);
    return typeof value === 'string' ? value.trim() : '';
  }

  function parseOrder(raw) {
    return firstQueryValue(raw) === 'oldest' ? 'oldest' : 'recent';
  }

  function parseView(raw) {
    return firstQueryValue(raw) === 'grid' ? 'grid' : 'list';
  }

  /**
   * Vuelca el query en todos los estados visibles. Devuelve un resumen para que
   * atrás/adelante sólo repida el fetch o la búsqueda cuando realmente hace
   * falta y no por cambios de página, vista o foco.
   */
  function applyQueryToStore() {
    const nextState = {
      folder: parseFolder(route.query.folder) ?? 'all',
      scope: parseScope(route.query.scope) ?? DEFAULT_SCOPE,
      tags: parseTags(route.query.tags),
      client: parseAssociation(route.query.client),
      project: parseAssociation(route.query.project),
      search: parseSearch(route.query.q),
      order: parseOrder(route.query.order),
      view: parseView(route.query.view),
      page: positiveInteger(route.query.page) ?? 1,
      focus: positiveInteger(route.query.focus),
    };

    const summary = {
      filtersChanged: documentStore.activeFolderId !== nextState.folder
        || documentStore.archiveScope !== nextState.scope
        || !sameIds(documentStore.activeTagIds || [], nextState.tags)
        || documentStore.activeClientId !== nextState.client
        || documentStore.activeProjectId !== nextState.project
        || documentStore.archivedOrder !== nextState.order,
      searchChanged: !!searchQuery && searchQuery.value !== nextState.search,
      viewChanged: !!viewMode && viewMode.value !== nextState.view,
      pageChanged: !!currentPage && currentPage.value !== nextState.page,
      focusChanged: !!focusedDocumentId && focusedDocumentId.value !== nextState.focus,
    };
    summary.changed = Object.values(summary).some(Boolean);

    isApplyingQuery.value = true;
    documentStore.activeFolderId = nextState.folder;
    documentStore.archiveScope = nextState.scope;
    documentStore.activeTagIds = nextState.tags;
    documentStore.activeClientId = nextState.client;
    documentStore.activeProjectId = nextState.project;
    documentStore.archivedOrder = nextState.order;
    if (searchQuery) searchQuery.value = nextState.search;
    if (viewMode) viewMode.value = nextState.view;
    if (currentPage) currentPage.value = nextState.page;
    if (focusedDocumentId) focusedDocumentId.value = nextState.focus;

    // Normaliza basura y defaults escritos a mano. Los watchers originados por
    // estas asignaciones convergen en el mismo query y no agregan historial.
    syncQuery();
    nextTick(() => { isApplyingQuery.value = false; });
    return summary;
  }

  /** Una carpeta borrada ya no es un destino reproducible: cae a Todos. */
  function validateFolder(folderStore) {
    const id = documentStore.activeFolderId;
    if (typeof id === 'number' && !folderStore.folderById(id)) {
      documentStore.activeFolderId = 'all';
      return true;
    }
    return false;
  }

  function syncQuery() {
    const query = { ...route.query };
    const folder = documentStore.activeFolderId;
    const scope = documentStore.archiveScope;
    const tags = [...new Set(documentStore.activeTagIds || [])]
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0)
      .sort((left, right) => left - right);
    const client = documentStore.activeClientId;
    const project = documentStore.activeProjectId;
    const search = searchQuery?.value?.trim() || '';
    const order = documentStore.archivedOrder;
    const view = viewMode?.value;
    const page = currentPage?.value;
    const focus = focusedDocumentId?.value;

    if (folder === 'all' || folder == null) delete query.folder;
    else query.folder = String(folder);
    if (scope === DEFAULT_SCOPE) delete query.scope;
    else query.scope = scope;
    if (tags.length) query.tags = tags.join(',');
    else delete query.tags;
    if (client == null) delete query.client;
    else query.client = String(client);
    if (project == null) delete query.project;
    else query.project = String(project);
    if (search) query.q = search;
    else delete query.q;
    if (order === 'oldest') query.order = 'oldest';
    else delete query.order;
    if (view === 'grid') query.view = 'grid';
    else delete query.view;
    if (Number.isInteger(page) && page > 1) query.page = String(page);
    else delete query.page;
    if (Number.isInteger(focus) && focus > 0) query.focus = String(focus);
    else delete query.focus;

    if (CONTROLLED_QUERY_KEYS.every(
      (key) => sameQueryValue(query[key], route.query[key]),
    )) return;
    router.replace({ query });
  }

  watch(() => [
    documentStore.activeFolderId,
    documentStore.archiveScope,
    documentStore.activeTagIds,
    documentStore.activeClientId,
    documentStore.activeProjectId,
    documentStore.archivedOrder,
    searchQuery?.value,
    viewMode?.value,
    currentPage?.value,
    focusedDocumentId?.value,
  ], syncQuery, { deep: true });

  // El otro sentido: un popstate aplica la dirección completa y avisa al
  // listado qué clase de trabajo necesita repetir.
  watch(() => CONTROLLED_QUERY_KEYS.map((key) => route.query[key]), () => {
    const summary = applyQueryToStore();
    if (summary.changed) onNavigate?.(summary);
  }, { deep: true });

  return {
    applyQueryToStore,
    validateFolder,
    isApplyingQuery,
    syncQuery,
  };
}
