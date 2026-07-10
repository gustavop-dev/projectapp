import { computed, onMounted, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

const VIEW_NAME = 'client';
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

function cloneFilters(filters) {
  return structuredClone(toRaw(filters));
}

function loadTabFilters(target, tab) {
  Object.assign(target, freshFilters(), cloneFilters(tab.filters));
}

export function useClientFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const isFilterPanelOpen = ref(false);

  const tabs = useSavedFilterTabs(VIEW_NAME);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  const initialTab = route.query.clientTab || 'all';
  const activeTabId = ref(initialTab);

  function numericTabId(value) {
    return typeof value === 'number' ? value : Number(value);
  }

  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.clientTab;
    } else {
      query.clientTab = String(tabId);
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

    const projectTypeSet = currentFilters.projectTypes.length
      ? new Set(currentFilters.projectTypes)
      : null;
    const marketTypeSet = currentFilters.marketTypes.length
      ? new Set(currentFilters.marketTypes)
      : null;

    return clients.filter((c) => {
      if (currentFilters.lastStatuses.length && !currentFilters.lastStatuses.includes(c.last_status))
        return false;

      if (projectTypeSet && !(c.project_types || []).some((t) => projectTypeSet.has(t)))
        return false;

      if (marketTypeSet && !(c.market_types || []).some((t) => marketTypeSet.has(t)))
        return false;

      if (currentFilters.totalProposalsMin != null && c.total_proposals < currentFilters.totalProposalsMin)
        return false;
      if (currentFilters.totalProposalsMax != null && c.total_proposals > currentFilters.totalProposalsMax)
        return false;

      if (currentFilters.acceptedMin != null && (c.accepted_count || 0) < currentFilters.acceptedMin)
        return false;
      if (currentFilters.acceptedMax != null && (c.accepted_count || 0) > currentFilters.acceptedMax)
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
    reloadTabs: tabs.loadTabs,
  };
}
