/**
 * Tests para useProposalFilters después de migrar persistencia a backend.
 *
 * La capa de persistencia (load/save/update/delete contra el backend) vive en
 * `useSavedFilterTabs` y se cubre en su propia suite. Aquí cubrimos la lógica
 * que sigue siendo pura: applyFilters por dimensión, activeFilterCount,
 * hasActiveFilters, resetFilters, selectTab y el sync de URL.
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
      const tab = { id: savedTabsRef.value.length + 1, view: 'proposal', name, filters, order: 0 };
      savedTabsRef.value = [...savedTabsRef.value, tab];
      return tab;
    }),
    updateTabFilters: jest.fn(),
    renameTab: jest.fn(async (id, name) => {
      const idx = savedTabsRef.value.findIndex((t) => t.id === id);
      if (idx === -1) return;
      const copy = [...savedTabsRef.value];
      copy[idx] = { ...copy[idx], name };
      savedTabsRef.value = copy;
    }),
    deleteTab: jest.fn(async (id) => {
      savedTabsRef.value = savedTabsRef.value.filter((t) => t.id !== id);
    }),
  };
  return { useSavedFilterTabs: () => stub, __stub: stub };
});

import { nextTick } from 'vue';
import * as savedFilterTabsModule from '~/composables/useSavedFilterTabs';
import { useProposalFilters } from '~/composables/useProposalFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  Object.values(tabsStub)
    .filter((v) => typeof v === 'function' && v.mockClear)
    .forEach((fn) => fn.mockClear && fn.mockClear());
});

describe('initialization', () => {
  it('starts with empty filters and activeTabId="all"', () => {
    const { currentFilters, activeTabId } = useProposalFilters();
    expect(activeTabId.value).toBe('all');
    expect(currentFilters.statuses).toEqual([]);
    expect(currentFilters.isActive).toBe('all');
  });

  it('reads initial activeTabId from URL ?tab=', () => {
    mockRoute.query = { tab: '5' };
    const { activeTabId } = useProposalFilters();
    expect(String(activeTabId.value)).toBe('5');
  });
});

describe('applyFilters', () => {
  const baseProp = (overrides = {}) => ({
    status: 'draft',
    project_type: 'web',
    market_type: 'b2b',
    currency: 'COP',
    language: 'es',
    total_investment: '1000',
    heat_score: 5,
    view_count: 0,
    created_at: '2026-02-15',
    last_activity_at: '2026-02-20',
    is_active: true,
    engagement_summary: { technical_viewed: false },
    ...overrides,
  });

  it('returns all proposals when no filters active', () => {
    const { applyFilters } = useProposalFilters();
    const list = [baseProp(), baseProp({ status: 'sent' })];
    expect(applyFilters(list)).toHaveLength(2);
  });

  it('filters by statuses', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    currentFilters.statuses = ['sent'];
    const list = [baseProp({ status: 'draft' }), baseProp({ status: 'sent' })];
    expect(applyFilters(list)).toHaveLength(1);
    expect(applyFilters(list)[0].status).toBe('sent');
  });

  it('filters by projectTypes / marketTypes / currencies / languages', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [
      baseProp({ project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es' }),
      baseProp({ project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en' }),
    ];

    currentFilters.projectTypes = ['app'];
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.projectTypes = [];

    currentFilters.marketTypes = ['b2c'];
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.marketTypes = [];

    currentFilters.currencies = ['USD'];
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.currencies = [];

    currentFilters.languages = ['en'];
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by investment range', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [
      baseProp({ total_investment: '500' }),
      baseProp({ total_investment: '3000' }),
      baseProp({ total_investment: '9000' }),
    ];
    currentFilters.investmentMin = 1000;
    currentFilters.investmentMax = 5000;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by heat score range', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [baseProp({ heat_score: 2 }), baseProp({ heat_score: 7 })];
    currentFilters.heatScoreMin = 5;
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.heatScoreMin = null;
    currentFilters.heatScoreMax = 4;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by view count range', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [baseProp({ view_count: 1 }), baseProp({ view_count: 15 })];
    currentFilters.viewCountMin = 10;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by created_at range', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [
      baseProp({ created_at: '2026-01-15T12:00:00Z' }),
      baseProp({ created_at: '2026-03-15T12:00:00Z' }),
    ];
    currentFilters.createdAfter = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.createdAfter = null;
    currentFilters.createdBefore = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by last_activity_at range with created_at fallback', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [
      baseProp({ last_activity_at: '2026-01-10' }),
      baseProp({ last_activity_at: '2026-03-10' }),
      baseProp({ last_activity_at: null, created_at: '2026-04-10' }),
    ];
    currentFilters.lastActivityAfter = '2026-02-01';
    expect(applyFilters(list)).toHaveLength(2);
  });

  it('drops proposals with no activity date when an activity range is set', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [baseProp({ last_activity_at: null, created_at: null })];
    currentFilters.lastActivityAfter = '2026-01-01';
    expect(applyFilters(list)).toHaveLength(0);
  });

  it('filters by isActive', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [baseProp({ is_active: true }), baseProp({ is_active: false })];
    currentFilters.isActive = 'active';
    expect(applyFilters(list)).toHaveLength(1);
    currentFilters.isActive = 'inactive';
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('filters by technicalViewed flag', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [
      baseProp({ engagement_summary: { technical_viewed: true } }),
      baseProp({ engagement_summary: { technical_viewed: false } }),
      baseProp({ engagement_summary: undefined }),
    ];
    currentFilters.technicalViewed = true;
    expect(applyFilters(list)).toHaveLength(1);
  });

  it('uses cached_heat_score as fallback when heat_score is missing', () => {
    const { currentFilters, applyFilters } = useProposalFilters();
    const list = [baseProp({ heat_score: undefined, cached_heat_score: 9 })];
    currentFilters.heatScoreMin = 8;
    expect(applyFilters(list)).toHaveLength(1);
  });
});

describe('activeFilterCount + hasActiveFilters', () => {
  it('returns 0 / false when no filters active', () => {
    const { activeFilterCount, hasActiveFilters } = useProposalFilters();
    expect(activeFilterCount.value).toBe(0);
    expect(hasActiveFilters.value).toBe(false);
  });

  it('counts each dimension once and ranges as a single dimension', () => {
    const { currentFilters, activeFilterCount, hasActiveFilters } = useProposalFilters();
    currentFilters.statuses = ['draft'];
    currentFilters.investmentMin = 1000;
    currentFilters.investmentMax = 5000;
    currentFilters.heatScoreMin = 3;
    currentFilters.isActive = 'active';
    currentFilters.technicalViewed = true;
    currentFilters.createdAfter = '2026-01-01';
    expect(activeFilterCount.value).toBe(6);
    expect(hasActiveFilters.value).toBe(true);
  });
});

describe('resetFilters', () => {
  it('clears all filters and sets activeTabId to all', () => {
    const { currentFilters, activeTabId, resetFilters } = useProposalFilters();
    currentFilters.statuses = ['draft'];
    currentFilters.investmentMin = 1000;
    activeTabId.value = 99;

    resetFilters();

    expect(currentFilters.statuses).toEqual([]);
    expect(currentFilters.investmentMin).toBeNull();
    expect(activeTabId.value).toBe('all');
  });
});

describe('selectTab', () => {
  it('loads filters from the selected tab', () => {
    savedTabsRef.value = [
      { id: 7, view: 'proposal', name: 'Activos', filters: { statuses: ['sent'], investmentMin: 5000 } },
    ];
    const { currentFilters, activeTabId, selectTab } = useProposalFilters();
    selectTab(7);
    expect(activeTabId.value).toBe(7);
    expect(currentFilters.statuses).toEqual(['sent']);
    expect(currentFilters.investmentMin).toBe(5000);
  });

  it('resets filters when selecting "all"', () => {
    const { currentFilters, activeTabId, selectTab } = useProposalFilters();
    currentFilters.statuses = ['draft'];
    selectTab('all');
    expect(activeTabId.value).toBe('all');
    expect(currentFilters.statuses).toEqual([]);
  });
});

describe('URL sync', () => {
  it('updates router.replace with the tab id as a string', async () => {
    const { activeTabId } = useProposalFilters();
    activeTabId.value = 42;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { tab: '42' } });
  });

  it('removes the tab query param when going back to all', async () => {
    mockRoute.query = { tab: '5', other: 'keep' };
    const { activeTabId } = useProposalFilters();
    activeTabId.value = 'all';
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { other: 'keep' } });
  });
});

describe('tab CRUD wiring', () => {
  it('saveTab delegates to the persistence layer and sets active', async () => {
    const { saveTab, activeTabId } = useProposalFilters();
    const tab = await saveTab('Mi tab');
    expect(tabsStub.saveTab).toHaveBeenCalledWith('Mi tab', expect.any(Object));
    expect(tab).not.toBeNull();
    expect(activeTabId.value).toBe(tab.id);
  });

  it('deleteTab delegates and resets when active', async () => {
    savedTabsRef.value = [{ id: 3, view: 'proposal', name: 'X', filters: {} }];
    const { deleteTab, activeTabId } = useProposalFilters();
    activeTabId.value = 3;
    await deleteTab(3);
    expect(tabsStub.deleteTab).toHaveBeenCalledWith(3);
    expect(activeTabId.value).toBe('all');
  });

  it('renameTab delegates to the persistence layer', async () => {
    savedTabsRef.value = [{ id: 4, view: 'proposal', name: 'Old', filters: {} }];
    const { renameTab } = useProposalFilters();
    await renameTab(4, 'New');
    expect(tabsStub.renameTab).toHaveBeenCalledWith(4, 'New');
  });
});
