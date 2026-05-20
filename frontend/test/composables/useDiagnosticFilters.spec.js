/**
 * Tests para useDiagnosticFilters después de migrar persistencia a backend.
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
      const tab = { id: savedTabsRef.value.length + 1, view: 'diagnostic', name, filters, order: 0 };
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
import { useDiagnosticFilters } from '~/composables/useDiagnosticFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  tabsStub.saveTab.mockClear();
  tabsStub.deleteTab.mockClear();
});

const baseDiag = (overrides = {}) => ({
  status: 'draft',
  investment_amount: 1000,
  created_at: '2026-02-15',
  ...overrides,
});

describe('applyFilters', () => {
  it('returns all diagnostics when no filters', () => {
    const { applyFilters } = useDiagnosticFilters();
    expect(applyFilters([baseDiag(), baseDiag({ status: 'sent' })])).toHaveLength(2);
  });

  it('filters by statuses', () => {
    const { currentFilters, applyFilters } = useDiagnosticFilters();
    currentFilters.statuses = ['sent'];
    const list = [baseDiag({ status: 'draft' }), baseDiag({ status: 'sent' })];
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by investment range', () => {
    const { currentFilters, applyFilters } = useDiagnosticFilters();
    const list = [
      baseDiag({ investment_amount: 500 }),
      baseDiag({ investment_amount: 3000 }),
      baseDiag({ investment_amount: 9000 }),
    ];
    currentFilters.investmentMin = 1000;
    currentFilters.investmentMax = 5000;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by createdAfter / createdBefore', () => {
    const { currentFilters, applyFilters } = useDiagnosticFilters();
    const list = [
      baseDiag({ created_at: '2026-01-10' }),
      baseDiag({ created_at: '2026-03-10' }),
    ];
    currentFilters.createdAfter = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.createdAfter = null;
    currentFilters.createdBefore = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('drops diagnostics without created_at when a date range is active', () => {
    const { currentFilters, applyFilters } = useDiagnosticFilters();
    currentFilters.createdAfter = '2026-01-01';
    expect(applyFilters([baseDiag({ created_at: null })])).toHaveLength(0);
  });
});

describe('activeFilterCount + hasActiveFilters', () => {
  it('returns 0 / false initially', () => {
    const { activeFilterCount, hasActiveFilters } = useDiagnosticFilters();
    expect(activeFilterCount.value).toBe(0);
    expect(hasActiveFilters.value).toBe(false);
  });

  it('counts min and max as separate dimensions', () => {
    const { currentFilters, activeFilterCount } = useDiagnosticFilters();
    currentFilters.statuses = ['sent'];
    currentFilters.investmentMin = 1000;
    currentFilters.investmentMax = 5000;
    currentFilters.createdAfter = '2026-01-01';
    expect(activeFilterCount.value).toBe(4);
  });
});

describe('resetFilters + selectTab', () => {
  it('resetFilters clears state', () => {
    const { currentFilters, activeTabId, resetFilters } = useDiagnosticFilters();
    currentFilters.statuses = ['sent'];
    activeTabId.value = 5;
    resetFilters();
    expect(currentFilters.statuses).toEqual([]);
    expect(activeTabId.value).toBe('all');
  });

  it('selectTab loads filters', () => {
    savedTabsRef.value = [{ id: 4, view: 'diagnostic', name: 'X', filters: { statuses: ['draft'] } }];
    const { currentFilters, activeTabId, selectTab } = useDiagnosticFilters();
    selectTab(4);
    expect(activeTabId.value).toBe(4);
    expect(currentFilters.statuses).toEqual(['draft']);
  });
});

describe('URL sync + delegation', () => {
  it('uses diagnosticTab URL param', async () => {
    const { activeTabId } = useDiagnosticFilters();
    activeTabId.value = 8;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { diagnosticTab: '8' } });
  });

  it('saveTab delegates', async () => {
    const { saveTab } = useDiagnosticFilters();
    await saveTab('A');
    expect(tabsStub.saveTab).toHaveBeenCalledWith('A', expect.any(Object));
  });
});
