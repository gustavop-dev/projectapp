/**
 * Tests for the useAccountingFilters factory (generalization of
 * useClientFilters): defaults, activeFilterCount, applyFilters with the
 * prebuilt matchers, and resetFilters.
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
      const tab = { id: savedTabsRef.value.length + 1, view: 'accounting_income', name, filters, order: 0 };
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

import * as savedFilterTabsModule from '~/composables/useSavedFilterTabs';
import {
  useAccountingFilters,
  matchDateRange,
  matchNumberRange,
  matchIncludes,
  matchEquals,
} from '~/composables/useAccountingFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  tabsStub.saveTab.mockClear();
  tabsStub.deleteTab.mockClear();
});

const DEFAULTS = {
  statuses: [],
  method: null,
  amountMin: null,
  amountMax: null,
  dateAfter: null,
  dateBefore: null,
};

function makeFilters() {
  return useAccountingFilters({
    viewName: 'accounting_income',
    defaults: DEFAULTS,
    matchers: {
      statuses: matchIncludes('status', 'statuses'),
      method: matchEquals('method', 'method'),
      amountRange: matchNumberRange('amount', 'amountMin', 'amountMax'),
      dateRange: matchDateRange('date', 'dateAfter', 'dateBefore'),
    },
    searchFields: ['concept', 'client_name'],
  });
}

const baseRecord = (overrides = {}) => ({
  status: 'paid',
  method: 'transfer',
  amount: 500000,
  date: '2026-02-15',
  concept: 'Página web',
  client_name: 'Acme SAS',
  ...overrides,
});

describe('defaults', () => {
  it('initializes currentFilters with defaults plus empty search', () => {
    const { currentFilters } = makeFilters();
    expect(currentFilters).toMatchObject({ ...DEFAULTS, search: '' });
  });

  it('starts with no active filters', () => {
    const { activeFilterCount, hasActiveFilters } = makeFilters();
    expect(activeFilterCount.value).toBe(0);
    expect(hasActiveFilters.value).toBe(false);
  });
});

describe('activeFilterCount', () => {
  it('counts each dimension once, ranges included', () => {
    const { currentFilters, activeFilterCount } = makeFilters();
    currentFilters.statuses = ['paid'];
    currentFilters.amountMin = 1000;
    currentFilters.amountMax = 900000;
    currentFilters.dateAfter = '2026-01-01';
    currentFilters.search = 'acme';
    expect(activeFilterCount.value).toBe(4);
  });

  it('does not count values equal to their defaults', () => {
    const { currentFilters, activeFilterCount } = makeFilters();
    currentFilters.statuses = [];
    currentFilters.method = null;
    currentFilters.search = '   ';
    expect(activeFilterCount.value).toBe(0);
  });
});

describe('applyFilters', () => {
  it('returns records untouched when no filter is active', () => {
    const { applyFilters } = makeFilters();
    const list = [baseRecord(), baseRecord({ status: 'pending' })];
    expect(applyFilters(list)).toBe(list);
  });

  it('filters with matchIncludes over multi-select arrays', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [baseRecord({ status: 'paid' }), baseRecord({ status: 'pending' })];
    currentFilters.statuses = ['pending'];
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].status).toBe('pending');
  });

  it('filters with matchEquals', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [baseRecord({ method: 'transfer' }), baseRecord({ method: 'cash' })];
    currentFilters.method = 'cash';
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].method).toBe('cash');
  });

  it('filters with matchNumberRange (numeric strings supported)', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [
      baseRecord({ amount: '100000' }),
      baseRecord({ amount: 500000 }),
      baseRecord({ amount: 1200000 }),
    ];
    currentFilters.amountMin = 200000;
    currentFilters.amountMax = 1000000;
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].amount).toBe(500000);
  });

  it('date range max bound is inclusive to end of day', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [
      baseRecord({ date: '2026-03-10T20:30:00' }),
      baseRecord({ date: '2026-03-11T08:00:00' }),
    ];
    currentFilters.dateBefore = '2026-03-10';
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].date).toBe('2026-03-10T20:30:00');
  });

  it('date range drops records without the date field', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [baseRecord({ date: '2026-02-15' }), baseRecord({ date: null })];
    currentFilters.dateAfter = '2026-01-01';
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('free-text search is case-insensitive across searchFields', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [
      baseRecord({ concept: 'Hosting anual', client_name: 'Beta Ltda' }),
      baseRecord({ concept: 'Página web', client_name: 'ACME SAS' }),
    ];
    currentFilters.search = 'acme';
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].client_name).toBe('ACME SAS');
  });

  it('combines search and matchers with AND semantics', () => {
    const { currentFilters, applyFilters } = makeFilters();
    const list = [
      baseRecord({ client_name: 'Acme SAS', status: 'paid' }),
      baseRecord({ client_name: 'Acme SAS', status: 'pending' }),
    ];
    currentFilters.search = 'acme';
    currentFilters.statuses = ['paid'];
    const result = applyFilters(list);
    expect(result).toHaveLength(1);
    expect(result[0].status).toBe('paid');
  });
});

describe('resetFilters', () => {
  it('restores defaults and returns to the "all" tab', () => {
    const { currentFilters, activeTabId, resetFilters, activeFilterCount } = makeFilters();
    currentFilters.statuses = ['paid'];
    currentFilters.search = 'acme';
    activeTabId.value = 5;
    resetFilters();
    expect(currentFilters.statuses).toEqual([]);
    expect(currentFilters.search).toBe('');
    expect(activeTabId.value).toBe('all');
    expect(activeFilterCount.value).toBe(0);
  });
});

describe('clearFilterKeys', () => {
  it('resets only the given keys to their defaults', () => {
    const { currentFilters, clearFilterKeys } = makeFilters();
    currentFilters.statuses = ['paid'];
    currentFilters.search = 'acme';
    clearFilterKeys(['statuses']);
    expect(currentFilters.statuses).toEqual([]);
    expect(currentFilters.search).toBe('acme');
  });

  it('ignores keys that are not part of the defaults', () => {
    const { currentFilters, clearFilterKeys } = makeFilters();
    currentFilters.statuses = ['paid'];
    clearFilterKeys(['nope']);
    expect(currentFilters.statuses).toEqual(['paid']);
  });
});

describe('saved tabs delegation', () => {
  it('saveTab delegates to the persistence layer with current filters', async () => {
    const { currentFilters, saveTab } = makeFilters();
    currentFilters.statuses = ['paid'];
    await saveTab('Pagados');
    expect(tabsStub.saveTab).toHaveBeenCalledWith(
      'Pagados',
      expect.objectContaining({ statuses: ['paid'] }),
    );
  });

  it('selectTab loads filters from a saved tab', () => {
    savedTabsRef.value = [
      { id: 9, view: 'accounting_income', name: 'X', filters: { statuses: ['pending'] } },
    ];
    const { currentFilters, activeTabId, selectTab } = makeFilters();
    selectTab(9);
    expect(activeTabId.value).toBe(9);
    expect(currentFilters.statuses).toEqual(['pending']);
  });

  it('deleteTab delegates and resets when the active tab is removed', async () => {
    savedTabsRef.value = [{ id: 7, view: 'accounting_income', name: 'Z', filters: {} }];
    const { deleteTab, activeTabId } = makeFilters();
    activeTabId.value = 7;
    await deleteTab(7);
    expect(tabsStub.deleteTab).toHaveBeenCalledWith(7);
    expect(activeTabId.value).toBe('all');
  });
});
