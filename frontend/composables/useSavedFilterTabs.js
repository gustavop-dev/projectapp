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

function isInactiveValue(value) {
  return (
    value === '' || value === null || value === undefined
    || (Array.isArray(value) && value.length === 0)
  );
}

/**
 * Drop inactive keys (`''` / `null` / `[]`) from a filters dict, and read a
 * one-value dimension the same way however it was stored.
 *
 * Stored tabs carry the page's expanded default shape (every filter key plus
 * `search`) because the auto-save clones the whole `currentFilters`, while
 * seeded `base_filters` stay sparse — both spell the same active filters.
 *
 * The single-element unwrap is what keeps the "drifted" dot honest across the
 * move to multi-value dimensions: a tab written before it holds
 * `kind: 'expected'` and the live panel now holds `kind: ['expected']`. Those
 * are the same cut, and comparing them raw would light the dot on every seeded
 * tab and offer a "Restaurar filtros" that restores nothing.
 */
function canonicalValue(value) {
  return Array.isArray(value) && value.length === 1 ? value[0] : value;
}

export function normalizedFilters(filters) {
  const result = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (!isInactiveValue(value)) result[key] = canonicalValue(value);
  }
  return result;
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((item, i) => deepEqual(item, b[i]));
  }
  if (a && b && typeof a === 'object' && typeof b === 'object'
    && !Array.isArray(a) && !Array.isArray(b)) {
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    return (
      keysA.length === keysB.length
      && keysA.every((key) => deepEqual(a[key], b[key]))
    );
  }
  return false;
}

/** Semantic equality between two filter dicts (key order and inactive keys ignored). */
export function sameFilters(a, b) {
  return deepEqual(normalizedFilters(a), normalizedFilters(b));
}

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
 * @param {string} viewName - Identificador permitido por SavedFilterTab.VIEW_CHOICES.
 */
export function useSavedFilterTabs(viewName) {
  const savedTabs = ref([]);
  const isLoading = ref(false);
  const isReady = ref(false);
  const lastError = ref(null);
  const updateTimers = new Map();

  const isTabLimitReached = computed(() => (
    savedTabs.value.filter((tab) => !tab.builtin_key).length >= MAX_TABS
  ));

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

  async function restoreTab(tabId) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return null;
    // A pending debounced auto-save would overwrite the restore — drop it.
    if (updateTimers.has(tabId)) {
      clearTimeout(updateTimers.get(tabId));
      updateTimers.delete(tabId);
    }
    lastError.value = null;
    try {
      const base = savedTabs.value[idx].base_filters || {};
      const { data } = await patch_request(`${ENDPOINT}${tabId}/`, { filters: base });
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, data);
      return data;
    } catch (err) {
      lastError.value = err;
      return null;
    }
  }

  async function rebaseTab(tabId) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return null;
    lastError.value = null;
    try {
      const current = savedTabs.value[idx].filters || {};
      const { data } = await patch_request(
        `${ENDPOINT}${tabId}/`, { base_filters: current },
      );
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, data);
      return data;
    } catch (err) {
      lastError.value = err;
      return null;
    }
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

  /** Patch a single stored attribute (visibility, for now). */
  async function updateTab(tabId, patch) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return null;
    const previous = { ...savedTabs.value[idx] };
    _replaceTab(idx, patch);
    try {
      const { data } = await patch_request(`${ENDPOINT}${tabId}/`, patch);
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, data);
      return data;
    } catch (err) {
      lastError.value = err;
      const stillThere = savedTabs.value.findIndex((t) => t.id === tabId);
      if (stillThere !== -1) _replaceTab(stillThere, previous);
      return null;
    }
  }

  /**
   * Apply the strip's order, top to bottom.
   *
   * `ids` is what the caller can see, which is rarely everything: the strip
   * leaves out hidden tabs and, in a two-level view, every tab outside the
   * active module. The server numbers positions straight from the list it
   * receives, so passing a subset through would renumber it from zero and
   * collide with the tabs left out. The visible sequence is therefore woven
   * back into the full list, keeping the slots of everything it never names.
   *
   * An id matches a saved tab by `id`, or a builtin's placeholder row by its
   * `builtin_key` — the strip knows a builtin by its code-level string id.
   */
  async function reorderTabs(ids) {
    const wanted = (ids || []).map(String);
    const full = [...savedTabs.value].sort((a, b) => (a.order || 0) - (b.order || 0));

    const rowFor = (id) => full.find((tab) => (
      tab.builtin_key ? String(tab.builtin_key) === id : String(tab.id) === id
    ));
    const moving = wanted.map(rowFor).filter(Boolean);
    if (!moving.length) return false;

    const movingIds = new Set(moving.map((tab) => tab.id));
    const slots = [];
    full.forEach((tab, index) => {
      if (movingIds.has(tab.id)) slots.push(index);
    });
    const merged = [...full];
    slots.forEach((slot, i) => { merged[slot] = moving[i]; });

    lastError.value = null;
    try {
      const { data } = await create_request(`${ENDPOINT}reorder/`, {
        view: viewName, ids: merged.map((tab) => tab.id),
      });
      savedTabs.value = Array.isArray(data) ? data : savedTabs.value;
      return true;
    } catch (err) {
      lastError.value = err;
      // Snap the strip back. The drag already moved the chip on screen, and
      // the strip mirrors this list to know better; leaving the list byte
      // for byte identical would tell it nothing happened, and the rejected
      // order would sit there looking saved until the next reload undid it.
      // A fresh array is what makes the mirror re-read the real order.
      savedTabs.value = [...savedTabs.value];
      return false;
    }
  }

  /**
   * Put the factory tabs back. The server keeps the user's own: only the
   * seeded rows are rebuilt.
   */
  async function resetTabs() {
    lastError.value = null;
    try {
      const { data } = await create_request(`${ENDPOINT}reset/`, {
        view: viewName,
      });
      savedTabs.value = Array.isArray(data) ? data : [];
      return true;
    } catch (err) {
      lastError.value = err;
      return false;
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
    updateTab,
    reorderTabs,
    resetTabs,
    restoreTab,
    rebaseTab,
    renameTab,
    deleteTab,
  };
}
