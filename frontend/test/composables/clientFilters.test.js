/**
 * Filtros de /panel/clients sobre useAccountingFilters.
 *
 * La vista migró desde useClientFilters (su ancestro pre-generalización) al
 * factory compartido, así que estos tests corren el mismo CLIENT_FILTERS_CONFIG
 * que usa la página: cubren la lógica pura heredada (applyFilters,
 * activeFilterCount, resetFilters, selectTab, sync de URL) más los filtros
 * predefinidos nuevos.
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
  return { useSavedFilterTabs: () => stub, sameFilters: () => true, __stub: stub };
});

import { nextTick } from 'vue';
import * as savedFilterTabsModule from '~/composables/useSavedFilterTabs';
import { useAccountingFilters } from '~/composables/useAccountingFilters';
import { CLIENT_FILTERS_CONFIG, CLIENT_PRESETS } from '~/constants/clientFilters';

const tabsStub = savedFilterTabsModule.__stub;
const savedTabsRef = tabsStub.savedTabs;

const useClientFilters = () => useAccountingFilters(CLIENT_FILTERS_CONFIG);

beforeEach(() => {
  savedTabsRef.value = [];
  mockRoute.query = {};
  mockReplace.mockClear();
  tabsStub.saveTab.mockClear();
  tabsStub.deleteTab.mockClear();
  tabsStub.updateTabFilters.mockClear();
});

const baseClient = (overrides = {}) => ({
  last_status: 'sent',
  project_types: ['web'],
  market_types: ['b2b'],
  total_proposals: 5,
  accepted_count: 2,
  last_sent_at: '2026-02-15',
  hostings_count: 0,
  active_hostings_count: 0,
  active_projects_count: 0,
  nit: '900123456',
  cedula: '',
  billing_code: 'ACME',
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

  it('ignores the search key because the box is server-side', () => {
    const { currentFilters, applyFilters, activeFilterCount } = useClientFilters();
    const list = [baseClient({ last_status: 'sent' }), baseClient({ last_status: 'draft' })];
    currentFilters.search = 'nothing matches this';
    expect(applyFilters(list)).toHaveLength(2);
    expect(activeFilterCount.value).toBe(0);
  });
});

describe('predefined filters', () => {
  const withHosting = baseClient({ hostings_count: 2, active_hostings_count: 1 });
  const expiredHostingOnly = baseClient({ hostings_count: 1, active_hostings_count: 0 });
  const noHosting = baseClient();

  it('hosting-charged keeps only clients holding a live hosting', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.preset = 'hosting-charged';
    expect(applyFilters([withHosting, expiredHostingOnly, noHosting])).toEqual([withHosting]);
  });

  it('hosting-any also keeps the ones whose hostings all expired', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.preset = 'hosting-any';
    expect(applyFilters([withHosting, expiredHostingOnly, noHosting]))
      .toEqual([withHosting, expiredHostingOnly]);
  });

  it('no-billing treats a null billing_code and blank ids as missing', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const missing = baseClient({ nit: '', cedula: '   ', billing_code: null });
    const identified = baseClient({ nit: '', cedula: '', billing_code: 'KORE' });
    currentFilters.preset = 'no-billing';
    expect(applyFilters([missing, identified, baseClient()])).toEqual([missing]);
  });

  it('active-project ignores clients whose projects are all archived', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const live = baseClient({ active_projects_count: 1 });
    const archivedOnly = baseClient({ active_projects_count: 0 });
    currentFilters.preset = 'active-project';
    expect(applyFilters([live, archivedOnly])).toEqual([live]);
  });

  it('renders every preset ahead of the saved tabs', () => {
    savedTabsRef.value = [{ id: 4, view: 'client', name: 'Mia', filters: {} }];
    const { displayTabs } = useClientFilters();
    expect(displayTabs.value.slice(0, CLIENT_PRESETS.length).map((t) => t.id))
      .toEqual(CLIENT_PRESETS.map((p) => p.id));
    expect(displayTabs.value.every((t, i) => i >= CLIENT_PRESETS.length || t.builtin)).toBe(true);
  });

  it('keeps an edited preset local instead of persisting the drift', async () => {
    const { selectTab, currentFilters } = useClientFilters();
    selectTab('hosting-charged');
    currentFilters.lastStatuses = ['draft'];
    await nextTick();

    // The edit lands on the live filters...
    expect(currentFilters.preset).toBe('hosting-charged');
    expect(currentFilters.lastStatuses).toEqual(['draft']);
    // ...but a builtin tab has no server row to rewrite.
    expect(tabsStub.updateTabFilters).not.toHaveBeenCalled();
  });

  it('combines a preset with the panel filters instead of replacing them', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const wanted = baseClient({ active_hostings_count: 1, last_status: 'draft' });
    const otherStatus = baseClient({ active_hostings_count: 1, last_status: 'sent' });
    currentFilters.preset = 'hosting-charged';
    currentFilters.lastStatuses = ['draft'];
    expect(applyFilters([wanted, otherStatus, noHosting])).toEqual([wanted]);
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

  it('counts an applied preset as one active filter', () => {
    const { currentFilters, activeFilterCount } = useClientFilters();
    currentFilters.preset = 'hosting-charged';
    expect(activeFilterCount.value).toBe(1);
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

  it('selecting "all" clears an applied preset', () => {
    const { currentFilters, selectTab } = useClientFilters();
    selectTab('hosting-charged');
    expect(currentFilters.preset).toBe('hosting-charged');
    selectTab('all');
    expect(currentFilters.preset).toBe('');
  });
});

describe('URL sync + tab CRUD delegation', () => {
  it('updates router on activeTabId change using clientTab param', async () => {
    const { activeTabId } = useClientFilters();
    activeTabId.value = 3;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { clientTab: '3' } });
  });

  it('puts the preset id in the URL so the link survives a reload', async () => {
    const { selectTab } = useClientFilters();
    selectTab('hosting-charged');
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { clientTab: 'hosting-charged' } });
  });

  it('restores the preset from the URL before mount', () => {
    mockRoute.query = { clientTab: 'hosting-charged' };
    const { currentFilters, activeTabId } = useClientFilters();
    expect(activeTabId.value).toBe('hosting-charged');
    expect(currentFilters.preset).toBe('hosting-charged');
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

  it('reloadTabs returns the refreshed tabs after a settings reset', async () => {
    const { reloadTabs } = useClientFilters();
    savedTabsRef.value = [{ id: 2, view: 'client', name: 'Resembrado', filters: {} }];

    const reloaded = await reloadTabs();

    expect(reloaded).toEqual([
      { id: 2, view: 'client', name: 'Resembrado', filters: {} },
    ]);
  });
});
