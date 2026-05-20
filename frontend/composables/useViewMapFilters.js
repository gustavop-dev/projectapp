import { computed, onMounted, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { useSavedFilterTabs } from '~/composables/useSavedFilterTabs';

const VIEW_NAME = 'view_map';
const DEFAULT_FILTERS = Object.freeze({
  categories: [],
  audiences: [],
  viewTypes: [],
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

export function useViewMapFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const isFilterPanelOpen = ref(false);

  const tabs = useSavedFilterTabs(VIEW_NAME);
  const { savedTabs, isLoading, isReady, lastError, isTabLimitReached } = tabs;

  const initialTab = route.query.viewTab || 'all';
  const activeTabId = ref(initialTab);

  function numericTabId(value) {
    return typeof value === 'number' ? value : Number(value);
  }

  watch(activeTabId, (tabId) => {
    const query = { ...route.query };
    if (tabId === 'all') {
      delete query.viewTab;
    } else {
      query.viewTab = String(tabId);
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
    if (currentFilters.categories.length) count++;
    if (currentFilters.audiences.length) count++;
    if (currentFilters.viewTypes.length) count++;
    return count;
  });

  const hasActiveFilters = computed(() => activeFilterCount.value > 0);

  function applyFilters(sections) {
    if (!hasActiveFilters.value) return sections;

    const categorySet = currentFilters.categories.length
      ? new Set(currentFilters.categories)
      : null;
    const audienceSet = currentFilters.audiences.length
      ? new Set(currentFilters.audiences)
      : null;
    const viewTypeSet = currentFilters.viewTypes.length
      ? new Set(currentFilters.viewTypes)
      : null;

    return sections
      .filter((s) => !categorySet || categorySet.has(s.id))
      .map((s) => ({
        ...s,
        views: s.views.filter((v) => {
          if (audienceSet && !audienceSet.has(v.audience)) return false;
          if (viewTypeSet && !viewTypeSet.has(v.viewType)) return false;
          return true;
        }),
      }))
      .filter((s) => s.views.length > 0);
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
