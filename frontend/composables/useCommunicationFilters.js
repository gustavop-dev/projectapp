import {
  computed, getCurrentScope, onMounted, onScopeDispose, reactive, ref, watch,
} from 'vue';

import { sameFilters, useSavedFilterTabs } from '~/composables/useSavedFilterTabs';
import {
  COMMUNICATION_BUILTIN_BY_ID,
  COMMUNICATION_BUILTIN_TABS,
} from '~/constants/communicationFilters';

export const COMMUNICATION_FILTER_DEFAULTS = Object.freeze({
  by: 'project',
  project: '',
  client: '',
  status: [],
  channel: [],
  direction: [],
  message_status: [],
  reply_status: [],
  q: '',
  date_from: '',
  date_to: '',
  order: 'recent',
});

const ARRAY_KEYS = ['status', 'channel', 'direction', 'message_status', 'reply_status'];
const FILTER_KEYS = Object.keys(COMMUNICATION_FILTER_DEFAULTS);
const URL_KEYS = [...FILTER_KEYS, 'page', 'tab'];

function scalar(value) {
  return Array.isArray(value) ? value[0] : value;
}

function values(value) {
  const raw = scalar(value);
  if (raw === undefined || raw === null || raw === '') return [];
  return String(raw).split(',').map((token) => token.trim()).filter(Boolean);
}

function normalizeStoredFilters(stored = {}) {
  const normalized = structuredClone(COMMUNICATION_FILTER_DEFAULTS);
  Object.assign(normalized, stored || {});
  normalized.by = normalized.by === 'client' ? 'client' : 'project';
  for (const key of ARRAY_KEYS) {
    const value = normalized[key];
    normalized[key] = Array.isArray(value)
      ? [...value]
      : (value === '' || value === null || value === undefined ? [] : [value]);
  }
  normalized.project = normalized.project == null ? '' : String(normalized.project);
  normalized.client = normalized.client == null ? '' : String(normalized.client);
  if (normalized.by === 'project') normalized.client = '';
  else normalized.project = '';
  normalized.q = String(normalized.q || '');
  normalized.date_from = String(normalized.date_from || '');
  normalized.date_to = String(normalized.date_to || '');
  normalized.order = ['recent', 'oldest', 'title'].includes(normalized.order)
    ? normalized.order : 'recent';
  return normalized;
}

export function communicationFiltersFromQuery(query = {}) {
  const inferredMode = scalar(query.by) === 'client' || query.client ? 'client' : 'project';
  return normalizeStoredFilters({
    by: inferredMode,
    project: scalar(query.project) || '',
    client: scalar(query.client) || '',
    status: values(query.status),
    channel: values(query.channel),
    direction: values(query.direction),
    message_status: values(query.message_status),
    reply_status: values(query.reply_status),
    q: scalar(query.q) || '',
    date_from: scalar(query.date_from) || '',
    date_to: scalar(query.date_to) || '',
    order: scalar(query.order) || 'recent',
  });
}

export function communicationFiltersToQuery(filters) {
  const query = { by: filters.by };
  if (filters.by === 'project' && filters.project) query.project = String(filters.project);
  if (filters.by === 'client' && filters.client) query.client = String(filters.client);
  for (const key of ARRAY_KEYS) {
    if (filters[key]?.length) query[key] = filters[key].join(',');
  }
  if (filters.q.trim()) query.q = filters.q.trim();
  if (filters.date_from) query.date_from = filters.date_from;
  if (filters.date_to) query.date_to = filters.date_to;
  if (filters.order !== 'recent') query.order = filters.order;
  return query;
}

function pageFromQuery(query) {
  const parsed = Number(scalar(query?.page) || 1);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1;
}

function stableState(value) {
  if (Array.isArray(value)) return value.map(stableState);
  if (value && typeof value === 'object') {
    return Object.keys(value).sort().reduce((result, key) => {
      result[key] = stableState(value[key]);
      return result;
    }, {});
  }
  return value;
}

function stateSignature(value) {
  return JSON.stringify(stableState(value));
}

function sameState(a, b) {
  return stateSignature(a) === stateSignature(b);
}

