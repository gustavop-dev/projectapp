/**
 * Tests for the useClientFilters composable.
 *
 * Covers: initialization, applyFilters (all 8 dimensions using flat project_types/market_types),
 * activeFilterCount, tab CRUD (save, update, delete, rename), resetFilters, selectTab,
 * tab limit enforcement, and URL sync via clientTab query param.
 *
 * Strategy: Mock vue-router + localStorage, then exercise the composable's public API.
 */

// Polyfill structuredClone for Jest (Node <17)
if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (val) => JSON.parse(JSON.stringify(val));
}

const mockRoute = { query: {} };
const mockReplace = jest.fn();

jest.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ replace: mockReplace }),
}));

// Mock crypto.randomUUID
let uuidCounter = 0;
global.crypto = { randomUUID: () => `uuid-${++uuidCounter}` };

import { nextTick } from 'vue';
import { useClientFilters } from '../../composables/useClientFilters';

// ── Test data factory ────────────────────────────────────────────────────────

function buildClient(overrides = {}) {
  return {
    last_status: 'active',
    project_types: ['web'],
    market_types: ['b2b'],
    total_proposals: 5,
    accepted_count: 2,
    last_sent_at: '2026-02-15T12:00:00Z',
    ...overrides,
  };
}

describe('useClientFilters', () => {
  beforeEach(() => {
    localStorage.clear();
    mockRoute.query = {};
    mockReplace.mockClear();
    uuidCounter = 0;
  });

  // ── Initialization ──────────────────────────────────────────────────────────

  describe('initialization', () => {
    it('starts with empty filters and no saved tabs', () => {
      const { currentFilters, savedTabs, activeTabId } = useClientFilters();

      expect(activeTabId.value).toBe('all');
      expect(savedTabs.value).toEqual([]);
      expect(currentFilters.lastStatuses).toEqual([]);
      expect(currentFilters.projectTypes).toEqual([]);
      expect(currentFilters.totalProposalsMin).toBeNull();
    });

    it('loads saved tabs from localStorage', () => {
      const tabs = [{ id: 'tab-1', name: 'Test', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('client_filter_tabs', JSON.stringify(tabs));

      const { savedTabs } = useClientFilters();

      expect(savedTabs.value).toHaveLength(1);
      expect(savedTabs.value[0].name).toBe('Test');
    });

    it('returns empty array for corrupted localStorage', () => {
      localStorage.setItem('client_filter_tabs', 'invalid-json{');

      const { savedTabs } = useClientFilters();

      expect(savedTabs.value).toEqual([]);
    });

    it('restores activeTabId from clientTab query param', () => {
      const tabs = [{ id: 'saved-1', name: 'Saved', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('client_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { clientTab: 'saved-1' };

      const { activeTabId } = useClientFilters();

      expect(activeTabId.value).toBe('saved-1');
    });

    it('falls back to all when clientTab does not exist in saved tabs', () => {
      mockRoute.query = { clientTab: 'nonexistent' };

      const { activeTabId } = useClientFilters();

      expect(activeTabId.value).toBe('all');
    });
  });

  // ── applyFilters — lastStatuses ────────────────────────────────────────────

  describe('applyFilters — lastStatuses', () => {
    const clients = [
      buildClient({ last_status: 'active' }),
      buildClient({ last_status: 'inactive' }),
      buildClient({ last_status: 'prospect' }),
    ];

    it('returns all clients when no filters active', () => {
      const { applyFilters } = useClientFilters();

      expect(applyFilters(clients)).toHaveLength(3);
    });

    it('filters by single status', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastStatuses = ['active'];

      expect(applyFilters(clients)).toHaveLength(1);
      expect(applyFilters(clients)[0].last_status).toBe('active');
    });

    it('filters by multiple statuses', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastStatuses = ['active', 'prospect'];

      expect(applyFilters(clients)).toHaveLength(2);
    });
  });

  // ── applyFilters — projectTypes via proposals.some() ───────────────────────

  describe('applyFilters — projectTypes', () => {
    const clients = [
      buildClient({ project_types: ['web'] }),
      buildClient({ project_types: ['app'] }),
      buildClient({ project_types: ['web', 'app'] }),
    ];

    it('filters clients whose proposals match projectType', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.projectTypes = ['app'];

      const result = applyFilters(clients);
      expect(result).toHaveLength(2);
    });

    it('excludes clients with no matching proposal projectType', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.projectTypes = ['saas'];

      expect(applyFilters(clients)).toHaveLength(0);
    });
  });

  // ── applyFilters — marketTypes via proposals.some() ────────────────────────

  describe('applyFilters — marketTypes', () => {
    const clients = [
      buildClient({ market_types: ['b2b'] }),
      buildClient({ market_types: ['b2c'] }),
    ];

    it('filters clients whose proposals match marketType', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.marketTypes = ['b2c'];

      expect(applyFilters(clients)).toHaveLength(1);
    });
  });

  // ── applyFilters — totalProposals range ────────────────────────────────────

  describe('applyFilters — totalProposals range', () => {
    const clients = [
      buildClient({ total_proposals: 2 }),
      buildClient({ total_proposals: 5 }),
      buildClient({ total_proposals: 10 }),
    ];

    it('filters by totalProposalsMin', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.totalProposalsMin = 4;

      expect(applyFilters(clients)).toHaveLength(2);
    });

    it('filters by totalProposalsMax', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.totalProposalsMax = 5;

      expect(applyFilters(clients)).toHaveLength(2);
    });

    it('filters by both min and max', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.totalProposalsMin = 3;
      currentFilters.totalProposalsMax = 7;

      expect(applyFilters(clients)).toHaveLength(1);
      expect(applyFilters(clients)[0].total_proposals).toBe(5);
    });
  });

  // ── applyFilters — accepted range ──────────────────────────────────────────

  describe('applyFilters — accepted range', () => {
    const clients = [
      buildClient({ accepted_count: 0 }),
      buildClient({ accepted_count: 3 }),
      buildClient({ accepted_count: 8 }),
    ];

    it('filters by acceptedMin', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.acceptedMin = 2;

      expect(applyFilters(clients)).toHaveLength(2);
    });

    it('filters by acceptedMax', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.acceptedMax = 5;

      expect(applyFilters(clients)).toHaveLength(2);
    });
  });

  // ── applyFilters — lastActivity date range ─────────────────────────────────

  describe('applyFilters — lastActivity date range', () => {
    const clients = [
      buildClient({ last_sent_at: '2026-01-15T12:00:00Z' }),
      buildClient({ last_sent_at: '2026-03-15T12:00:00Z' }),
    ];

    it('filters by lastActivityAfter', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastActivityAfter = '2026-02-01';

      expect(applyFilters(clients)).toHaveLength(1);
      expect(applyFilters(clients)[0].last_sent_at).toBe('2026-03-15T12:00:00Z');
    });

    it('filters by lastActivityBefore', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastActivityBefore = '2026-02-01';

      expect(applyFilters(clients)).toHaveLength(1);
      expect(applyFilters(clients)[0].last_sent_at).toBe('2026-01-15T12:00:00Z');
    });

    it('excludes clients with null last_sent_at when activity filter is active', () => {
      const clientsWithNull = [
        buildClient({ last_sent_at: null }),
        buildClient({ last_sent_at: '2026-03-15T12:00:00Z' }),
      ];
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastActivityAfter = '2026-01-01';

      expect(applyFilters(clientsWithNull)).toHaveLength(1);
    });
  });

  // ── applyFilters — combined ────────────────────────────────────────────────

  describe('applyFilters — combined filters', () => {
    const clients = [
      buildClient({ last_status: 'active', total_proposals: 5, project_types: ['web'], market_types: ['b2b'] }),
      buildClient({ last_status: 'active', total_proposals: 2, project_types: ['app'], market_types: ['b2c'] }),
      buildClient({ last_status: 'inactive', total_proposals: 10, project_types: ['web'], market_types: ['b2b'] }),
    ];

    it('applies multiple filter dimensions simultaneously', () => {
      const { currentFilters, applyFilters } = useClientFilters();
      currentFilters.lastStatuses = ['active'];
      currentFilters.totalProposalsMin = 3;

      const result = applyFilters(clients);
      expect(result).toHaveLength(1);
      expect(result[0].total_proposals).toBe(5);
    });
  });

  // ── activeFilterCount ──────────────────────────────────────────────────────

  describe('activeFilterCount', () => {
    it('returns 0 when no filters active', () => {
      const { activeFilterCount } = useClientFilters();

      expect(activeFilterCount.value).toBe(0);
    });

    it('increments per active dimension', () => {
      const { currentFilters, activeFilterCount } = useClientFilters();
      currentFilters.lastStatuses = ['active'];
      currentFilters.projectTypes = ['web'];

      expect(activeFilterCount.value).toBe(2);
    });

    it('counts range as single dimension', () => {
      const { currentFilters, activeFilterCount } = useClientFilters();
      currentFilters.totalProposalsMin = 1;
      currentFilters.totalProposalsMax = 10;

      expect(activeFilterCount.value).toBe(1);
    });

    it('counts all 6 filter dimensions', () => {
      const { currentFilters, activeFilterCount } = useClientFilters();
      currentFilters.lastStatuses = ['active'];
      currentFilters.projectTypes = ['web'];
      currentFilters.marketTypes = ['b2b'];
      currentFilters.totalProposalsMin = 1;
      currentFilters.acceptedMin = 1;
      currentFilters.lastActivityAfter = '2026-01-01';

      expect(activeFilterCount.value).toBe(6);
    });
  });

  // ── hasActiveFilters ───────────────────────────────────────────────────────

  describe('hasActiveFilters', () => {
    it('returns false when no filters active', () => {
      const { hasActiveFilters } = useClientFilters();

      expect(hasActiveFilters.value).toBe(false);
    });

    it('returns true when any filter active', () => {
      const { currentFilters, hasActiveFilters } = useClientFilters();
      currentFilters.lastStatuses = ['active'];

      expect(hasActiveFilters.value).toBe(true);
    });
  });

  // ── Tab CRUD ───────────────────────────────────────────────────────────────

  describe('tab CRUD', () => {
    it('saveTab creates a new tab with current filters', () => {
      const { currentFilters, savedTabs, saveTab } = useClientFilters();
      currentFilters.lastStatuses = ['active'];

      const tab = saveTab('My Tab');

      expect(tab).not.toBeNull();
      expect(tab.name).toBe('My Tab');
      expect(tab.filters.lastStatuses).toEqual(['active']);
      expect(savedTabs.value).toHaveLength(1);
    });

    it('saveTab returns null when max tabs reached', () => {
      const { savedTabs, saveTab } = useClientFilters();
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `tab-${i}`, name: `Tab ${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      const result = saveTab('Overflow');

      expect(result).toBeNull();
      expect(savedTabs.value).toHaveLength(12);
    });

    it('saveTab sets the new tab as active', () => {
      const { activeTabId, savedTabs, saveTab } = useClientFilters();

      saveTab('Active Tab');

      expect(activeTabId.value).not.toBe('all');
      expect(savedTabs.value[0].id).toBe(activeTabId.value);
    });

    it('deleteTab removes the tab', () => {
      const { savedTabs, saveTab, deleteTab } = useClientFilters();
      saveTab('To Delete');

      const tabId = savedTabs.value[0].id;
      deleteTab(tabId);

      expect(savedTabs.value).toHaveLength(0);
    });

    it('deleteTab resets to all when active tab is deleted', () => {
      const { activeTabId, savedTabs, saveTab, deleteTab } = useClientFilters();
      saveTab('Active');

      const tabId = savedTabs.value[0].id;
      expect(activeTabId.value).toBe(tabId);
      deleteTab(tabId);

      expect(activeTabId.value).toBe('all');
    });

    it('renameTab changes the tab name', () => {
      const { savedTabs, saveTab, renameTab } = useClientFilters();
      saveTab('Original');

      const tabId = savedTabs.value[0].id;
      renameTab(tabId, 'Renamed');

      expect(savedTabs.value[0].name).toBe('Renamed');
    });

    it('renameTab does nothing for nonexistent tab', () => {
      const { savedTabs, saveTab, renameTab } = useClientFilters();
      saveTab('Only');

      renameTab('nonexistent-id', 'New Name');

      expect(savedTabs.value[0].name).toBe('Only');
    });
  });

  // ── watcher: activeTabId → URL sync ─────────────────────────────────────────

  describe('activeTabId watcher', () => {
    it('syncs activeTabId to URL clientTab query param', async () => {
      const { activeTabId } = useClientFilters();

      activeTabId.value = 'custom-tab';
      await nextTick();

      expect(mockReplace).toHaveBeenCalledWith({
        query: { clientTab: 'custom-tab' },
      });
    });

    it('removes clientTab from URL when set to all', async () => {
      const { activeTabId } = useClientFilters();

      activeTabId.value = 'some-tab';
      await nextTick();
      mockReplace.mockClear();

      activeTabId.value = 'all';
      await nextTick();

      expect(mockReplace).toHaveBeenCalledWith({ query: {} });
    });
  });

  // ── watcher: currentFilters → updateTab ────────────────────────────────────

  describe('currentFilters deep watcher', () => {
    it('auto-updates active tab when filters change', async () => {
      const { currentFilters, savedTabs, saveTab } = useClientFilters();
      const tab = saveTab('Auto');

      currentFilters.lastStatuses = ['inactive'];
      await nextTick();

      const updated = savedTabs.value.find((t) => t.id === tab.id);
      expect(updated.filters.lastStatuses).toEqual(['inactive']);
    });

    it('skips updateTab when activeTabId points to nonexistent tab', async () => {
      const { currentFilters, activeTabId, savedTabs } = useClientFilters();
      activeTabId.value = 'nonexistent';
      await nextTick();

      currentFilters.lastStatuses = ['active'];
      await nextTick();

      expect(savedTabs.value).toHaveLength(0);
    });
  });

  // ── resetFilters ───────────────────────────────────────────────────────────

  describe('resetFilters', () => {
    it('clears all filters to defaults', () => {
      const { currentFilters, resetFilters } = useClientFilters();
      currentFilters.lastStatuses = ['active'];
      currentFilters.totalProposalsMin = 5;

      resetFilters();

      expect(currentFilters.lastStatuses).toEqual([]);
      expect(currentFilters.totalProposalsMin).toBeNull();
    });

    it('sets activeTabId to all', () => {
      const { activeTabId, saveTab, resetFilters } = useClientFilters();
      saveTab('Tab');

      resetFilters();

      expect(activeTabId.value).toBe('all');
    });
  });

  // ── selectTab ──────────────────────────────────────────────────────────────

  describe('selectTab', () => {
    it('selects all and resets filters', () => {
      const { currentFilters, activeTabId, selectTab } = useClientFilters();
      currentFilters.lastStatuses = ['active'];

      selectTab('all');

      expect(activeTabId.value).toBe('all');
      expect(currentFilters.lastStatuses).toEqual([]);
    });

    it('loads filters from saved tab', () => {
      const { currentFilters, savedTabs, activeTabId, selectTab } = useClientFilters();
      savedTabs.value = [{
        id: 'tab-x', name: 'Test',
        filters: {
          lastStatuses: ['inactive'], projectTypes: [], marketTypes: [],
          totalProposalsMin: null, totalProposalsMax: null,
          acceptedMin: null, acceptedMax: null,
          lastActivityAfter: null, lastActivityBefore: null,
        },
        createdAt: '', updatedAt: '',
      }];

      selectTab('tab-x');

      expect(activeTabId.value).toBe('tab-x');
      expect(currentFilters.lastStatuses).toEqual(['inactive']);
    });
  });

  // ── isTabLimitReached ──────────────────────────────────────────────────────

  describe('isTabLimitReached', () => {
    it('returns false when under limit', () => {
      const { isTabLimitReached } = useClientFilters();

      expect(isTabLimitReached.value).toBe(false);
    });

    it('returns true when at limit', () => {
      const { savedTabs, isTabLimitReached } = useClientFilters();
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `t-${i}`, name: `T${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      expect(isTabLimitReached.value).toBe(true);
    });
  });
});
