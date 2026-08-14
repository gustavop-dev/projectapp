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
} = {}) {
  const route = useRoute();
  const router = useRouter();

  const DEFAULT_FILTERS = Object.freeze({ search: '', ...structuredClone(defaults) });
  const tabQueryParam = `${viewName}Tab`;

  function freshFilters() {
    return structuredClone(DEFAULT_FILTERS);
  }

  function cloneFilters(filters) {
    return structuredClone(toRaw(filters));
  }

  function loadTabFilters(target, tab) {
    Object.assign(target, freshFilters(), cloneFilters(tab.filters));
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
  const isFilterPanelOpen = ref(false);

  const tabs = useSavedFilterTabs(viewName);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  const displayTabs = computed(() => [
    ...builtinTabs.map((t) => ({ id: t.id, name: t.name, builtin: true })),
    ...savedTabs.value,
  ]);

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

  // The param is written for every tab that is NOT the landing one — including
  // 'all'. Omitting it there would make a reload of the cleared view snap back
  // to the default tab.
  watch(activeTabId, (tabId) => {
    if (!route || !router) return;
    const query = { ...route.query };
    if (String(tabId) === String(defaultTabId)) {
      delete query[tabQueryParam];
    } else {
      query[tabQueryParam] = String(tabId);
    }
    router.replace({ query });
  });

  watch(
    currentFilters,
    () => {
      if (
        activeTabId.value !== 'all'
        && !builtinById.has(String(activeTabId.value))
      ) {
        tabs.updateTabFilters(numericTabId(activeTabId.value), cloneFilters(currentFilters));
      }
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
    Object.assign(currentFilters, freshFilters());
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
      Object.assign(currentFilters, freshFilters());
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
  };
}
