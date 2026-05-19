import { computed, onMounted, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

const VIEW_NAME = 'diagnostic';
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

function cloneFilters(filters) {
  return structuredClone(toRaw(filters));
}

function loadTabFilters(target, tab) {
  Object.assign(target, freshFilters(), cloneFilters(tab.filters));
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
  const isFilterPanelOpen = ref(false);

  const tabs = useSavedFilterTabs(VIEW_NAME);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  const initialTab = route.query.diagnosticTab || 'all';
  const activeTabId = ref(initialTab);

  function numericTabId(value) {
    return typeof value === 'number' ? value : Number(value);
  }

  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.diagnosticTab;
    } else {
      query.diagnosticTab = String(tabId);
    }
    router.replace({ query });
  });

  watch(
    currentFilters,
    () => {
      if (activeTabId.value !== 'all') {
        tabs.updateTabFilters(numericTabId(activeTabId.value), cloneFilters(currentFilters));
      }
    },
    { deep: true },
  );

  onMounted(async () => {
    await tabs.loadTabs();
    if (activeTabId.value !== 'all') {
      const tab = savedTabs.value.find((t) => String(t.id) === String(activeTabId.value));
      if (tab) {
        loadTabFilters(currentFilters, tab);
        activeTabId.value = tab.id;
        isFilterPanelOpen.value = true;
      } else {
        activeTabId.value = 'all';
      }
    }
  });

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

  return {
    currentFilters,
    savedTabs,
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
    selectTab,
    saveTab,
    deleteTab,
    renameTab,
  };
}
