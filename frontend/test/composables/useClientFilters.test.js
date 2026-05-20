/**
 * Tests para useClientFilters después de migrar persistencia a backend.
 * Cubre lógica pura: applyFilters, activeFilterCount, resetFilters, selectTab.
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
      const tab = { id: savedTabsRef.value.length + 1, view: 'client', name, filters, order: 0 };
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
import { useClientFilters } from '~/composables/useClientFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  tabsStub.saveTab.mockClear();
  tabsStub.deleteTab.mockClear();
});

const baseClient = (overrides = {}) => ({
  last_status: 'sent',
  project_types: ['web'],
  market_types: ['b2b'],
  total_proposals: 5,
  accepted_count: 2,
  last_sent_at: '2026-02-15',
  ...overrides,
});

describe('applyFilters', () => {
  it('returns all clients when no filters', () => {
    const { applyFilters } = useClientFilters();
    expect(applyFilters([baseClient(), baseClient({ last_status: 'draft' })])).toHaveLength(2);
  });

  it('filters by lastStatuses', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.lastStatuses = ['draft'];
    const list = [baseClient({ last_status: 'sent' }), baseClient({ last_status: 'draft' })];
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by projectTypes and marketTypes (any-of within array)', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const list = [
      baseClient({ project_types: ['web'], market_types: ['b2b'] }),
      baseClient({ project_types: ['app', 'web'], market_types: ['b2c'] }),
    ];
    currentFilters.projectTypes = ['app'];
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.projectTypes = [];
    currentFilters.marketTypes = ['b2c'];
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by totalProposals and accepted ranges', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const list = [
      baseClient({ total_proposals: 1, accepted_count: 0 }),
      baseClient({ total_proposals: 5, accepted_count: 3 }),
      baseClient({ total_proposals: 12, accepted_count: 8 }),
    ];
    currentFilters.totalProposalsMin = 3;
    currentFilters.totalProposalsMax = 10;
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.totalProposalsMin = null;
    currentFilters.totalProposalsMax = null;
    currentFilters.acceptedMin = 5;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by lastActivity range; drops clients without last_sent_at', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const list = [
      baseClient({ last_sent_at: '2026-01-10' }),
      baseClient({ last_sent_at: '2026-03-10' }),
      baseClient({ last_sent_at: null }),
    ];
    currentFilters.lastActivityAfter = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(1);
  });
});

describe('activeFilterCount + hasActiveFilters', () => {
  it('returns 0 / false initially', () => {
    const { activeFilterCount, hasActiveFilters } = useClientFilters();
    expect(activeFilterCount.value).toBe(0);
    expect(hasActiveFilters.value).toBe(false);
  });

  it('counts dimensions and ranges once', () => {
    const { currentFilters, activeFilterCount } = useClientFilters();
    currentFilters.lastStatuses = ['sent'];
    currentFilters.projectTypes = ['web'];
    currentFilters.totalProposalsMin = 1;
    currentFilters.totalProposalsMax = 10;
    currentFilters.lastActivityAfter = '2026-01-01';
    expect(activeFilterCount.value).toBe(4);
  });
});

describe('resetFilters + selectTab', () => {
  it('resetFilters clears state and sets activeTabId="all"', () => {
    const { currentFilters, activeTabId, resetFilters } = useClientFilters();
    currentFilters.lastStatuses = ['sent'];
    activeTabId.value = 5;
    resetFilters();
    expect(currentFilters.lastStatuses).toEqual([]);
    expect(activeTabId.value).toBe('all');
  });

  it('selectTab loads filters from saved tab', () => {
    savedTabsRef.value = [{ id: 9, view: 'client', name: 'X', filters: { lastStatuses: ['draft'] } }];
    const { currentFilters, activeTabId, selectTab } = useClientFilters();
    selectTab(9);
    expect(activeTabId.value).toBe(9);
    expect(currentFilters.lastStatuses).toEqual(['draft']);
  });
});

describe('URL sync + tab CRUD delegation', () => {
  it('updates router on activeTabId change using clientTab param', async () => {
    const { activeTabId } = useClientFilters();
    activeTabId.value = 3;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { clientTab: '3' } });
  });

  it('saveTab delegates to persistence layer', async () => {
    const { saveTab } = useClientFilters();
    await saveTab('Mine');
    expect(tabsStub.saveTab).toHaveBeenCalledWith('Mine', expect.any(Object));
  });

  it('deleteTab delegates and resets when active', async () => {
    savedTabsRef.value = [{ id: 7, view: 'client', name: 'Z', filters: {} }];
    const { deleteTab, activeTabId } = useClientFilters();
    activeTabId.value = 7;
    await deleteTab(7);
    expect(tabsStub.deleteTab).toHaveBeenCalledWith(7);
    expect(activeTabId.value).toBe('all');
  });
});
