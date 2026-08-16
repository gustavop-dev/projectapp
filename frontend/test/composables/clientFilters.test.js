/**
 * Filtros de /panel/clients sobre useAccountingFilters.
 *
 * La vista corre sobre el factory compartido con el mismo CLIENT_FILTERS_CONFIG
 * que usa la página: estos tests cubren la lógica pura (applyFilters,
 * activeFilterCount, resetFilters, selectTab, sync de URL) más los dos niveles
 * — módulo de negocio y sus subfiltros — y la traducción de la clave `preset`
 * que aquellos reemplazaron.
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
import {
  CLIENT_FILTERS_CONFIG,
  CLIENT_MODULES,
  CLIENT_SUBFILTERS,
  clientSubfiltersFor,
  matchDocumentsStatus,
  matchesSubfilter,
  normalizeLegacyPreset,
  subfilterOptionsFor,
} from '~/constants/clientFilters';

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
  projects_count: 1,
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

describe('subfilters', () => {
  const withHosting = baseClient({ hostings_count: 2, active_hostings_count: 1 });
  const expiredHostingOnly = baseClient({ hostings_count: 1, active_hostings_count: 0 });
  const noHosting = baseClient();

  it('hosting-charged keeps only clients holding a live hosting', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.hostingStatus = 'charged';
    expect(applyFilters([withHosting, expiredHostingOnly, noHosting])).toEqual([withHosting]);
  });

  it('hosting-any also keeps the ones whose hostings all expired', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.hostingStatus = 'any';
    expect(applyFilters([withHosting, expiredHostingOnly, noHosting]))
      .toEqual([withHosting, expiredHostingOnly]);
  });

  it('no-hosting keeps exactly the complement of hosting-any', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    currentFilters.hostingStatus = 'none';
    expect(applyFilters([withHosting, expiredHostingOnly, noHosting])).toEqual([noHosting]);
  });

  it('no-billing treats a null billing_code and blank ids as missing', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const missing = baseClient({ nit: '', cedula: '   ', billing_code: null });
    const identified = baseClient({ nit: '', cedula: '', billing_code: 'KORE' });
    currentFilters.billingData = 'missing';
    expect(applyFilters([missing, identified, baseClient()])).toEqual([missing]);
  });

  it('active-project ignores clients whose projects are all archived', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const live = baseClient({ projects_count: 2, active_projects_count: 1 });
    const archivedOnly = baseClient({ projects_count: 2, active_projects_count: 0 });
    currentFilters.projectStatus = 'active';
    expect(applyFilters([live, archivedOnly])).toEqual([live]);
  });

  it('no-project means none at all, not merely none active', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const archivedOnly = baseClient({ projects_count: 2, active_projects_count: 0 });
    const none = baseClient({ projects_count: 0, active_projects_count: 0 });
    currentFilters.projectStatus = 'none';
    expect(applyFilters([archivedOnly, none])).toEqual([none]);
  });

  it('keeps an edited subfilter local instead of persisting the drift', async () => {
    const { selectTab, currentFilters } = useClientFilters();
    selectTab('hosting-charged');
    currentFilters.lastStatuses = ['draft'];
    await nextTick();

    // The edit lands on the live filters...
    expect(currentFilters.hostingStatus).toBe('charged');
    expect(currentFilters.lastStatuses).toEqual(['draft']);
    // ...but a builtin tab has no server row to rewrite.
    expect(tabsStub.updateTabFilters).not.toHaveBeenCalled();
  });

  it('combines a subfilter with the panel filters instead of replacing them', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const wanted = baseClient({ active_hostings_count: 1, last_status: 'draft' });
    const otherStatus = baseClient({ active_hostings_count: 1, last_status: 'sent' });
    currentFilters.hostingStatus = 'charged';
    currentFilters.lastStatuses = ['draft'];
    expect(applyFilters([wanted, otherStatus, noHosting])).toEqual([wanted]);
  });

  it('cuts from two different modules narrow the list together', () => {
    const { currentFilters, applyFilters } = useClientFilters();
    const both = baseClient({ active_hostings_count: 1, nit: '', cedula: '', billing_code: null });
    const hostingOnly = baseClient({ active_hostings_count: 1 });
    currentFilters.hostingStatus = 'charged';
    currentFilters.billingData = 'missing';
    expect(applyFilters([both, hostingOnly])).toEqual([both]);
  });

  it('matchesSubfilter agrees with applying the same subfilter', () => {
    const rows = [withHosting, expiredHostingOnly, noHosting];
    for (const sub of CLIENT_SUBFILTERS) {
      const { currentFilters, applyFilters } = useClientFilters();
      Object.assign(currentFilters, sub.filters);
      expect(rows.filter((r) => matchesSubfilter(sub, r))).toEqual(applyFilters(rows));
    }
  });
});

describe('taxonomy', () => {
  it('every subfilter belongs to a declared module', () => {
    const ids = CLIENT_MODULES.map((m) => m.id);
    expect(CLIENT_SUBFILTERS.every((s) => ids.includes(s.module))).toBe(true);
  });

  it('keeps the ids that already shipped in URLs', () => {
    const ids = CLIENT_SUBFILTERS.map((s) => s.id);
    expect(ids).toEqual(expect.arrayContaining([
      'hosting-charged', 'hosting-any', 'no-billing', 'active-project',
    ]));
  });

  it('carries the seven proposal-status cuts that used to be seeded tabs', () => {
    expect(clientSubfiltersFor('proposals').map((s) => s.name)).toEqual([
      'Draft', 'Sent/Viewed', 'Negociación', 'Accepted', 'Expired', 'Rejected', 'Finished',
    ]);
  });

  it('offers every hosting subfilter as a panel option too', () => {
    expect(subfilterOptionsFor('hosting', 'hostingStatus')).toEqual([
      { value: 'charged', label: 'Con hosting cobrado' },
      { value: 'any', label: 'Con hosting (histórico)' },
      { value: 'none', label: 'Sin hosting' },
    ]);
  });

  it('offers every documents subfilter as a panel option too', () => {
    expect(subfilterOptionsFor('documents', 'documentsStatus')).toEqual([
      { value: 'with', label: 'Con documentos' },
      { value: 'none', label: 'Sin documentos' },
      { value: 'no-project', label: 'Con documentos sin proyecto' },
    ]);
  });
});

describe('documents module', () => {
  it('matchDocumentsStatus reads the association aggregates for its three cuts', () => {
    const withDocs = baseClient({ documents_count: 3, documents_no_project_count: 1 });
    const without = baseClient({ documents_count: 0, documents_no_project_count: 0 });

    expect(matchDocumentsStatus(withDocs, 'with')).toBe(true);
    expect(matchDocumentsStatus(without, 'with')).toBe(false);
    expect(matchDocumentsStatus(without, 'none')).toBe(true);
    expect(matchDocumentsStatus(withDocs, 'none')).toBe(false);
    expect(matchDocumentsStatus(withDocs, 'no-project')).toBe(true);
    expect(matchDocumentsStatus(without, 'no-project')).toBe(false);
  });

  it('level 2 lists the documents subfilters under their module', () => {
    const { currentFilters, displayTabs } = useClientFilters();
    currentFilters.module = 'documents';
    expect(displayTabs.value.map((t) => t.id))
      .toEqual(['docs-with', 'docs-none', 'docs-no-project']);
  });
});

describe('module (level 1)', () => {
  it('narrows nothing on its own', () => {
    const { currentFilters, applyFilters, activeFilterCount } = useClientFilters();
    const list = [baseClient(), baseClient({ hostings_count: 3 })];
    currentFilters.module = 'hosting';
    expect(applyFilters(list)).toHaveLength(2);
    expect(activeFilterCount.value).toBe(0);
  });

  it('level 2 only lists the subfilters of the active module', () => {
    const { currentFilters, displayTabs } = useClientFilters();
    currentFilters.module = 'hosting';
    expect(displayTabs.value.map((t) => t.id))
      .toEqual(['hosting-charged', 'hosting-any', 'no-hosting']);
  });

  it('groups a saved tab under the module it was saved in', () => {
    savedTabsRef.value = [
      { id: 4, view: 'client', name: 'Mía', filters: { module: 'hosting', hostingStatus: 'any' } },
      { id: 5, view: 'client', name: 'Otra', filters: { module: 'proposals' } },
    ];
    const { currentFilters, displayTabs } = useClientFilters();
    currentFilters.module = 'hosting';
    expect(displayTabs.value.map((t) => t.name)).toContain('Mía');
    expect(displayTabs.value.map((t) => t.name)).not.toContain('Otra');
  });

  it('shows a module-less saved tab under Todos', () => {
    savedTabsRef.value = [{ id: 6, view: 'client', name: 'Vieja', filters: { lastStatuses: ['draft'] } }];
    const { displayTabs } = useClientFilters();
    expect(displayTabs.value.map((t) => t.name)).toContain('Vieja');
  });

  it('selecting a subfilter switches to its module', () => {
    const { currentFilters, selectTab } = useClientFilters();
    selectTab('no-billing');
    expect(currentFilters.module).toBe('accounting');
  });

  it('mirrors the module in the URL and drops it back at the default', async () => {
    const { selectModule } = useClientFilters();
    selectModule('hosting');
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { clientModule: 'hosting' } });

    selectModule('all');
    await nextTick();
    expect(mockReplace).toHaveBeenLastCalledWith({ query: {} });
  });

  it('restores the module from the URL before mount', () => {
    mockRoute.query = { clientModule: 'projects' };
    const { activeModule } = useClientFilters();
    expect(activeModule.value).toBe('projects');
  });

  it('clearing the filters keeps the module being read', () => {
    const { currentFilters, resetFilters } = useClientFilters();
    currentFilters.module = 'hosting';
    currentFilters.hostingStatus = 'charged';
    resetFilters();
    expect(currentFilters.hostingStatus).toBe('');
    expect(currentFilters.module).toBe('hosting');
  });
});

describe('legacy preset key', () => {
  it('translates a tab saved with the old single preset key', () => {
    expect(normalizeLegacyPreset({ preset: 'hosting-charged' }))
      .toEqual({ hostingStatus: 'charged', module: 'hosting' });
  });

  it('leaves filters without the legacy key untouched', () => {
    const filters = { lastStatuses: ['draft'] };
    expect(normalizeLegacyPreset(filters)).toBe(filters);
  });

  it('a tab stored with the legacy key still filters once loaded', () => {
    savedTabsRef.value = [
      { id: 8, view: 'client', name: 'Vieja', filters: { preset: 'hosting-charged' } },
    ];
    const { currentFilters, selectTab, applyFilters } = useClientFilters();
    selectTab(8);
    expect(currentFilters.hostingStatus).toBe('charged');
    const live = baseClient({ active_hostings_count: 1 });
    expect(applyFilters([live, baseClient()])).toEqual([live]);
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

  it('counts an applied subfilter as one active filter', () => {
    const { currentFilters, activeFilterCount } = useClientFilters();
    currentFilters.hostingStatus = 'charged';
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

  it('selecting "all" clears an applied subfilter but stays in its module', () => {
    const { currentFilters, selectTab } = useClientFilters();
    selectTab('hosting-charged');
    expect(currentFilters.hostingStatus).toBe('charged');
    selectTab('all');
    expect(currentFilters.hostingStatus).toBe('');
    expect(currentFilters.module).toBe('hosting');
  });
});

describe('URL sync + tab CRUD delegation', () => {
  it('updates router on activeTabId change using clientTab param', async () => {
    const { activeTabId } = useClientFilters();
    activeTabId.value = 3;
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith({ query: { clientTab: '3' } });
  });

  it('puts the subfilter id in the URL so the link survives a reload', async () => {
    const { selectTab } = useClientFilters();
    selectTab('hosting-charged');
    await nextTick();
    expect(mockReplace).toHaveBeenCalledWith(
      expect.objectContaining({ query: expect.objectContaining({ clientTab: 'hosting-charged' }) }),
    );
  });

  it('restores the subfilter and its module from the URL before mount', () => {
    mockRoute.query = { clientTab: 'hosting-charged' };
    const { currentFilters, activeTabId, activeModule } = useClientFilters();
    expect(activeTabId.value).toBe('hosting-charged');
    expect(currentFilters.hostingStatus).toBe('charged');
    expect(activeModule.value).toBe('hosting');
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
