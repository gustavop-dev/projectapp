import { computed, onMounted, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

const VIEW_NAME = 'proposal';
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
  technicalViewed: false,
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

export function useProposalFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const isFilterPanelOpen = ref(false);

  const tabs = useSavedFilterTabs(VIEW_NAME);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  // URL tab id is a string ('all' o numérico); IDs del backend son enteros.
  const initialTab = route.query.tab || 'all';
  const activeTabId = ref(initialTab);

  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.tab;
    } else {
      query.tab = String(tabId);
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

  function numericTabId(value) {
    return typeof value === 'number' ? value : Number(value);
  }

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
    if (currentFilters.technicalViewed) count++;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(proposals) {
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

      if (currentFilters.technicalViewed && p.engagement_summary?.technical_viewed !== true) return false;

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
