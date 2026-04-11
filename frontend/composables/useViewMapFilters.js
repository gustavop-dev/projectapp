import { computed, reactive, ref, toRaw, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const STORAGE_KEY = 'view_map_filter_tabs';
const MAX_TABS = 12;
const DEFAULT_FILTERS = Object.freeze({
  categories: [],
  audiences: [],
  viewTypes: [],
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

export function useViewMapFilters() {
  const route = useRoute();
  const router = useRouter();

  const currentFilters = reactive(freshFilters());
  const savedTabs = ref(loadTabs());
  const isFilterPanelOpen = ref(false);

  const initialTab = route.query.viewTab || 'all';
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
      delete query.viewTab;
    } else {
      query.viewTab = tabId;
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
