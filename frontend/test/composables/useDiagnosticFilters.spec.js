/**
 * Tests for the useDiagnosticFilters composable.
 *
 * Covers: initialization, applyFilters (status, investment range, date range,
 * no-created_at fallback), activeFilterCount, hasActiveFilters, isTabLimitReached,
 * tab CRUD (save, update, delete, rename), resetFilters, selectTab, and URL sync.
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

let uuidCounter = 0;
global.crypto = { randomUUID: () => `uuid-${++uuidCounter}` };

import { nextTick } from 'vue';
import { useDiagnosticFilters } from '../../composables/useDiagnosticFilters';

describe('useDiagnosticFilters', () => {
  beforeEach(() => {
    localStorage.clear();
    mockRoute.query = {};
    mockReplace.mockClear();
    uuidCounter = 0;
  });

  // ── Initialization ──────────────────────────────────────────────────────────

  describe('initialization', () => {
    it('starts with empty filters and no saved tabs', () => {
      const { currentFilters, savedTabs, activeTabId } = useDiagnosticFilters();

      expect(activeTabId.value).toBe('all');
      expect(savedTabs.value).toEqual([]);
      expect(currentFilters.statuses).toEqual([]);
      expect(currentFilters.investmentMin).toBeNull();
      expect(currentFilters.investmentMax).toBeNull();
      expect(currentFilters.createdAfter).toBeNull();
      expect(currentFilters.createdBefore).toBeNull();
    });

    it('loads saved tabs from localStorage on mount', () => {
      const tabs = [{ id: 'tab-1', name: 'Test', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('diagnostic_filter_tabs', JSON.stringify(tabs));

      const { savedTabs } = useDiagnosticFilters();

      expect(savedTabs.value).toHaveLength(1);
      expect(savedTabs.value[0].name).toBe('Test');
    });

    it('returns empty tabs array for corrupted localStorage value', () => {
      localStorage.setItem('diagnostic_filter_tabs', 'invalid{json');

      const { savedTabs } = useDiagnosticFilters();

      expect(savedTabs.value).toEqual([]);
    });

    it('restores activeTabId from diagnosticTab route query', () => {
      const tabs = [{ id: 'saved-1', name: 'Saved', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('diagnostic_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { diagnosticTab: 'saved-1' };

      const { activeTabId } = useDiagnosticFilters();

      expect(activeTabId.value).toBe('saved-1');
    });

    it('falls back to all when URL tab id is not found in saved tabs', () => {
      mockRoute.query = { diagnosticTab: 'nonexistent' };

      const { activeTabId } = useDiagnosticFilters();

      expect(activeTabId.value).toBe('all');
    });

    it('loads saved tab filters when initializing from URL query', () => {
      const tabs = [{
        id: 'saved-2',
        name: 'Saved',
        filters: { statuses: ['active'], investmentMin: 500, investmentMax: null, createdAfter: null, createdBefore: null },
        createdAt: '',
        updatedAt: '',
      }];
      localStorage.setItem('diagnostic_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { diagnosticTab: 'saved-2' };

      const { activeTabId, currentFilters, isFilterPanelOpen } = useDiagnosticFilters();

      expect(activeTabId.value).toBe('saved-2');
      expect(currentFilters.statuses).toEqual(['active']);
      expect(currentFilters.investmentMin).toBe(500);
      expect(isFilterPanelOpen.value).toBe(true);
    });
  });

  // ── applyFilters — status ───────────────────────────────────────────────────

  describe('applyFilters — status', () => {
    const diagnostics = [
      { status: 'draft', investment_amount: '1000', created_at: '2026-01-01' },
      { status: 'active', investment_amount: '5000', created_at: '2026-02-01' },
      { status: 'closed', investment_amount: '10000', created_at: '2026-03-01' },
    ];

    it('returns all diagnostics when no filters are active', () => {
      const { applyFilters } = useDiagnosticFilters();

      expect(applyFilters(diagnostics)).toHaveLength(3);
    });

    it('filters by a single status value', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      expect(applyFilters(diagnostics)).toHaveLength(1);
      expect(applyFilters(diagnostics)[0].status).toBe('draft');
    });

    it('filters by multiple status values', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.statuses = ['draft', 'active'];

      expect(applyFilters(diagnostics)).toHaveLength(2);
    });

    it('returns empty array when no diagnostic matches the status filter', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.statuses = ['pending'];

      expect(applyFilters(diagnostics)).toEqual([]);
    });
  });

  // ── applyFilters — investment range ─────────────────────────────────────────

  describe('applyFilters — investment range', () => {
    const diagnostics = [
      { status: 'draft', investment_amount: '1000', created_at: '2026-01-01' },
      { status: 'active', investment_amount: '5000', created_at: '2026-02-01' },
      { status: 'closed', investment_amount: '10000', created_at: '2026-03-01' },
    ];

    it('filters by investmentMin', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.investmentMin = 3000;

      expect(applyFilters(diagnostics)).toHaveLength(2);
    });

    it('filters by investmentMax', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.investmentMax = 5000;

      expect(applyFilters(diagnostics)).toHaveLength(2);
    });

    it('filters by both investmentMin and investmentMax simultaneously', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.investmentMin = 2000;
      currentFilters.investmentMax = 8000;

      expect(applyFilters(diagnostics)).toHaveLength(1);
      expect(applyFilters(diagnostics)[0].investment_amount).toBe('5000');
    });

    it('treats missing investment_amount as zero when filtering by min', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.investmentMin = 100;

      const result = applyFilters([{ status: 'draft', investment_amount: null, created_at: '2026-01-01' }]);
      expect(result).toEqual([]);
    });
  });

  // ── applyFilters — date ranges ──────────────────────────────────────────────

  describe('applyFilters — date ranges', () => {
    const diagnostics = [
      { status: 'draft', investment_amount: '1000', created_at: '2026-01-15T12:00:00Z' },
      { status: 'active', investment_amount: '5000', created_at: '2026-03-15T12:00:00Z' },
    ];

    it('filters by createdAfter', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.createdAfter = '2026-02-01';

      expect(applyFilters(diagnostics)).toHaveLength(1);
      expect(applyFilters(diagnostics)[0].status).toBe('active');
    });

    it('filters by createdBefore', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.createdBefore = '2026-02-01';

      expect(applyFilters(diagnostics)).toHaveLength(1);
      expect(applyFilters(diagnostics)[0].status).toBe('draft');
    });

    it('filters by both createdAfter and createdBefore', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.createdAfter = '2026-01-01';
      currentFilters.createdBefore = '2026-02-28';

      expect(applyFilters(diagnostics)).toHaveLength(1);
      expect(applyFilters(diagnostics)[0].status).toBe('draft');
    });

    it('drops diagnostics with no created_at when a date range filter is active', () => {
      const { currentFilters, applyFilters } = useDiagnosticFilters();
      currentFilters.createdAfter = '2026-01-01';

      const result = applyFilters([{ status: 'draft', investment_amount: '0', created_at: null }]);
      expect(result).toEqual([]);
    });
  });

  // ── activeFilterCount ────────────────────────────────────────────────────────

  describe('activeFilterCount', () => {
    it('returns 0 when no filters are active', () => {
      const { activeFilterCount } = useDiagnosticFilters();

      expect(activeFilterCount.value).toBe(0);
    });

    it('counts statuses as one active dimension', () => {
      const { currentFilters, activeFilterCount } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      expect(activeFilterCount.value).toBe(1);
    });

    it('counts investmentMin and investmentMax as separate dimensions', () => {
      const { currentFilters, activeFilterCount } = useDiagnosticFilters();
      currentFilters.investmentMin = 1000;
      currentFilters.investmentMax = 5000;

      expect(activeFilterCount.value).toBe(2);
    });

    it('counts createdAfter and createdBefore as separate dimensions', () => {
      const { currentFilters, activeFilterCount } = useDiagnosticFilters();
      currentFilters.createdAfter = '2026-01-01';
      currentFilters.createdBefore = '2026-12-31';

      expect(activeFilterCount.value).toBe(2);
    });

    it('counts all five dimensions when fully populated', () => {
      const { currentFilters, activeFilterCount } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];
      currentFilters.investmentMin = 1000;
      currentFilters.investmentMax = 5000;
      currentFilters.createdAfter = '2026-01-01';
      currentFilters.createdBefore = '2026-12-31';

      expect(activeFilterCount.value).toBe(5);
    });
  });

  // ── hasActiveFilters ─────────────────────────────────────────────────────────

  describe('hasActiveFilters', () => {
    it('returns false when no filters are active', () => {
      const { hasActiveFilters } = useDiagnosticFilters();

      expect(hasActiveFilters.value).toBe(false);
    });

    it('returns true when at least one filter is active', () => {
      const { currentFilters, hasActiveFilters } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      expect(hasActiveFilters.value).toBe(true);
    });
  });

  // ── isTabLimitReached ────────────────────────────────────────────────────────

  describe('isTabLimitReached', () => {
    it('returns false when saved tabs are below the limit', () => {
      const { isTabLimitReached } = useDiagnosticFilters();

      expect(isTabLimitReached.value).toBe(false);
    });

    it('returns true when saved tabs reach 12', () => {
      const { savedTabs, isTabLimitReached } = useDiagnosticFilters();
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `t-${i}`, name: `Tab ${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      expect(isTabLimitReached.value).toBe(true);
    });
  });

  // ── Tab CRUD ─────────────────────────────────────────────────────────────────

  describe('tab CRUD', () => {
    it('saveTab creates a new tab with the current filter state', () => {
      const { currentFilters, savedTabs, saveTab } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      const tab = saveTab('Mi Tab');

      expect(tab).not.toBeNull();
      expect(tab.name).toBe('Mi Tab');
      expect(tab.filters.statuses).toEqual(['draft']);
      expect(savedTabs.value).toHaveLength(1);
    });

    it('saveTab returns null when the maximum tab count is reached', () => {
      const { savedTabs, saveTab } = useDiagnosticFilters();
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `tab-${i}`, name: `Tab ${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      const result = saveTab('Overflow');

      expect(result).toBeNull();
      expect(savedTabs.value).toHaveLength(12);
    });

    it('saveTab sets the new tab as the active tab', () => {
      const { activeTabId, savedTabs, saveTab } = useDiagnosticFilters();

      saveTab('Active Tab');

      expect(activeTabId.value).not.toBe('all');
      expect(savedTabs.value[0].id).toBe(activeTabId.value);
    });

    it('persists tabs to localStorage when tabs change', async () => {
      const { saveTab } = useDiagnosticFilters();

      saveTab('Persisted');
      await nextTick();

      expect(JSON.parse(localStorage.getItem('diagnostic_filter_tabs'))).toHaveLength(1);
    });

    it('deleteTab removes the specified tab', () => {
      const { savedTabs, saveTab, deleteTab } = useDiagnosticFilters();
      saveTab('To Delete');

      const tabId = savedTabs.value[0].id;
      deleteTab(tabId);

      expect(savedTabs.value).toHaveLength(0);
    });

    it('deleteTab resets to all when the active tab is deleted', () => {
      const { activeTabId, savedTabs, saveTab, deleteTab } = useDiagnosticFilters();
      saveTab('Active');

      const tabId = savedTabs.value[0].id;
      expect(activeTabId.value).toBe(tabId);
      deleteTab(tabId);

      expect(activeTabId.value).toBe('all');
    });

    it('deleteTab leaves other tabs intact when deleting an inactive tab', () => {
      const { savedTabs, saveTab, deleteTab } = useDiagnosticFilters();
      const tab1 = saveTab('First');
      saveTab('Second');

      deleteTab(tab1.id);

      expect(savedTabs.value).toHaveLength(1);
      expect(savedTabs.value[0].name).toBe('Second');
    });

    it('renameTab changes the name of the specified tab', () => {
      const { savedTabs, saveTab, renameTab } = useDiagnosticFilters();
      saveTab('Original');

      const tabId = savedTabs.value[0].id;
      renameTab(tabId, 'Renamed');

      expect(savedTabs.value[0].name).toBe('Renamed');
    });

    it('renameTab does nothing when the tab id is not found', () => {
      const { savedTabs, saveTab, renameTab } = useDiagnosticFilters();
      saveTab('Original');

      renameTab('missing-tab', 'Renamed');

      expect(savedTabs.value[0].name).toBe('Original');
    });

    it('auto-saves filter changes to the active tab via the watcher', async () => {
      const { currentFilters, savedTabs, saveTab } = useDiagnosticFilters();
      saveTab('Updatable');

      currentFilters.statuses = ['active'];
      await nextTick();

      expect(savedTabs.value[0].filters.statuses).toEqual(['active']);
    });

    it('does not auto-save filter changes when active tab is reset to all', async () => {
      const { currentFilters, savedTabs, saveTab, resetFilters } = useDiagnosticFilters();
      saveTab('Known');
      await nextTick();

      // Record state before switching to all
      const filtersBefore = JSON.stringify(savedTabs.value[0].filters);
      resetFilters(); // switches activeTabId to 'all'
      currentFilters.statuses = ['draft'];
      await nextTick();

      expect(JSON.stringify(savedTabs.value[0].filters)).toBe(filtersBefore);
    });

    it('skips rewriting a tab when the filters have not changed', async () => {
      const { savedTabs, saveTab } = useDiagnosticFilters();
      saveTab('Stable');

      const before = savedTabs.value[0].updatedAt;
      // No filter change — watcher fires but detects no diff
      await nextTick();

      expect(savedTabs.value[0].updatedAt).toBe(before);
    });
  });

  // ── resetFilters ─────────────────────────────────────────────────────────────

  describe('resetFilters', () => {
    it('clears all filter fields to their default values', () => {
      const { currentFilters, resetFilters } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];
      currentFilters.investmentMin = 1000;

      resetFilters();

      expect(currentFilters.statuses).toEqual([]);
      expect(currentFilters.investmentMin).toBeNull();
    });

    it('sets activeTabId back to all', () => {
      const { activeTabId, saveTab, resetFilters } = useDiagnosticFilters();
      saveTab('Tab');

      resetFilters();

      expect(activeTabId.value).toBe('all');
    });

    it('removes the diagnosticTab query param when resetting', async () => {
      mockRoute.query = { diagnosticTab: 'saved-1', search: 'keep-me' };
      const tabs = [{ id: 'saved-1', name: 'Saved', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('diagnostic_filter_tabs', JSON.stringify(tabs));

      const { resetFilters } = useDiagnosticFilters();
      resetFilters();
      await nextTick();

      expect(mockReplace).toHaveBeenLastCalledWith({ query: { search: 'keep-me' } });
    });
  });

  // ── selectTab ────────────────────────────────────────────────────────────────

  describe('selectTab', () => {
    it('selects all tab and resets current filters', () => {
      const { currentFilters, activeTabId, selectTab } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      selectTab('all');

      expect(activeTabId.value).toBe('all');
      expect(currentFilters.statuses).toEqual([]);
    });

    it('loads the saved filters when selecting a known tab', () => {
      const { currentFilters, savedTabs, activeTabId, selectTab } = useDiagnosticFilters();
      savedTabs.value = [{
        id: 'tab-x',
        name: 'Test',
        filters: { statuses: ['active'], investmentMin: null, investmentMax: null, createdAfter: null, createdBefore: null },
        createdAt: '',
        updatedAt: '',
      }];

      selectTab('tab-x');

      expect(activeTabId.value).toBe('tab-x');
      expect(currentFilters.statuses).toEqual(['active']);
    });

    it('sets the active tab without overwriting filters when tab id is unknown', () => {
      const { currentFilters, activeTabId, selectTab } = useDiagnosticFilters();
      currentFilters.statuses = ['draft'];

      selectTab('missing-tab');

      expect(activeTabId.value).toBe('missing-tab');
      expect(currentFilters.statuses).toEqual(['draft']);
    });
  });
});
