import { computed, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const STORAGE_KEY = 'diagnostic_filter_tabs';
const MAX_TABS = 12;
const DEFAULT_FILTERS = Object.freeze({
  statuses: [],
  investmentMin: null,
  investmentMax: null,
  createdAfter: null,
  createdBefore: null,
});

function freshFilters() {
  return structuredClone(DEFAULT_FILTERS);
}

function loadTabs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistTabs(tabs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tabs));
}

function cloneFilters(filters) {
  return structuredClone(toRaw(filters));
}

function loadTabFilters(target, tab) {
  Object.assign(target, freshFilters(), cloneFilters(tab.filters));
}

function spliceTab(tabs, idx, updated) {
  const copy = [...tabs];
  copy[idx] = updated;
  return copy;
}

function normalizeNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function useDiagnosticFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const savedTabs = ref(loadTabs());
  const isFilterPanelOpen = ref(false);

  const initialTab = route.query.diagnosticTab || 'all';
  const activeTabId = ref(
    initialTab === 'all' || savedTabs.value.some((t) => t.id === initialTab)
      ? initialTab
      : 'all',
  );

  if (activeTabId.value !== 'all') {
    const tab = savedTabs.value.find((t) => t.id === activeTabId.value);
    if (tab) {
      loadTabFilters(currentFilters, tab);
      isFilterPanelOpen.value = true;
    }
  }

  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.diagnosticTab;
    } else {
      query.diagnosticTab = tabId;
    }
    router.replace({ query });
  });

  watch(savedTabs, (val) => persistTabs(val));

  watch(
    currentFilters,
    () => {
      if (activeTabId.value !== 'all') {
        updateTab(activeTabId.value);
      }
    },
    { deep: true },
  );

  const isTabLimitReached = computed(() => savedTabs.value.length >= MAX_TABS);

  const activeFilterCount = computed(() => {
    let count = 0;
    if (currentFilters.statuses.length) count += 1;
    if (normalizeNumber(currentFilters.investmentMin) !== null) count += 1;
    if (normalizeNumber(currentFilters.investmentMax) !== null) count += 1;
    if (currentFilters.createdAfter) count += 1;
    if (currentFilters.createdBefore) count += 1;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(diagnostics) {
    if (!hasActiveFilters.value) return diagnostics;

    const statuses = currentFilters.statuses;
    const invMin = normalizeNumber(currentFilters.investmentMin);
    const invMax = normalizeNumber(currentFilters.investmentMax);
    const afterDate = currentFilters.createdAfter ? new Date(currentFilters.createdAfter) : null;
    let beforeDate = null;
    if (currentFilters.createdBefore) {
      beforeDate = new Date(currentFilters.createdBefore);
      beforeDate.setHours(23, 59, 59, 999);
    }

    const statusSet = statuses.length ? new Set(statuses) : null;

    return diagnostics.filter((d) => {
      if (statusSet && !statusSet.has(d.status)) return false;

      const amount = Number(d.investment_amount || 0);
      if (invMin !== null && amount < invMin) return false;
      if (invMax !== null && amount > invMax) return false;

      if (afterDate || beforeDate) {
        if (!d.created_at) return false;
        const created = new Date(d.created_at);
        if (afterDate && created < afterDate) return false;
        if (beforeDate && created > beforeDate) return false;
      }
      return true;
    });
  }

  function resetFilters() {
    Object.assign(currentFilters, freshFilters());
    activeTabId.value = 'all';
  }

  function selectTab(tabId) {
    activeTabId.value = tabId;
    if (tabId === 'all') {
      Object.assign(currentFilters, freshFilters());
      return;
    }
    const tab = savedTabs.value.find((t) => t.id === tabId);
    if (tab) {
      loadTabFilters(currentFilters, tab);
    }
  }

  function saveTab(name) {
    if (savedTabs.value.length >= MAX_TABS) return null;
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const tab = {
      id,
      name,
      filters: cloneFilters(currentFilters),
      createdAt: now,
      updatedAt: now,
    };
    savedTabs.value = [...savedTabs.value, tab];
    activeTabId.value = id;
    return tab;
  }

  function updateTab(tabId) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return;
    const newFilters = cloneFilters(currentFilters);
    if (JSON.stringify(newFilters) === JSON.stringify(savedTabs.value[idx].filters)) return;
    savedTabs.value = spliceTab(savedTabs.value, idx, {
      ...savedTabs.value[idx],
      filters: newFilters,
      updatedAt: new Date().toISOString(),
    });
  }

  function deleteTab(tabId) {
    savedTabs.value = savedTabs.value.filter((t) => t.id !== tabId);
    if (activeTabId.value === tabId) {
      resetFilters();
    }
  }

  function renameTab(tabId, newName) {
    const idx = savedTabs.value.findIndex((t) => t.id === tabId);
    if (idx === -1) return;
    savedTabs.value = spliceTab(savedTabs.value, idx, {
      ...savedTabs.value[idx],
      name: newName,
      updatedAt: new Date().toISOString(),
    });
  }

  return {
    currentFilters,
    savedTabs,
    activeTabId,
    isFilterPanelOpen,
    hasActiveFilters,
    activeFilterCount,
    isTabLimitReached,
    applyFilters,
    resetFilters,
    selectTab,
    saveTab,
    deleteTab,
    renameTab,
  };
}
