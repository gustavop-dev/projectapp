import { computed, ref } from 'vue';
import {
  create_request,
  delete_request,
  get_request,
  patch_request,
} from '~/stores/services/request_http';

const ENDPOINT = 'accounts/saved-filter-tabs/';
const MAX_TABS = 12;
const UPDATE_DEBOUNCE_MS = 400;

/**
 * Persiste pestañas de filtros guardados en el backend (antes localStorage).
 *
 * Cada vista (`proposal`, `client`, `diagnostic`, `view_map`) instancia este
 * helper con su `viewName`. Las pestañas son por (usuario autenticado, view),
 * así un mismo admin las recupera desde cualquier dispositivo.
 *
 * Las llamadas HTTP usan `frontend/stores/services/request_http.js`
 * (sesión Django + CSRF), no la API de plataforma.
 *
 * @param {string} viewName - Uno de: 'proposal' | 'client' | 'diagnostic' | 'view_map'
 */
export function useSavedFilterTabs(viewName) {
  const savedTabs = ref([]);
  const isLoading = ref(false);
  const isReady = ref(false);
  const lastError = ref(null);
  const updateTimers = new Map();

  const isTabLimitReached = computed(() => savedTabs.value.length >= MAX_TABS);

  async function loadTabs() {
    isLoading.value = true;
    lastError.value = null;
    try {
      const { data } = await get_request(`${ENDPOINT}?view=${viewName}`);
      savedTabs.value = Array.isArray(data) ? data : [];
    } catch (err) {
      lastError.value = err;
      savedTabs.value = [];
    } finally {
      isLoading.value = false;
      isReady.value = true;
    }
    return savedTabs.value;
  }

  async function saveTab(name, filters) {
    if (isTabLimitReached.value) return null;
    lastError.value = null;
    try {
      const { data } = await create_request(ENDPOINT, {
        view: viewName,
        name,
        filters,
      });
      savedTabs.value = [...savedTabs.value, data];
      return data;
    } catch (err) {
      lastError.value = err;
      return null;
    }
  }

  function _replaceTab(idx, patch) {
    const copy = [...savedTabs.value];
    copy[idx] = { ...copy[idx], ...patch };
    savedTabs.value = copy;
  }

  function updateTabFilters(tabId, filters) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return;
    const currentJson = JSON.stringify(savedTabs.value[idx].filters);
    const nextJson = JSON.stringify(filters);
    if (currentJson === nextJson) return;

    _replaceTab(idx, { filters, updated_at: new Date().toISOString() });

    if (updateTimers.has(tabId)) clearTimeout(updateTimers.get(tabId));
    const timer = setTimeout(async () => {
      updateTimers.delete(tabId);
      try {
        const { data } = await patch_request(`${ENDPOINT}${tabId}/`, { filters });
        const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
        if (stillThere !== -1) _replaceTab(stillThere, data);
      } catch (err) {
        lastError.value = err;
      }
    }, UPDATE_DEBOUNCE_MS);
    updateTimers.set(tabId, timer);
  }

  async function renameTab(tabId, newName) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return;
    const prev = savedTabs.value[idx].name;
    _replaceTab(idx, { name: newName });
    try {
      const { data } = await patch_request(`${ENDPOINT}${tabId}/`, { name: newName });
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, data);
    } catch (err) {
      lastError.value = err;
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, { name: prev });
    }
  }

  async function deleteTab(tabId) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return;
    const removed = savedTabs.value[idx];
    savedTabs.value = savedTabs.value.filter((t) => t.id !== tabId);
    try {
      await delete_request(`${ENDPOINT}${tabId}/`);
    } catch (err) {
      lastError.value = err;
      savedTabs.value = [
        ...savedTabs.value.slice(0, idx),
        removed,
        ...savedTabs.value.slice(idx),
      ];
    }
  }

  return {
    savedTabs,
    isLoading,
    isReady,
    lastError,
    isTabLimitReached,
    MAX_TABS,
    loadTabs,
    saveTab,
    updateTabFilters,
    renameTab,
    deleteTab,
  };
}
