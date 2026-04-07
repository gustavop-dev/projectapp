import { computed, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const STORAGE_KEY = 'client_filter_tabs';
const MAX_TABS = 12;
const DEFAULT_FILTERS = Object.freeze({
  lastStatuses: [],
  projectTypes: [],
  marketTypes: [],
  totalProposalsMin: null,
  totalProposalsMax: null,
  acceptedMin: null,
  acceptedMax: null,
  lastActivityAfter: null,
  lastActivityBefore: null,
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

export function useClientFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const savedTabs = ref(loadTabs());
  const isFilterPanelOpen = ref(false);

  const initialTab = route.query.clientTab || 'all';
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

  // Sync activeTabId → URL (clientTab avoids collision with proposals ?tab=)
  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.clientTab;
    } else {
      query.clientTab = tabId;
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
    if (currentFilters.lastStatuses.length) count++;
    if (currentFilters.projectTypes.length) count++;
    if (currentFilters.marketTypes.length) count++;
    if (currentFilters.totalProposalsMin != null || currentFilters.totalProposalsMax != null) count++;
    if (currentFilters.acceptedMin != null || currentFilters.acceptedMax != null) count++;
    if (currentFilters.lastActivityAfter || currentFilters.lastActivityBefore) count++;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(clients) {
    if (!hasActiveFilters.value) return clients;

    const activityAfterDate = currentFilters.lastActivityAfter
      ? new Date(currentFilters.lastActivityAfter)
      : null;
    let activityBeforeDate = null;
    if (currentFilters.lastActivityBefore) {
      activityBeforeDate = new Date(currentFilters.lastActivityBefore);
      activityBeforeDate.setHours(23, 59, 59, 999);
    }

    // Pre-compute sets for O(1) membership checks inside proposals.some()
    const projectTypeSet = currentFilters.projectTypes.length
      ? new Set(currentFilters.projectTypes)
      : null;
    const marketTypeSet = currentFilters.marketTypes.length
      ? new Set(currentFilters.marketTypes)
      : null;

    return clients.filter((c) => {
      if (currentFilters.lastStatuses.length && !currentFilters.lastStatuses.includes(c.last_status))
        return false;

      if (projectTypeSet && !c.proposals.some((p) => projectTypeSet.has(p.project_type)))
        return false;

      if (marketTypeSet && !c.proposals.some((p) => marketTypeSet.has(p.market_type)))
        return false;

      if (currentFilters.totalProposalsMin != null && c.total_proposals < currentFilters.totalProposalsMin)
        return false;
      if (currentFilters.totalProposalsMax != null && c.total_proposals > currentFilters.totalProposalsMax)
        return false;

      if (currentFilters.acceptedMin != null && c.accepted < currentFilters.acceptedMin)
        return false;
      if (currentFilters.acceptedMax != null && c.accepted > currentFilters.acceptedMax)
        return false;

      if (activityAfterDate || activityBeforeDate) {
        if (!c.last_sent_at) return false;
        const d = new Date(c.last_sent_at);
        if (activityAfterDate && d < activityAfterDate) return false;
        if (activityBeforeDate && d > activityBeforeDate) return false;
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
