/**
 * Tests para useViewMapFilters después de migrar persistencia a backend.
 * Filtra sobre estructura sections→views (categories, audiences, viewTypes).
 */

if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (val) => JSON.parse(JSON.stringify(val));
}

const mockRoute = { query: {} };
const mockReplace = jest.fn();

jest.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ replace: mockReplace }),
}));

jest.mock('~/composables/useSavedFilterTabs', () => {
  const { ref, computed } = require('vue');
  const savedTabsRef = ref([]);
  const stub = {
    savedTabs: savedTabsRef,
    isLoading: ref(false),
    isReady: ref(true),
    lastError: ref(null),
    isTabLimitReached: computed(() => savedTabsRef.value.length >= 12),
    MAX_TABS: 12,
    loadTabs: jest.fn(() => Promise.resolve(savedTabsRef.value)),
    saveTab: jest.fn(async (name, filters) => {
      const tab = { id: savedTabsRef.value.length + 1, view: 'view_map', name, filters, order: 0 };
      savedTabsRef.value = [...savedTabsRef.value, tab];
      return tab;
    }),
    updateTabFilters: jest.fn(),
    renameTab: jest.fn(),
    deleteTab: jest.fn(async (id) => {
      savedTabsRef.value = savedTabsRef.value.filter((t) => t.id !== id);
    }),
  };
  return { useSavedFilterTabs: () => stub, __stub: stub };
});

import { nextTick } from 'vue';
import * as savedFilterTabsModule from '~/composables/useSavedFilterTabs';
import { useViewMapFilters } from '~/composables/useViewMapFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  tabsStub.saveTab.mockClear();
  tabsStub.updateTabFilters.mockClear();
});

const sections = () => [
  {
    id: 'panel',
    label: 'Panel',
    views: [
      { name: 'A', audience: 'admin', viewType: 'list' },
      { name: 'B', audience: 'admin', viewType: 'detail' },
    ],
  },
  {
    id: 'platform',
    label: 'Platform',
    views: [
      { name: 'C', audience: 'client', viewType: 'list' },
    ],
  },
];

describe('applyFilters', () => {
  it('returns all sections when no filters', () => {
    const { applyFilters } = useViewMapFilters();
    expect(applyFilters(sections())).toHaveLength(2);
  });

  it('filters by categories (section id)', () => {
    const { currentFilters, applyFilters } = useViewMapFilters();
    currentFilters.categories = ['panel'];
    const out = applyFilters(sections());
    expect(out).toHaveLength(1);
    expect(out[0].id).toBe('panel');
  });

  it('filters views by audience, dropping sections that become empty', () => {
    const { currentFilters, applyFilters } = useViewMapFilters();
    currentFilters.audiences = ['client'];
    const out = applyFilters(sections());
    expect(out).toHaveLength(1);
    expect(out[0].id).toBe('platform');
    expect(out[0].views).toHaveLength(1);
  });

  it('filters by viewTypes', () => {
    const { currentFilters, applyFilters } = useViewMapFilters();
    currentFilters.viewTypes = ['detail'];
    const out = applyFilters(sections());
    expect(out).toHaveLength(1);
    expect(out[0].views.map((v) => v.name)).toEqual(['B']);
  });
});

describe('activeFilterCount + hasActiveFilters', () => {
  it('returns 0 / false initially', () => {
    const { activeFilterCount, hasActiveFilters } = useViewMapFilters();
    expect(activeFilterCount.value).toBe(0);
    expect(hasActiveFilters.value).toBe(false);
  });

  it('counts each non-empty array as one dimension', () => {
    const { currentFilters, activeFilterCount } = useViewMapFilters();
    currentFilters.categories = ['panel'];
    currentFilters.audiences = ['admin'];
    expect(activeFilterCount.value).toBe(2);
  });
});

describe('resetFilters + selectTab', () => {
  it('resetFilters clears state', () => {
    const { currentFilters, activeTabId, resetFilters } = useViewMapFilters();
    currentFilters.categories = ['panel'];
    activeTabId.value = 6;
    resetFilters();
    expect(currentFilters.categories).toEqual([]);
    expect(activeTabId.value).toBe('all');
  });

  it('selectTab loads filters', () => {
    savedTabsRef.value = [{ id: 2, view: 'view_map', name: 'X', filters: { audiences: ['client'] } }];
    const { currentFilters, activeTabId, selectTab } = useViewMapFilters();
    selectTab(2);
    expect(activeTabId.value).toBe(2);
    expect(currentFilters.audiences).toEqual(['client']);
  });
});

describe('applyDefaultFilters', () => {
  it('merges configured defaults over fresh filters and opens the panel', () => {
    const { currentFilters, isFilterPanelOpen, applyDefaultFilters } = useViewMapFilters();
    currentFilters.categories = ['panel'];

    applyDefaultFilters({ audiences: ['admin'], viewTypes: ['config'] });

    expect(currentFilters.categories).toEqual([]);
    expect(currentFilters.audiences).toEqual(['admin']);
    expect(currentFilters.viewTypes).toEqual(['config']);
    expect(isFilterPanelOpen.value).toBe(true);
  });

  it('does not apply when a saved tab is active', () => {
    const { currentFilters, activeTabId, applyDefaultFilters } = useViewMapFilters();
    activeTabId.value = 4;

    applyDefaultFilters({ audiences: ['admin'] });

    expect(currentFilters.audiences).toEqual([]);
  });

  it('does not apply when the URL deep-links a ?viewTab', () => {
    mockRoute.query = { viewTab: '9' };
    const { currentFilters, applyDefaultFilters } = useViewMapFilters();

    applyDefaultFilters({ audiences: ['admin'] });

    expect(currentFilters.audiences).toEqual([]);
  });

  it('ignores unknown keys and non-array values', () => {
    const { currentFilters, isFilterPanelOpen, applyDefaultFilters } = useViewMapFilters();

    applyDefaultFilters({ statuses: ['draft'], audiences: 'admin' });

    expect(currentFilters).toMatchObject({ categories: [], audiences: [], viewTypes: [] });
    expect(currentFilters.statuses).toBeUndefined();
    expect(isFilterPanelOpen.value).toBe(false);
  });

  it('does not trigger a saved-tab autosave PATCH', async () => {
    const { applyDefaultFilters } = useViewMapFilters();

    applyDefaultFilters({ audiences: ['admin'] });
    await nextTick();

    expect(tabsStub.updateTabFilters).not.toHaveBeenCalled();
  });
});

describe('URL sync + delegation', () => {
  it('uses viewTab URL param', async () => {
    const { activeTabId } = useViewMapFilters();
    activeTabId.value = 11;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { viewTab: '11' } });
  });

  it('saveTab delegates', async () => {
    const { saveTab } = useViewMapFilters();
    await saveTab('B');
    expect(tabsStub.saveTab).toHaveBeenCalledWith('B', expect.any(Object));
  });
});