export function useCommunicationFilters() {
  const route = useRoute();
  const router = useRouter();
  const initialTabId = scalar(route.query.tab) || 'all';
  const hasExplicitFilterState = FILTER_KEYS.some(
    (key) => key !== 'by' && route.query[key] !== undefined,
  );
  const initialFilters = communicationFiltersFromQuery(route.query);
  const initialBuiltin = COMMUNICATION_BUILTIN_BY_ID.get(String(initialTabId));
  if (initialBuiltin && !hasExplicitFilterState) {
    Object.assign(initialFilters, normalizeStoredFilters(initialBuiltin.filters));
  }
  const currentFilters = reactive(initialFilters);
  const page = ref(pageFromQuery(route.query));
  const activeTabId = ref(initialTabId);
  const isFilterPanelOpen = ref(
    ARRAY_KEYS.some((key) => currentFilters[key].length)
      || Boolean(currentFilters.date_from || currentFilters.date_to),
  );
  const searchInput = ref(currentFilters.q);
  const tabs = useSavedFilterTabs('communication');
  let applyingExternalState = false;
  let pendingRouteSignature = '';
  let searchTimer = null;

  const placeholderByKey = computed(() => new Map(
    tabs.savedTabs.value
      .filter((tab) => tab.builtin_key)
      .map((tab) => [String(tab.builtin_key), tab]),
  ));
  const displayTabs = computed(() => {
    const placeholders = placeholderByKey.value;
    const rows = [
      ...COMMUNICATION_BUILTIN_TABS.map((builtin, index) => {
        const placeholder = placeholders.get(String(builtin.id));
        return {
          ...builtin,
          builtin: true,
          order: placeholder ? placeholder.order : -1000 + index,
          is_hidden: placeholder ? placeholder.is_hidden : false,
        };
      }),
      ...tabs.savedTabs.value.filter((tab) => !tab.builtin_key),
    ];
    return rows.sort((a, b) => (a.order || 0) - (b.order || 0));
  });
  const tabCountSpecs = computed(() => [
    { id: 'all', filters: {} },
    ...displayTabs.value.map((tab) => ({ id: tab.id, filters: tab.filters || {} })),
  ]);
  const navigationSelection = computed(() => (
    currentFilters.by === 'project'
      ? (currentFilters.project || 'all')
      : (currentFilters.client || 'all')
  ));
  const activeFilterCount = computed(() => (
    ARRAY_KEYS.filter((key) => currentFilters[key].length).length
      + (currentFilters.date_from || currentFilters.date_to ? 1 : 0)
  ));
  const hasActiveFilters = computed(() => (
    activeFilterCount.value > 0 || Boolean(currentFilters.q.trim())
  ));

  function snapshot() {
    return normalizeStoredFilters(currentFilters);
  }

  function builtinStillMatches(tab) {
    return Object.entries(tab.filters || {}).every(([key, value]) => (
      sameFilters({ [key]: currentFilters[key] }, { [key]: value })
    ));
  }

  function applySnapshot(filters) {
    applyingExternalState = true;
    Object.assign(currentFilters, normalizeStoredFilters(filters));
    searchInput.value = currentFilters.q;
    page.value = 1;
    applyingExternalState = false;
  }

  function replaceUrl() {
    const query = { ...route.query };
    for (const key of URL_KEYS) delete query[key];
    Object.assign(query, communicationFiltersToQuery(currentFilters));
    if (page.value > 1) query.page = String(page.value);
    if (String(activeTabId.value) !== 'all') query.tab = String(activeTabId.value);
    const targetSignature = stateSignature(query);
    if (targetSignature === stateSignature(route.query)) {
      pendingRouteSignature = '';
      return;
    }
    pendingRouteSignature = targetSignature;
    router.replace({ query }).catch(() => {
      if (pendingRouteSignature === targetSignature) pendingRouteSignature = '';
    });
  }

  watch(searchInput, (value) => {
    if (searchTimer) clearTimeout(searchTimer);
    if (value === currentFilters.q) return;
    searchTimer = setTimeout(() => {
      currentFilters.q = String(value || '');
      page.value = 1;
    }, 250);
  });
  watch(() => currentFilters.q, (value) => {
    if (value !== searchInput.value) searchInput.value = value;
  });

  watch(
    currentFilters,
    () => {
      if (!applyingExternalState && String(activeTabId.value) !== 'all' && tabs.isReady.value) {
        const builtin = COMMUNICATION_BUILTIN_BY_ID.get(String(activeTabId.value));
        if (builtin) {
          if (!builtinStillMatches(builtin)) activeTabId.value = 'all';
        } else {
          tabs.updateTabFilters(Number(activeTabId.value), snapshot());
        }
      }
      replaceUrl();
    },
    { deep: true },
  );
  watch([page, activeTabId], replaceUrl);

  watch(
    () => route.query,
    (query) => {
      const incomingSignature = stateSignature(query);
      if (pendingRouteSignature && incomingSignature !== pendingRouteSignature) return;
      if (incomingSignature === pendingRouteSignature) pendingRouteSignature = '';
      const incoming = communicationFiltersFromQuery(query);
      if (!sameState(incoming, snapshot())) {
        applyingExternalState = true;
        Object.assign(currentFilters, incoming);
        searchInput.value = incoming.q;
        applyingExternalState = false;
      }
      const incomingPage = pageFromQuery(query);
      if (incomingPage !== page.value) page.value = incomingPage;
      const incomingTab = scalar(query.tab) || 'all';
      if (String(incomingTab) !== String(activeTabId.value)) activeTabId.value = incomingTab;
    },
  );

  onMounted(async () => {
    await tabs.loadTabs();
    if (String(activeTabId.value) === 'all') return;
    if (COMMUNICATION_BUILTIN_BY_ID.has(String(activeTabId.value))) return;
    const tab = tabs.savedTabs.value.find(
      (candidate) => !candidate.builtin_key
        && String(candidate.id) === String(activeTabId.value),
    );
    if (!tab) {
      activeTabId.value = 'all';
      return;
    }
    if (!hasExplicitFilterState) applySnapshot(tab.filters);
    activeTabId.value = tab.id;
  });

  if (getCurrentScope()) {
    onScopeDispose(() => {
      if (searchTimer) clearTimeout(searchTimer);
    });
  }

  function setMode(mode) {
    currentFilters.by = mode === 'client' ? 'client' : 'project';
    currentFilters.project = '';
    currentFilters.client = '';
    page.value = 1;
  }

  function selectNavigation(value) {
    if (currentFilters.by === 'project') {
      currentFilters.project = value === 'all' ? '' : String(value);
      currentFilters.client = '';
    } else {
      currentFilters.client = value === 'all' ? '' : String(value);
      currentFilters.project = '';
    }
    page.value = 1;
  }

  function updateFilters(filters) {
    for (const key of [...ARRAY_KEYS, 'date_from', 'date_to']) {
      if (key in filters) currentFilters[key] = filters[key];
    }
    page.value = 1;
  }

  function setOrder(order) {
    currentFilters.order = order;
    page.value = 1;
  }

  function clearFilters() {
    for (const key of ARRAY_KEYS) currentFilters[key] = [];
    currentFilters.q = '';
    currentFilters.date_from = '';
    currentFilters.date_to = '';
    currentFilters.order = 'recent';
    page.value = 1;
  }

  function clearAll() {
    applySnapshot(COMMUNICATION_FILTER_DEFAULTS);
    activeTabId.value = 'all';
  }

  function selectTab(tabId) {
    if (String(tabId) === 'all') {
      clearAll();
      return;
    }
    const builtin = COMMUNICATION_BUILTIN_BY_ID.get(String(tabId));
    if (builtin) {
      activeTabId.value = builtin.id;
      applySnapshot(builtin.filters);
      return;
    }
    const tab = tabs.savedTabs.value.find((candidate) => (
      !candidate.builtin_key && String(candidate.id) === String(tabId)
    ));
    if (!tab) return;
    activeTabId.value = tab.id;
    applySnapshot(tab.filters);
    isFilterPanelOpen.value = true;
  }

  async function saveTab(name) {
    const tab = await tabs.saveTab(name, snapshot());
    if (tab) activeTabId.value = tab.id;
    return tab;
  }

  async function deleteTab(tabId) {
    if (COMMUNICATION_BUILTIN_BY_ID.has(String(tabId))) return;
    await tabs.deleteTab(Number(tabId));
    if (String(activeTabId.value) === String(tabId)) clearAll();
  }

  async function restoreTab(tabId) {
    if (COMMUNICATION_BUILTIN_BY_ID.has(String(tabId))) return null;
    const restored = await tabs.restoreTab(Number(tabId));
    if (restored && String(activeTabId.value) === String(tabId)) {
      applySnapshot(restored.filters);
    }
    return restored;
  }

  function renameTab(tabId, name) {
    if (COMMUNICATION_BUILTIN_BY_ID.has(String(tabId))) return null;
    return tabs.renameTab(Number(tabId), name);
  }

  function rebaseTab(tabId) {
    if (COMMUNICATION_BUILTIN_BY_ID.has(String(tabId))) return null;
    return tabs.rebaseTab(Number(tabId));
  }

  function requestFilters() {
    const request = {
      page: page.value,
      order: currentFilters.order,
    };
    if (currentFilters.by === 'project' && currentFilters.project) {
      request.project = currentFilters.project;
    }
    if (currentFilters.by === 'client' && currentFilters.client) {
      request.client = currentFilters.client;
    }
    for (const key of ARRAY_KEYS) {
      if (currentFilters[key].length) request[key] = currentFilters[key];
    }
    if (currentFilters.q.trim()) request.q = currentFilters.q.trim();
    if (currentFilters.date_from) request.date_from = currentFilters.date_from;
    if (currentFilters.date_to) request.date_to = currentFilters.date_to;
    return request;
  }

  return {
    currentFilters,
    page,
    activeTabId,
    isFilterPanelOpen,
    searchInput,
    displayTabs,
    tabCountSpecs,
    navigationSelection,
    activeFilterCount,
    hasActiveFilters,
    isTabLimitReached: tabs.isTabLimitReached,
    tabsError: tabs.lastError,
    setMode,
    selectNavigation,
    updateFilters,
    setOrder,
    clearFilters,
    clearAll,
    selectTab,
    saveTab,
    deleteTab,
    renameTab,
    restoreTab,
    rebaseTab,
    reorderTabs: tabs.reorderTabs,
    reloadTabs: tabs.loadTabs,
    tabsReady: tabs.isReady,
    requestFilters,
  };
}
