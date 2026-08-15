import { computed, getCurrentScope, onMounted, onScopeDispose, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

/**
 * Generalization of useClientFilters into a factory reusable by the
 * accounting subviews (incomes, expenses, hostings, pocket, recurring, ads).
 *
 * Filtering is declarative: `matchers` maps a filter key to a predicate
 * `(record, filterValue, allFilters) => boolean` that only runs when the
 * corresponding filter value differs from its default. Range matchers built
 * with the exported helpers attach a `.keys` list so a single matcher entry
 * (e.g. `amountRange`) activates when either bound key (min/max) is set and
 * counts once in `activeFilterCount`.
 *
 * Saved tabs degrade gracefully: `useSavedFilterTabs` traps HTTP errors
 * internally (exposed via `lastError`), and the mount-time load is wrapped
 * so a failing tabs API never breaks the page's local filtering.
 */

function normalizeScalar(value) {
  return value === '' || value === undefined ? null : value;
}

function isValueActive(value, defaultValue) {
  if (Array.isArray(value)) {
    const def = Array.isArray(defaultValue) ? defaultValue : [];
    if (value.length !== def.length) return value.length > 0 || def.length > 0;
    return JSON.stringify(value) !== JSON.stringify(def);
  }
  return normalizeScalar(value) !== normalizeScalar(defaultValue);
}

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

// ---------------------------------------------------------------------------
// Prebuilt matcher helpers
// ---------------------------------------------------------------------------

/** Inclusive date range; the max bound extends to end-of-day (23:59:59.999). */
export function matchDateRange(field, minKey, maxKey) {
  const fn = (record, _value, filters) => {
    const min = filters[minKey];
    const max = filters[maxKey];
    if (!min && !max) return true;
    if (!record[field]) return false;
    const d = new Date(record[field]);
    if (Number.isNaN(d.getTime())) return false;
    if (min && d < new Date(min)) return false;
    if (max) {
      const end = new Date(max);
      end.setHours(23, 59, 59, 999);
      if (d > end) return false;
    }
    return true;
  };
  fn.keys = [minKey, maxKey];
  return fn;
}

/** Inclusive numeric range over a record field (numbers or numeric strings). */
export function matchNumberRange(field, minKey, maxKey) {
  const fn = (record, _value, filters) => {
    const min = normalizeScalar(filters[minKey]);
    const max = normalizeScalar(filters[maxKey]);
    if (min === null && max === null) return true;
    const n = toNumber(record[field]);
    if (min !== null && n < Number(min)) return false;
    if (max !== null && n > Number(max)) return false;
    return true;
  };
  fn.keys = [minKey, maxKey];
  return fn;
}

/** Multi-select: record field (scalar or array) intersects the selected array. */
export function matchIncludes(field, key) {
  const fn = (record, _value, filters) => {
    const selected = filters[key];
    if (!Array.isArray(selected) || selected.length === 0) return true;
    const recordValue = record[field];
    if (Array.isArray(recordValue)) return recordValue.some((v) => selected.includes(v));
    return selected.includes(recordValue);
  };
  fn.keys = [key];
  return fn;
}

/** Strict equality against a single-value filter (null/'' means inactive). */
export function matchEquals(field, key) {
  const fn = (record, _value, filters) => {
    const selected = normalizeScalar(filters[key]);
    if (selected === null) return true;
    return record[field] === selected;
  };
  fn.keys = [key];
  return fn;
}

/** Tri-state boolean: '' matches all, 'true'/'false' match the boolean field. */
export function matchBoolean(field, key) {
  const fn = (record, _value, filters) => {
    const selected = filters[key];
    if (selected === '' || selected === null || selected === undefined) return true;
    return record[field] === (selected === 'true');
  };
  fn.keys = [key];
  return fn;
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

export function useAccountingFilters({
  viewName,
  defaults = {},
  matchers = {},
  searchFields = [],
  // Fixed quick-filter tabs rendered before the saved ones. Items are
  // `{ id, name, filters }` with non-numeric string ids ('lost'); they are
  // never persisted server-side and cannot be renamed or deleted.
  builtinTabs = [],
  // Tab the view lands on with no `?<viewName>Tab` in the URL. Only 'all' or a
  // builtin id make sense here: saved-tab ids are per-user database rows.
  defaultTabId = 'all',
  // Deep-link params this view is seeded with once (`project`, `client`,
  // `focus`). See `consumeParam`.
  ephemeralParams = [],
  // Query param carrying the active tab. Defaults to `<viewName>Tab`; views
  // whose name is long enough to make an ugly URL can shorten it.
  tabQueryParam = `${viewName}Tab`,
  // Put the active filters in the URL too, not just the tab, so a query can
  // be bookmarked and shared. Off by default: the views that filter in the
  // browser already restore their state from the tab alone.
  syncFiltersToUrl = false,
  // With two instances on one page (Historial's two subtabs), only the one on
  // screen owns the query string — otherwise both would write the keys they
  // share and overwrite each other.
  isUrlOwner = () => true,
  // Keys to clear before writing. Defaults to this instance's own; a page
  // with several instances passes the union so switching between them cannot
  // leave the previous one's filters behind.
  urlFilterKeys = null,
  // Opt-in second level. When set, it names the filter key holding the active
  // module and `displayTabs` only lists the tabs belonging to it, so a view can
  // group its quick filters instead of laying them out flat. Views that leave
  // it null behave exactly as before.
  moduleKey = null,
  defaultModule = 'all',
  // Query param carrying the active module, same shortening rationale as
  // `tabQueryParam`.
  moduleQueryParam = `${viewName}Module`,
  // Optional migration hook applied to a stored tab's filters before they are
  // loaded, for keys whose shape changed after the tab was saved.
  normalizeFilters = null,
} = {}) {
  const route = useRoute();
  const router = useRouter();

  const DEFAULT_FILTERS = Object.freeze({ search: '', ...structuredClone(defaults) });
  const queryKeys = urlFilterKeys || Object.keys(DEFAULT_FILTERS);

  // ── Params de deep link ────────────────────────────────────────────────────
  // Se leían sueltos con `route.query.x` en el `onMounted` de cada página y no
  // los borraba nadie. Como el watcher del tab clona el query entero, cada
  // `replace` posterior los volvía a arrastrar: limpiar los filtros dejaba la
  // URL diciendo `?project=5` con el filtro ya apagado, y el F5 siguiente lo
  // resucitaba. Un param que sobrevive a su contexto es estado oculto.
  //
  // El valor se captura AQUÍ, en el setup, antes de que nada pueda retirarlo,
  // así el orden en que la página lo consuma deja de importar.
  const ephemeral = ephemeralParams.map(
    (param) => (typeof param === 'string' ? { name: param } : param),
  );

  const seededQuery = Object.freeze(Object.fromEntries(
    ephemeral.map(({ name }) => [name, route?.query?.[name]]),
  ));

  /** Valor con el que se sembró la vista, o undefined si no venía en la URL. */
  function consumeParam(name) {
    return seededQuery[name];
  }

  function dropParams(names) {
    if (!route || !router || !names.length) return;
    const present = names.filter((name) => route.query?.[name] !== undefined);
    if (!present.length) return;
    const query = { ...route.query };
    present.forEach((name) => delete query[name]);
    router.replace({ query });
  }

  function freshFilters() {
    return structuredClone(DEFAULT_FILTERS);
  }

  /**
   * Defaults for "clear everything" and for stepping off a tab. The module is
   * carried over: it selects an angle, it is not one of the cuts being
   * cleared, so dropping the filters must not also walk the user back to the
   * first module.
   */
  function freshFiltersKeepingModule(from) {
    const fresh = freshFilters();
    if (moduleKey) fresh[moduleKey] = from[moduleKey];
    return fresh;
  }

  function cloneFilters(filters) {
    return structuredClone(toRaw(filters));
  }

  function loadTabFilters(target, tab) {
    const stored = cloneFilters(tab.filters);
    Object.assign(target, freshFilters(), normalizeFilters ? normalizeFilters(stored) : stored);
  }

  /** Read this instance's filters out of the query string. */
  function filtersFromQuery(query) {
    const parsed = {};
    for (const [key, fallback] of Object.entries(DEFAULT_FILTERS)) {
      const raw = Array.isArray(query?.[key]) ? query[key][0] : query?.[key];
      if (raw === undefined || raw === null || raw === '') continue;
      parsed[key] = Array.isArray(fallback)
        ? String(raw).split(',').filter(Boolean)
        : String(raw);
    }
    return parsed;
  }

  /** Serialize the active filters, arrays joined like the export params. */
  function filtersToQuery() {
    const serialized = {};
    for (const [key, fallback] of Object.entries(DEFAULT_FILTERS)) {
      const value = currentFilters[key];
      if (!isValueActive(value, fallback)) continue;
      serialized[key] = Array.isArray(value) ? value.join(',') : String(value);
    }
    return serialized;
  }

  const builtinById = new Map(builtinTabs.map((t) => [String(t.id), t]));
  const initialTab = route?.query?.[tabQueryParam] || defaultTabId;
  const activeTabId = ref(initialTab);

  const currentFilters = reactive(freshFilters());
  // A builtin landing tab needs no server round-trip, so its filters are
  // applied here rather than on mount: waiting would flash an unfiltered list
  // and leave the search box out of sync with the tab it belongs to.
  if (builtinById.has(String(initialTab))) {
    loadTabFilters(currentFilters, builtinById.get(String(initialTab)));
  }
  // Same reason, for a shared link: the filters have to be in place before
  // the page's first fetch, not after it.
  if (syncFiltersToUrl && isUrlOwner()) {
    Object.assign(currentFilters, filtersFromQuery(route?.query));
  }
  // Read after the landing tab, which stamps its own module: an explicit
  // ?<view>Module in the URL is the more specific instruction and wins.
  if (moduleKey && route?.query?.[moduleQueryParam]) {
    currentFilters[moduleKey] = String(route.query[moduleQueryParam]);
  }
  const isFilterPanelOpen = ref(false);

  // Un param que dispara una acción de una sola vez (destacar una fila) agota
  // su contexto al montar: dejarlo puesto re-enciende el destello en cada F5.
  onMounted(() => {
    dropParams(ephemeral.filter((p) => !p.boundTo).map((p) => p.name));
  });

  // El que siembra un FILTRO se queda mientras ese filtro siga puesto — ahí el
  // param sí describe la vista y sostiene el deep link a través de un F5. Se va
  // en cuanto el filtro cambia o se limpia, que es lo que antes no pasaba
  // nunca: la URL seguía prometiendo un filtro ya apagado.
  ephemeral.filter((p) => p.boundTo).forEach(({ name, boundTo }) => {
    if (seededQuery[name] === undefined) return;
    watch(() => currentFilters[boundTo], (value) => {
      const stillSeeded = Array.isArray(value)
        && value.length === 1
        && String(value[0]) === String(seededQuery[name]);
      if (!stillSeeded) dropParams([name]);
    }, { deep: true });
  });

  const tabs = useSavedFilterTabs(viewName);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  // Tabs carry their module inside their filters, so a saved one is grouped by
  // whatever module was active when it was saved. Anything without a module —
  // every tab of every other view — belongs to the default one.
  function moduleOf(tab) {
    return String(tab.module ?? tab.filters?.[moduleKey] ?? defaultModule);
  }

  const activeModule = computed(() =>
    (moduleKey ? String(currentFilters[moduleKey] ?? defaultModule) : defaultModule),
  );

  // `filters` travels with the builtins too: a view that badges its tabs has
  // to be able to ask the server what each one is worth, and a builtin with
  // no definition attached would be counted as if it filtered nothing.
  const displayTabs = computed(() => {
    const all = [
      ...builtinTabs.map((t) => ({
        id: t.id, name: t.name, filters: t.filters || {}, module: t.module, builtin: true,
      })),
      ...savedTabs.value,
    ];
    if (!moduleKey) return all;
    return all.filter((tab) => moduleOf(tab) === activeModule.value);
  });

  /**
   * Switching module never clears what is already applied: the panel and the
   * active-filter chips keep showing it, so nothing goes invisible, and cuts
   * from different modules stay combinable. A tab selected in another module
   * simply drops out of `displayTabs` and lights up again on the way back.
   */
  function selectModule(moduleId) {
    if (!moduleKey) return;
    currentFilters[moduleKey] = String(moduleId);
  }

  // Debounced free-text search: pages bind their search box to
  // `searchInput`; the actual `currentFilters.search` value (which drives
  // applyFilters) follows 250ms after the user stops typing. External
  // changes (tab selection, reset) sync back into the input immediately.
  const searchInput = ref(currentFilters.search);
  let searchTimer = null;

  watch(searchInput, (value) => {
    if (searchTimer) clearTimeout(searchTimer);
    if (value === currentFilters.search) return;
    searchTimer = setTimeout(() => {
      currentFilters.search = value;
    }, 250);
  });

  watch(
    () => currentFilters.search,
    (value) => {
      if (value !== searchInput.value) searchInput.value = value;
    },
  );

  if (getCurrentScope()) {
    onScopeDispose(() => {
      if (searchTimer) clearTimeout(searchTimer);
    });
  }

  function numericTabId(value) {
    return typeof value === 'number' ? value : Number(value);
  }

  /**
   * Write tab, module and filters in one `router.replace`.
   *
   * One writer on purpose: two watchers each replacing the query would race,
   * and whichever landed second would drop the other's keys. Selecting a
   * subfilter moves the tab AND the module at once, so they have to share it.
   *
   * The tab param is written for every tab that is NOT the landing one —
   * including 'all'. Omitting it there would make a reload of the cleared
   * view snap back to the default tab. The module param follows the same rule.
   */
  function syncUrl() {
    if (!route || !router) return;
    const query = { ...route.query };
    if (String(activeTabId.value) === String(defaultTabId)) {
      delete query[tabQueryParam];
    } else {
      query[tabQueryParam] = String(activeTabId.value);
    }
    if (syncFiltersToUrl && isUrlOwner()) {
      for (const key of queryKeys) delete query[key];
      Object.assign(query, filtersToQuery());
    }
    if (moduleKey) {
      if (String(activeModule.value) === String(defaultModule)) {
        delete query[moduleQueryParam];
      } else {
        query[moduleQueryParam] = String(activeModule.value);
      }
    }
    router.replace({ query });
  }

  watch(activeTabId, syncUrl);
  watch(activeModule, syncUrl);

  watch(
    currentFilters,
    () => {
      if (
        activeTabId.value !== 'all'
        && !builtinById.has(String(activeTabId.value))
      ) {
        tabs.updateTabFilters(numericTabId(activeTabId.value), cloneFilters(currentFilters));
      }
      if (syncFiltersToUrl) syncUrl();
    },
    { deep: true },
  );

  onMounted(async () => {
    try {
      await tabs.loadTabs();
    } catch {
      // Saved tabs must never break local filtering.
      return;
    }
    // Builtin tabs already restored synchronously above, and being quick
    // filters they never pop the filter panel open.
    const tabId = activeTabId.value;
    if (tabId === 'all' || builtinById.has(String(tabId))) return;
    const tab = savedTabs.value.find((t) => String(t.id) === String(tabId));
    if (tab) {
      loadTabFilters(currentFilters, tab);
      activeTabId.value = tab.id;
      isFilterPanelOpen.value = true;
    } else {
      activeTabId.value = 'all';
    }
  });

  const matcherEntries = Object.entries(matchers);

  function matcherKeys(key, fn) {
    return Array.isArray(fn.keys) && fn.keys.length ? fn.keys : [key];
  }

  function isMatcherActive(key, fn) {
    return matcherKeys(key, fn).some((k) =>
      isValueActive(currentFilters[k], DEFAULT_FILTERS[k]),
    );
  }

  const searchQuery = computed(() => String(currentFilters.search || '').trim().toLowerCase());

  const activeFilterCount = computed(() => {
    let count = 0;
    for (const [key, fn] of matcherEntries) {
      if (isMatcherActive(key, fn)) count++;
    }
    if (searchFields.length && searchQuery.value) count++;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(records) {
    if (!hasActiveFilters.value) return records;

    const query = searchQuery.value;
    const activeMatchers = matcherEntries.filter(([key, fn]) => isMatcherActive(key, fn));

    return records.filter((record) => {
      if (query && searchFields.length) {
        const hit = searchFields.some((f) =>
          String(record[f] ?? '').toLowerCase().includes(query),
        );
        if (!hit) return false;
      }
      return activeMatchers.every(([key, fn]) =>
        fn(record, currentFilters[key], currentFilters),
      );
    });
  }

  function resetFilters() {
    Object.assign(currentFilters, freshFiltersKeepingModule(currentFilters));
    activeTabId.value = 'all';
  }

  /** Reset only the given filter keys to their defaults (chip removal). */
  function clearFilterKeys(keys) {
    const fresh = freshFilters();
    for (const key of keys) {
      if (key in fresh) currentFilters[key] = fresh[key];
    }
  }

  function selectTab(tabId) {
    const builtin = builtinById.get(String(tabId));
    if (builtin) {
      activeTabId.value = builtin.id;
      loadTabFilters(currentFilters, builtin);
      return;
    }
    activeTabId.value = tabId;
    if (tabId === 'all') {
      Object.assign(currentFilters, freshFiltersKeepingModule(currentFilters));
      return;
    }
    const tab = savedTabs.value.find((t) => String(t.id) === String(tabId));
    if (tab) {
      loadTabFilters(currentFilters, tab);
    }
  }

  async function saveTab(name) {
    const tab = await tabs.saveTab(name, cloneFilters(currentFilters));
    if (tab) activeTabId.value = tab.id;
    return tab;
  }

  async function deleteTab(tabId) {
    await tabs.deleteTab(numericTabId(tabId));
    if (String(activeTabId.value) === String(tabId)) {
      resetFilters();
    }
  }

  async function renameTab(tabId, newName) {
    await tabs.renameTab(numericTabId(tabId), newName);
  }

  async function restoreTab(tabId) {
    const updated = await tabs.restoreTab(numericTabId(tabId));
    if (updated && String(activeTabId.value) === String(tabId)) {
      loadTabFilters(currentFilters, updated);
    }
    return updated;
  }

  function rebaseTab(tabId) {
    return tabs.rebaseTab(numericTabId(tabId));
  }

  return {
    currentFilters,
    searchInput,
    savedTabs,
    displayTabs,
    activeTabId,
    activeModule,
    selectModule,
    isFilterPanelOpen,
    isLoading,
    isReady,
    lastError,
    hasActiveFilters,
    activeFilterCount,
    isTabLimitReached,
    applyFilters,
    resetFilters,
    clearFilterKeys,
    selectTab,
    saveTab,
    deleteTab,
    renameTab,
    restoreTab,
    rebaseTab,
    reloadTabs: tabs.loadTabs,
    consumeParam,
    // For a page with several instances: whichever becomes the visible one
    // re-claims the query string.
    syncUrl,
    filtersFromQuery,
  };
}
