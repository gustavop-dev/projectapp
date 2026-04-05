import { computed, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const STORAGE_KEY = 'proposal_filter_tabs';
const MAX_TABS = 12;
const DEFAULT_FILTERS = Object.freeze({
  statuses: [],
  projectTypes: [],
  marketTypes: [],
  currencies: [],
  languages: [],
  investmentMin: null,
  investmentMax: null,
  heatScoreMin: null,
  heatScoreMax: null,
  viewCountMin: null,
  viewCountMax: null,
  createdAfter: null,
  createdBefore: null,
  lastActivityAfter: null,
  lastActivityBefore: null,
  isActive: 'all',
});

function freshFilters() {
  return { ...DEFAULT_FILTERS, statuses: [], projectTypes: [], marketTypes: [], currencies: [], languages: [] };
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

export function useProposalFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const savedTabs = ref(loadTabs());
  const isFilterPanelOpen = ref(false);

  // Restore active tab from URL query param
  const initialTab = route.query.tab || 'all';
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

  // Sync activeTabId → URL
  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.tab;
    } else {
      query.tab = tabId;
    }
    router.replace({ query });
  });

  // Shallow watch — all mutations already replace the array reference
  watch(savedTabs, (val) => persistTabs(val));

  const isTabLimitReached = computed(() => savedTabs.value.length >= MAX_TABS);

  const activeFilterCount = computed(() => {
    let count = 0;
    if (currentFilters.statuses.length) count++;
    if (currentFilters.projectTypes.length) count++;
    if (currentFilters.marketTypes.length) count++;
    if (currentFilters.currencies.length) count++;
    if (currentFilters.languages.length) count++;
    if (currentFilters.investmentMin != null || currentFilters.investmentMax != null) count++;
    if (currentFilters.heatScoreMin != null || currentFilters.heatScoreMax != null) count++;
    if (currentFilters.viewCountMin != null || currentFilters.viewCountMax != null) count++;
    if (currentFilters.createdAfter || currentFilters.createdBefore) count++;
    if (currentFilters.lastActivityAfter || currentFilters.lastActivityBefore) count++;
    if (currentFilters.isActive !== 'all') count++;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(proposals) {
    // Pre-compute date boundaries once outside the loop
    const createdAfterDate = currentFilters.createdAfter ? new Date(currentFilters.createdAfter) : null;
    let createdBeforeDate = null;
    if (currentFilters.createdBefore) {
      createdBeforeDate = new Date(currentFilters.createdBefore);
      createdBeforeDate.setHours(23, 59, 59, 999);
    }
    const activityAfterDate = currentFilters.lastActivityAfter ? new Date(currentFilters.lastActivityAfter) : null;
    let activityBeforeDate = null;
    if (currentFilters.lastActivityBefore) {
      activityBeforeDate = new Date(currentFilters.lastActivityBefore);
      activityBeforeDate.setHours(23, 59, 59, 999);
    }

    return proposals.filter((p) => {
      if (currentFilters.statuses.length && !currentFilters.statuses.includes(p.status)) return false;
      if (currentFilters.projectTypes.length && !currentFilters.projectTypes.includes(p.project_type)) return false;
      if (currentFilters.marketTypes.length && !currentFilters.marketTypes.includes(p.market_type)) return false;
      if (currentFilters.currencies.length && !currentFilters.currencies.includes(p.currency)) return false;
      if (currentFilters.languages.length && !currentFilters.languages.includes(p.language)) return false;

      const inv = Number(p.total_investment) || 0;
      if (currentFilters.investmentMin != null && inv < currentFilters.investmentMin) return false;
      if (currentFilters.investmentMax != null && inv > currentFilters.investmentMax) return false;

      const hs = p.heat_score ?? p.cached_heat_score ?? 0;
      if (currentFilters.heatScoreMin != null && hs < currentFilters.heatScoreMin) return false;
      if (currentFilters.heatScoreMax != null && hs > currentFilters.heatScoreMax) return false;

      const vc = p.view_count ?? 0;
      if (currentFilters.viewCountMin != null && vc < currentFilters.viewCountMin) return false;
      if (currentFilters.viewCountMax != null && vc > currentFilters.viewCountMax) return false;

      if (createdAfterDate && new Date(p.created_at) < createdAfterDate) return false;
      if (createdBeforeDate && new Date(p.created_at) > createdBeforeDate) return false;

      if (activityAfterDate || activityBeforeDate) {
        const dateRef = p.last_activity_at || p.created_at;
        if (!dateRef) return false;
        const d = new Date(dateRef);
        if (activityAfterDate && d < activityAfterDate) return false;
        if (activityBeforeDate && d > activityBeforeDate) return false;
      }

      if (currentFilters.isActive === 'active' && !p.is_active) return false;
      if (currentFilters.isActive === 'inactive' && p.is_active) return false;

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
    savedTabs.value = spliceTab(savedTabs.value, idx, {
      ...savedTabs.value[idx],
      filters: cloneFilters(currentFilters),
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
    updateTab,
    deleteTab,
    renameTab,
  };
}
