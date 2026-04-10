/**
 * Tests for the useProposalFilters composable.
 *
 * Covers: freshFilters, cloneFilters, loadTabs, spliceTab, applyFilters (all 11 dimensions),
 * activeFilterCount, tab CRUD (save, update, delete, rename), resetFilters, selectTab,
 * tab limit enforcement, and URL sync.
 *
 * Strategy: Mock vue-router + localStorage, then exercise the composable's public API.
 * Pure helpers are tested through the composable since they are module-scoped (not exported).
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
import { useProposalFilters } from '../../composables/useProposalFilters';

describe('useProposalFilters', () => {
  beforeEach(() => {
    localStorage.clear();
    mockRoute.query = {};
    mockReplace.mockClear();
    uuidCounter = 0;
  });

  // ── Initialization ──────────────────────────────────────────────────────────

  describe('initialization', () => {
    it('starts with empty filters and no saved tabs', () => {
      const { currentFilters, savedTabs, activeTabId } = useProposalFilters();

      expect(activeTabId.value).toBe('all');
      expect(savedTabs.value).toEqual([]);
      expect(currentFilters.statuses).toEqual([]);
      expect(currentFilters.isActive).toBe('all');
    });

    it('loads saved tabs from localStorage', () => {
      const tabs = [{ id: 'tab-1', name: 'Test', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('proposal_filter_tabs', JSON.stringify(tabs));

      const { savedTabs } = useProposalFilters();

      expect(savedTabs.value).toHaveLength(1);
      expect(savedTabs.value[0].name).toBe('Test');
    });

    it('returns empty array for corrupted localStorage', () => {
      localStorage.setItem('proposal_filter_tabs', 'invalid-json{');

      const { savedTabs } = useProposalFilters();

      expect(savedTabs.value).toEqual([]);
    });

    it('restores activeTabId from route query', () => {
      const tabs = [{ id: 'saved-1', name: 'Saved', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('proposal_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { tab: 'saved-1' };

      const { activeTabId } = useProposalFilters();

      expect(activeTabId.value).toBe('saved-1');
    });

    it('falls back to all when URL tab does not exist in saved tabs', () => {
      mockRoute.query = { tab: 'nonexistent' };

      const { activeTabId } = useProposalFilters();

      expect(activeTabId.value).toBe('all');
    });

    it('loads the saved tab filters and opens the filter panel from the URL query', () => {
      const tabs = [{
        id: 'saved-2',
        name: 'Saved',
        filters: {
          statuses: ['sent'],
          projectTypes: [],
          marketTypes: [],
          currencies: [],
          languages: [],
          investmentMin: null,
          investmentMax: null,
          heatScoreMin: null,
          heatScoreMax: null,
          viewCountMin: null,
          viewCountMax: null,
          createdAfter: null,
          createdBefore: null,
          lastActivityAfter: null,
          lastActivityBefore: null,
          isActive: 'all',
          technicalViewed: true,
        },
        createdAt: '',
        updatedAt: '',
      }];
      localStorage.setItem('proposal_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { tab: 'saved-2' };

      const { activeTabId, currentFilters, isFilterPanelOpen } = useProposalFilters();

      expect(activeTabId.value).toBe('saved-2');
      expect(currentFilters.statuses).toEqual(['sent']);
      expect(currentFilters.technicalViewed).toBe(true);
      expect(isFilterPanelOpen.value).toBe(true);
    });
  });

  // ── applyFilters — status ──────────────────────────────────────────────────

  describe('applyFilters — status', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 1, created_at: '2026-01-01', last_activity_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 10, created_at: '2026-02-01', last_activity_at: '2026-02-01', is_active: true },
      { status: 'viewed', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '10000', heat_score: 3, view_count: 20, created_at: '2026-03-01', last_activity_at: '2026-03-01', is_active: false },
      { status: 'finished', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '15000', heat_score: 10, view_count: 30, created_at: '2026-03-15', last_activity_at: '2026-03-15', is_active: true },
    ];

    it('returns all proposals when no filters active', () => {
      const { applyFilters } = useProposalFilters();

      expect(applyFilters(proposals)).toHaveLength(4);
    });

    it('filters by single status', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.statuses = ['draft'];

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('draft');
    });

    it('filters by multiple statuses', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.statuses = ['draft', 'sent'];

      expect(applyFilters(proposals)).toHaveLength(2);
    });

    it('filters by finished status independently from accepted', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.statuses = ['finished'];

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('finished');
    });
  });

  // ── applyFilters — projectType / marketType ───────────────────────────────

  describe('applyFilters — projectType', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 0, created_at: '2026-02-01', is_active: true },
    ];

    it('filters by project type', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.projectTypes = ['web'];

      expect(applyFilters(proposals)).toHaveLength(1);
    });

    it('filters by market type', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.marketTypes = ['b2c'];

      expect(applyFilters(proposals)).toHaveLength(1);
    });
  });

  // ── applyFilters — currency / language ────────────────────────────────────

  describe('applyFilters — currency and language', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 0, created_at: '2026-02-01', is_active: true },
    ];

    it('filters by currency', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.currencies = ['USD'];

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].currency).toBe('USD');
    });

    it('filters by language', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.languages = ['en'];

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].language).toBe('en');
    });
  });

  // ── applyFilters — investment range ───────────────────────────────────────

  describe('applyFilters — investment range', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 0, created_at: '2026-02-01', is_active: true },
      { status: 'viewed', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '10000', heat_score: 3, view_count: 0, created_at: '2026-03-01', is_active: true },
    ];

    it('filters by investmentMin', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.investmentMin = 3000;

      expect(applyFilters(proposals)).toHaveLength(2);
    });

    it('filters by investmentMax', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.investmentMax = 5000;

      expect(applyFilters(proposals)).toHaveLength(2);
    });

    it('filters by both min and max', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.investmentMin = 2000;
      currentFilters.investmentMax = 8000;

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].total_investment).toBe('5000');
    });
  });

  // ── applyFilters — heat score range ───────────────────────────────────────

  describe('applyFilters — heat score range', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 2, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 7, view_count: 0, created_at: '2026-02-01', is_active: true },
    ];

    it('filters by heatScoreMin', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.heatScoreMin = 5;

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].heat_score).toBe(7);
    });

    it('filters by heatScoreMax', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.heatScoreMax = 5;

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].heat_score).toBe(2);
    });
  });

  // ── applyFilters — view count range ───────────────────────────────────────

  describe('applyFilters — view count range', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 15, created_at: '2026-02-01', is_active: true },
    ];

    it('filters by viewCountMin', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.viewCountMin = 10;

      expect(applyFilters(proposals)).toHaveLength(1);
    });

    it('filters by viewCountMax', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.viewCountMax = 5;

      expect(applyFilters(proposals)).toHaveLength(1);
    });
  });

  // ── applyFilters — date ranges ────────────────────────────────────────────

  describe('applyFilters — date ranges', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-15T12:00:00Z', last_activity_at: '2026-01-20T12:00:00Z', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 0, created_at: '2026-03-15T12:00:00Z', last_activity_at: '2026-03-20T12:00:00Z', is_active: true },
    ];

    it('filters by createdAfter', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.createdAfter = '2026-02-01';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('sent');
    });

    it('filters by createdBefore', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.createdBefore = '2026-02-01';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('draft');
    });

    it('filters by lastActivityAfter', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.lastActivityAfter = '2026-02-01';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('sent');
    });

    it('filters by lastActivityBefore', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.lastActivityBefore = '2026-02-01';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].status).toBe('draft');
    });
  });

  // ── applyFilters — isActive ───────────────────────────────────────────────

  describe('applyFilters — isActive', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '5000', heat_score: 8, view_count: 0, created_at: '2026-02-01', is_active: false },
    ];

    it('returns all when isActive is all', () => {
      const { applyFilters } = useProposalFilters();

      expect(applyFilters(proposals)).toHaveLength(2);
    });

    it('filters only active proposals', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.isActive = 'active';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].is_active).toBe(true);
    });

    it('filters only inactive proposals', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.isActive = 'inactive';

      expect(applyFilters(proposals)).toHaveLength(1);
      expect(applyFilters(proposals)[0].is_active).toBe(false);
    });
  });

  // ── applyFilters — combined ───────────────────────────────────────────────

  describe('applyFilters — combined filters', () => {
    const proposals = [
      { status: 'draft', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '1000', heat_score: 5, view_count: 0, created_at: '2026-01-01', is_active: true },
      { status: 'sent', project_type: 'web', market_type: 'b2b', currency: 'COP', language: 'es', total_investment: '5000', heat_score: 8, view_count: 10, created_at: '2026-02-01', is_active: true },
      { status: 'draft', project_type: 'app', market_type: 'b2c', currency: 'USD', language: 'en', total_investment: '10000', heat_score: 3, view_count: 5, created_at: '2026-03-01', is_active: false },
    ];

    it('applies multiple filters simultaneously', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.statuses = ['draft'];
      currentFilters.currencies = ['COP'];

      const result = applyFilters(proposals);
      expect(result).toHaveLength(1);
      expect(result[0].total_investment).toBe('1000');
    });

    it('uses cached heat score and created_at fallback for activity filtering', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.heatScoreMin = 7;
      currentFilters.lastActivityAfter = '2026-04-01';

      const result = applyFilters([
        {
          status: 'sent',
          project_type: 'web',
          market_type: 'b2b',
          currency: 'COP',
          language: 'es',
          total_investment: '0',
          cached_heat_score: 8,
          view_count: 0,
          created_at: '2026-04-10T12:00:00Z',
          last_activity_at: null,
          is_active: true,
        },
      ]);

      expect(result).toHaveLength(1);
    });

    it('drops proposals without any activity date when an activity range is active', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.lastActivityAfter = '2026-04-01';

      const result = applyFilters([
        {
          status: 'sent',
          project_type: 'web',
          market_type: 'b2b',
          currency: 'COP',
          language: 'es',
          total_investment: '1200',
          heat_score: 8,
          view_count: 0,
          created_at: null,
          last_activity_at: null,
          is_active: true,
        },
      ]);

      expect(result).toEqual([]);
    });

    it('filters on technicalViewed when the engagement summary is missing', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.technicalViewed = true;

      const result = applyFilters([
        {
          status: 'sent',
          project_type: 'web',
          market_type: 'b2b',
          currency: 'COP',
          language: 'es',
          total_investment: '1200',
          heat_score: 8,
          view_count: 0,
          created_at: '2026-04-10',
          last_activity_at: '2026-04-10',
          is_active: true,
        },
      ]);

      expect(result).toEqual([]);
    });

    it('keeps proposals when technicalViewed is true and the engagement summary is true', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.technicalViewed = true;

      const result = applyFilters([
        {
          status: 'sent',
          project_type: 'web',
          market_type: 'b2b',
          currency: 'COP',
          language: 'es',
          total_investment: '1200',
          heat_score: 8,
          view_count: 0,
          created_at: '2026-04-10',
          last_activity_at: '2026-04-10',
          is_active: true,
          engagement_summary: { technical_viewed: true },
        },
      ]);

      expect(result).toHaveLength(1);
    });

    it('falls back to zero for missing cached heat score and missing view count', () => {
      const { currentFilters, applyFilters } = useProposalFilters();
      currentFilters.heatScoreMax = 0;
      currentFilters.viewCountMax = 0;

      const result = applyFilters([
        {
          status: 'sent',
          project_type: 'web',
          market_type: 'b2b',
          currency: 'COP',
          language: 'es',
          total_investment: '1200',
          heat_score: null,
          cached_heat_score: null,
          view_count: undefined,
          created_at: '2026-04-10',
          last_activity_at: '2026-04-10',
          is_active: true,
        },
      ]);

      expect(result).toHaveLength(1);
    });
  });

  // ── activeFilterCount ─────────────────────────────────────────────────────

  describe('activeFilterCount', () => {
    it('returns 0 when no filters active', () => {
      const { activeFilterCount } = useProposalFilters();

      expect(activeFilterCount.value).toBe(0);
    });

    it('increments per active dimension', () => {
      const { currentFilters, activeFilterCount } = useProposalFilters();
      currentFilters.statuses = ['draft'];
      currentFilters.currencies = ['COP'];

      expect(activeFilterCount.value).toBe(2);
    });

    it('counts range as single dimension', () => {
      const { currentFilters, activeFilterCount } = useProposalFilters();
      currentFilters.investmentMin = 1000;
      currentFilters.investmentMax = 5000;

      expect(activeFilterCount.value).toBe(1);
    });

    it('counts isActive when not all', () => {
      const { currentFilters, activeFilterCount } = useProposalFilters();
      currentFilters.isActive = 'active';

      expect(activeFilterCount.value).toBe(1);
    });

    it('counts technicalViewed and date ranges as active dimensions', () => {
      const { currentFilters, activeFilterCount } = useProposalFilters();
      currentFilters.createdAfter = '2026-01-01';
      currentFilters.lastActivityBefore = '2026-01-31';
      currentFilters.technicalViewed = true;

      expect(activeFilterCount.value).toBe(3);
    });

    it('counts the remaining array and range dimensions', () => {
      const { currentFilters, activeFilterCount } = useProposalFilters();
      currentFilters.projectTypes = ['webapp'];
      currentFilters.marketTypes = ['b2b'];
      currentFilters.languages = ['es'];
      currentFilters.heatScoreMin = 2;
      currentFilters.viewCountMax = 9;

      expect(activeFilterCount.value).toBe(5);
    });
  });

  // ── hasActiveFilters ──────────────────────────────────────────────────────

  describe('hasActiveFilters', () => {
    it('returns false when no filters active', () => {
      const { hasActiveFilters } = useProposalFilters();

      expect(hasActiveFilters.value).toBe(false);
    });

    it('returns true when any filter active', () => {
      const { currentFilters, hasActiveFilters } = useProposalFilters();
      currentFilters.statuses = ['draft'];

      expect(hasActiveFilters.value).toBe(true);
    });
  });

  // ── Tab CRUD ──────────────────────────────────────────────────────────────

  describe('tab CRUD', () => {
    it('saveTab creates a new tab with current filters', () => {
      const { currentFilters, savedTabs, saveTab } = useProposalFilters();
      currentFilters.statuses = ['draft'];

      const tab = saveTab('Mi Tab');

      expect(tab).not.toBeNull();
      expect(tab.name).toBe('Mi Tab');
      expect(tab.filters.statuses).toEqual(['draft']);
      expect(savedTabs.value).toHaveLength(1);
    });

    it('saveTab returns null when max tabs reached', () => {
      const { savedTabs, saveTab } = useProposalFilters();
      // Pre-fill 12 tabs
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `tab-${i}`, name: `Tab ${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      const result = saveTab('Overflow');

      expect(result).toBeNull();
      expect(savedTabs.value).toHaveLength(12);
    });

    it('saveTab sets the new tab as active', () => {
      const { activeTabId, savedTabs, saveTab } = useProposalFilters();

      saveTab('Active Tab');

      expect(activeTabId.value).not.toBe('all');
      expect(savedTabs.value[0].id).toBe(activeTabId.value);
    });

    it('persists the saved tabs to localStorage when tabs change', async () => {
      const { saveTab } = useProposalFilters();

      saveTab('Persisted');
      await nextTick();

      expect(JSON.parse(localStorage.getItem('proposal_filter_tabs'))).toHaveLength(1);
    });

    it('deleteTab removes the tab', () => {
      const { savedTabs, saveTab, deleteTab } = useProposalFilters();
      saveTab('To Delete');

      const tabId = savedTabs.value[0].id;
      deleteTab(tabId);

      expect(savedTabs.value).toHaveLength(0);
    });

    it('deleteTab resets to all when active tab is deleted', () => {
      const { activeTabId, savedTabs, saveTab, deleteTab } = useProposalFilters();
      saveTab('Active');

      const tabId = savedTabs.value[0].id;
      expect(activeTabId.value).toBe(tabId);
      deleteTab(tabId);

      expect(activeTabId.value).toBe('all');
    });

    it('does nothing when deleteTab receives an unknown id', () => {
      const { savedTabs, saveTab, deleteTab } = useProposalFilters();
      saveTab('Existing');

      deleteTab('missing-tab');

      expect(savedTabs.value).toHaveLength(1);
    });

    it('renameTab changes the tab name', () => {
      const { savedTabs, saveTab, renameTab } = useProposalFilters();
      saveTab('Original');

      const tabId = savedTabs.value[0].id;
      renameTab(tabId, 'Renamed');

      expect(savedTabs.value[0].name).toBe('Renamed');
    });

    it('does nothing when renameTab receives an unknown id', () => {
      const { savedTabs, saveTab, renameTab } = useProposalFilters();
      saveTab('Original');

      renameTab('missing-tab', 'Renamed');

      expect(savedTabs.value[0].name).toBe('Original');
    });

    it('updateTab updates the filters of existing tab', () => {
      const { currentFilters, savedTabs, saveTab, updateTab } = useProposalFilters();
      saveTab('Updatable');

      const tabId = savedTabs.value[0].id;
      currentFilters.statuses = ['sent'];
      updateTab(tabId);

      expect(savedTabs.value[0].filters.statuses).toEqual(['sent']);
    });

    it('does nothing when updateTab receives an unknown id', () => {
      const { savedTabs, saveTab, updateTab } = useProposalFilters();
      saveTab('Known');

      const before = JSON.stringify(savedTabs.value);
      updateTab('missing-tab');

      expect(JSON.stringify(savedTabs.value)).toBe(before);
    });

    it('skips rewriting a tab when the filters are unchanged', () => {
      const { savedTabs, saveTab, updateTab } = useProposalFilters();
      saveTab('Stable');

      const before = savedTabs.value[0].updatedAt;
      updateTab(savedTabs.value[0].id);

      expect(savedTabs.value[0].updatedAt).toBe(before);
    });
  });

  // ── resetFilters ──────────────────────────────────────────────────────────

  describe('resetFilters', () => {
    it('clears all filters to defaults', () => {
      const { currentFilters, resetFilters } = useProposalFilters();
      currentFilters.statuses = ['draft'];
      currentFilters.investmentMin = 1000;

      resetFilters();

      expect(currentFilters.statuses).toEqual([]);
      expect(currentFilters.investmentMin).toBeNull();
    });

    it('sets activeTabId to all', () => {
      const { activeTabId, saveTab, resetFilters } = useProposalFilters();
      saveTab('Tab');

      resetFilters();

      expect(activeTabId.value).toBe('all');
    });

    it('removes the tab query param when resetting to all', async () => {
      mockRoute.query = { tab: 'saved-1', search: 'keep-me' };
      const tabs = [{ id: 'saved-1', name: 'Saved', filters: {}, createdAt: '', updatedAt: '' }];
      localStorage.setItem('proposal_filter_tabs', JSON.stringify(tabs));

      const { resetFilters } = useProposalFilters();

      resetFilters();
      await nextTick();

      expect(mockReplace).toHaveBeenLastCalledWith({ query: { search: 'keep-me' } });
    });
  });

  // ── selectTab ─────────────────────────────────────────────────────────────

  describe('selectTab', () => {
    it('selects all and resets filters', () => {
      const { currentFilters, activeTabId, selectTab } = useProposalFilters();
      currentFilters.statuses = ['draft'];

      selectTab('all');

      expect(activeTabId.value).toBe('all');
      expect(currentFilters.statuses).toEqual([]);
    });

    it('loads filters from saved tab', () => {
      const { currentFilters, savedTabs, activeTabId, selectTab } = useProposalFilters();
      savedTabs.value = [{
        id: 'tab-x', name: 'Test',
        filters: { statuses: ['sent'], projectTypes: [], marketTypes: [], currencies: [], languages: [], investmentMin: null, investmentMax: null, heatScoreMin: null, heatScoreMax: null, viewCountMin: null, viewCountMax: null, createdAfter: null, createdBefore: null, lastActivityAfter: null, lastActivityBefore: null, isActive: 'all' },
        createdAt: '', updatedAt: '',
      }];

      selectTab('tab-x');

      expect(activeTabId.value).toBe('tab-x');
      expect(currentFilters.statuses).toEqual(['sent']);
    });

    it('does not overwrite filters when selecting an unknown saved tab', () => {
      const { currentFilters, activeTabId, selectTab } = useProposalFilters();
      currentFilters.statuses = ['draft'];

      selectTab('missing-tab');

      expect(activeTabId.value).toBe('missing-tab');
      expect(currentFilters.statuses).toEqual(['draft']);
    });
  });

  // ── isTabLimitReached ─────────────────────────────────────────────────────

  describe('isTabLimitReached', () => {
    it('returns false when under limit', () => {
      const { isTabLimitReached } = useProposalFilters();

      expect(isTabLimitReached.value).toBe(false);
    });

    it('returns true when at limit', () => {
      const { savedTabs, isTabLimitReached } = useProposalFilters();
      savedTabs.value = Array.from({ length: 12 }, (_, i) => ({
        id: `t-${i}`, name: `T${i}`, filters: {}, createdAt: '', updatedAt: '',
      }));

      expect(isTabLimitReached.value).toBe(true);
    });
  });
});
