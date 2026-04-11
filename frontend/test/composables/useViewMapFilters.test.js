/**
 * Tests for the useViewMapFilters composable.
 *
 * Covers: initialization, applyFilters (category, audience, viewType dimensions),
 * activeFilterCount, tab CRUD (save, update, delete, rename), resetFilters, selectTab,
 * tab limit enforcement, and URL sync via viewTab query param.
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
import { useViewMapFilters } from '../../composables/useViewMapFilters';

// ── Test data factory ────────────────────────────────────────────────────────

function buildSections() {
  return [
    {
      id: 'public-site',
      label: 'Sitio publico',
      description: 'Vistas publicas',
      views: [
        { label: 'Inicio', url: '/', file: 'pages/index.vue', reference: 'inicio', audience: 'public', viewType: 'readonly' },
        { label: 'Blog', url: '/blog', file: 'pages/blog/index.vue', reference: 'blog', audience: 'public', viewType: 'list' },
        { label: 'Login LinkedIn', url: '/auth/linkedin/callback', file: 'pages/auth/linkedin/callback.vue', reference: 'linkedin', audience: 'public', viewType: 'auth' },
      ],
    },
    {
      id: 'admin-panel',
      label: 'Panel administrativo',
      description: 'Panel admin',
      views: [
        { label: 'Dashboard', url: '/panel', file: 'pages/panel/index.vue', reference: 'dashboard', audience: 'admin', viewType: 'dashboard' },
        { label: 'Crear propuesta', url: '/panel/proposals/create', file: 'pages/panel/proposals/create.vue', reference: 'crear', audience: 'admin', viewType: 'create' },
        { label: 'Editar propuesta', url: '/panel/proposals/:id/edit', file: 'pages/panel/proposals/[id]/edit.vue', reference: 'editar', audience: 'admin', viewType: 'edit' },
        { label: 'Listado propuestas', url: '/panel/proposals', file: 'pages/panel/proposals/index.vue', reference: 'listado', audience: 'admin', viewType: 'list' },
      ],
    },
    {
      id: 'client-platform',
      label: 'Plataforma de clientes',
      description: 'Portal clientes',
      views: [
        { label: 'Dashboard plataforma', url: '/platform/dashboard', file: 'pages/platform/dashboard.vue', reference: 'dashboard plat', audience: 'client', viewType: 'dashboard' },
        { label: 'Proyectos', url: '/platform/projects', file: 'pages/platform/projects/index.vue', reference: 'proyectos', audience: 'client', viewType: 'list' },
      ],
    },
  ];
}

describe('useViewMapFilters', () => {
  beforeEach(() => {
    localStorage.clear();
    mockRoute.query = {};
    mockReplace.mockClear();
    uuidCounter = 0;
  });

  // ── Initialization ──────────────────────────────────────────────────────────

  describe('initialization', () => {
    it('starts with empty filters and no saved tabs', () => {
      const { currentFilters, savedTabs, activeTabId } = useViewMapFilters();

      expect(activeTabId.value).toBe('all');
      expect(savedTabs.value).toEqual([]);
      expect(currentFilters.categories).toEqual([]);
      expect(currentFilters.audiences).toEqual([]);
      expect(currentFilters.viewTypes).toEqual([]);
    });

    it('loads saved tabs from localStorage', () => {
      const tabs = [{ id: 'tab-1', name: 'My tab', filters: { categories: ['admin-panel'], audiences: [], viewTypes: [] }, createdAt: '2026-01-01', updatedAt: '2026-01-01' }];
      localStorage.setItem('view_map_filter_tabs', JSON.stringify(tabs));
      mockRoute.query = { viewTab: 'tab-1' };

      const { savedTabs, activeTabId, currentFilters } = useViewMapFilters();

      expect(savedTabs.value).toHaveLength(1);
      expect(activeTabId.value).toBe('tab-1');
      expect(currentFilters.categories).toEqual(['admin-panel']);
    });

    it('falls back to all when viewTab references a missing tab', () => {
      mockRoute.query = { viewTab: 'nonexistent' };

      const { activeTabId } = useViewMapFilters();

      expect(activeTabId.value).toBe('all');
    });

    it('returns an empty savedTabs array when localStorage contains invalid JSON', () => {
      localStorage.setItem('view_map_filter_tabs', '{broken');

      const { savedTabs } = useViewMapFilters();

      expect(savedTabs.value).toEqual([]);
    });
  });

  // ── applyFilters ───────────────────────────────────────────────────────────

  describe('applyFilters', () => {
    it('returns all sections when no filters are active', () => {
      const { applyFilters } = useViewMapFilters();
      const sections = buildSections();

      const result = applyFilters(sections);

      expect(result).toHaveLength(3);
      expect(result[0].views).toHaveLength(3);
      expect(result[1].views).toHaveLength(4);
      expect(result[2].views).toHaveLength(2);
    });

    it('filters by single category', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('admin-panel');
      expect(result[0].views).toHaveLength(4);
    });

    it('filters by multiple categories', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['public-site', 'client-platform'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(2);
      expect(result.map((s) => s.id)).toEqual(['public-site', 'client-platform']);
    });

    it('filters by audience', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.audiences = ['admin'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('admin-panel');
    });

    it('filters by viewType', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.viewTypes = ['dashboard'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(2);
      expect(result[0].views).toHaveLength(1);
      expect(result[0].views[0].label).toBe('Dashboard');
      expect(result[1].views).toHaveLength(1);
      expect(result[1].views[0].label).toBe('Dashboard plataforma');
    });

    it('filters by multiple viewTypes', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.viewTypes = ['create', 'edit'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('admin-panel');
      expect(result[0].views).toHaveLength(2);
    });

    it('applies combined filters with AND logic', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];
      currentFilters.viewTypes = ['list'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(1);
      expect(result[0].views).toHaveLength(1);
      expect(result[0].views[0].label).toBe('Listado propuestas');
    });

    it('excludes sections with zero matching views', () => {
      const { applyFilters, currentFilters } = useViewMapFilters();
      currentFilters.audiences = ['client'];
      currentFilters.viewTypes = ['auth'];

      const result = applyFilters(buildSections());

      expect(result).toHaveLength(0);
    });
  });

  // ── activeFilterCount ──────────────────────────────────────────────────────

  describe('activeFilterCount', () => {
    it('returns 0 when no filters are set', () => {
      const { activeFilterCount } = useViewMapFilters();
      expect(activeFilterCount.value).toBe(0);
    });

    it('counts each non-empty dimension', () => {
      const { activeFilterCount, currentFilters } = useViewMapFilters();

      currentFilters.categories = ['admin-panel'];
      expect(activeFilterCount.value).toBe(1);

      currentFilters.audiences = ['admin'];
      expect(activeFilterCount.value).toBe(2);

      currentFilters.viewTypes = ['list'];
      expect(activeFilterCount.value).toBe(3);
    });

    it('sets hasActiveFilters to true when at least one dimension is active', () => {
      const { hasActiveFilters, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];
      expect(hasActiveFilters.value).toBe(true);
    });
  });

  // ── Tab CRUD ───────────────────────────────────────────────────────────────

  describe('tab operations', () => {
    it('saves a new tab with current filters', async () => {
      const { saveTab, savedTabs, activeTabId, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];

      const tab = saveTab('Admin views');

      expect(tab).not.toBeNull();
      expect(tab.name).toBe('Admin views');
      expect(tab.filters.categories).toEqual(['admin-panel']);
      expect(savedTabs.value).toHaveLength(1);
      expect(activeTabId.value).toBe(tab.id);

      await nextTick();
      expect(JSON.parse(localStorage.getItem('view_map_filter_tabs'))).toHaveLength(1);
    });

    it('prevents saving beyond tab limit', () => {
      const { saveTab, currentFilters } = useViewMapFilters();
      for (let i = 0; i < 12; i++) {
        saveTab(`Tab ${i}`);
      }

      const result = saveTab('One too many');
      expect(result).toBeNull();
    });

    it('marks the tab limit as reached when there are 12 saved tabs', () => {
      const { saveTab, isTabLimitReached } = useViewMapFilters();
      saveTab('Tab 0');
      saveTab('Tab 1');
      saveTab('Tab 2');
      saveTab('Tab 3');
      saveTab('Tab 4');
      saveTab('Tab 5');
      saveTab('Tab 6');
      saveTab('Tab 7');
      saveTab('Tab 8');
      saveTab('Tab 9');
      saveTab('Tab 10');
      saveTab('Tab 11');

      expect(isTabLimitReached.value).toBe(true);
    });

    it('deletes a tab and resets if it was active', () => {
      const { saveTab, deleteTab, savedTabs, activeTabId, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];
      const tab = saveTab('To delete');

      deleteTab(tab.id);

      expect(savedTabs.value).toHaveLength(0);
      expect(activeTabId.value).toBe('all');
      expect(currentFilters.categories).toEqual([]);
    });

    it('renames a tab', () => {
      const { saveTab, renameTab, savedTabs } = useViewMapFilters();
      const tab = saveTab('Original');

      renameTab(tab.id, 'Renamed');

      expect(savedTabs.value[0].name).toBe('Renamed');
    });

    it('does nothing when renaming an unknown tab', () => {
      const { renameTab, savedTabs } = useViewMapFilters();
      renameTab('missing', 'Renamed');
      expect(savedTabs.value).toEqual([]);
    });

    it('auto-updates active tab when filters change', async () => {
      const { saveTab, savedTabs, currentFilters } = useViewMapFilters();
      saveTab('Auto-update test');

      currentFilters.viewTypes = ['create'];
      await nextTick();

      expect(savedTabs.value[0].filters.viewTypes).toEqual(['create']);
    });

    it('does not update a missing tab id', async () => {
      const { savedTabs, activeTabId, currentFilters } = useViewMapFilters();
      savedTabs.value = [
        {
          id: 'tab-1',
          name: 'Admin',
          filters: { categories: [], audiences: [], viewTypes: [] },
          createdAt: '2026-01-01',
          updatedAt: '2026-01-01',
        },
      ];
      activeTabId.value = 'missing-tab';
      currentFilters.categories = ['admin-panel'];
      await nextTick();
      expect(savedTabs.value[0].filters.categories).toEqual([]);
    });

    it('does not update a tab when filters remain unchanged', async () => {
      const { saveTab, savedTabs } = useViewMapFilters();
      const tab = saveTab('Stable');
      const originalUpdatedAt = savedTabs.value[0].updatedAt;

      await nextTick();

      expect(savedTabs.value[0].id).toBe(tab.id);
      expect(savedTabs.value[0].updatedAt).toBe(originalUpdatedAt);
    });
  });

  // ── selectTab ──────────────────────────────────────────────────────────────

  describe('selectTab', () => {
    it('loads filters from the selected tab', () => {
      const { saveTab, selectTab, currentFilters } = useViewMapFilters();
      currentFilters.categories = ['public-site'];
      const tab = saveTab('Public');

      currentFilters.categories = [];
      selectTab('all');
      expect(currentFilters.categories).toEqual([]);

      selectTab(tab.id);
      expect(currentFilters.categories).toEqual(['public-site']);
    });

    it('resets filters when selecting all', () => {
      const { selectTab, currentFilters } = useViewMapFilters();
      currentFilters.audiences = ['admin'];

      selectTab('all');

      expect(currentFilters.audiences).toEqual([]);
    });

    it('keeps current filters when selecting an unknown tab id', () => {
      const { selectTab, currentFilters } = useViewMapFilters();
      currentFilters.audiences = ['admin'];

      selectTab('missing');

      expect(currentFilters.audiences).toEqual(['admin']);
    });
  });

  // ── resetFilters ───────────────────────────────────────────────────────────

  describe('resetFilters', () => {
    it('clears all filters and sets tab to all', () => {
      const { resetFilters, currentFilters, activeTabId } = useViewMapFilters();
      currentFilters.categories = ['admin-panel'];
      currentFilters.audiences = ['admin'];
      currentFilters.viewTypes = ['list'];

      resetFilters();

      expect(currentFilters.categories).toEqual([]);
      expect(currentFilters.audiences).toEqual([]);
      expect(currentFilters.viewTypes).toEqual([]);
      expect(activeTabId.value).toBe('all');
    });
  });

  // ── URL sync ───────────────────────────────────────────────────────────────

  describe('URL sync', () => {
    it('updates viewTab query param when tab changes', async () => {
      const { saveTab } = useViewMapFilters();
      const tab = saveTab('URL test');

      await nextTick();

      expect(mockReplace).toHaveBeenCalledWith(
        expect.objectContaining({ query: expect.objectContaining({ viewTab: tab.id }) }),
      );
    });

    it('removes viewTab query param when switching to all', async () => {
      const { saveTab, selectTab } = useViewMapFilters();
      saveTab('Temp');
      await nextTick();
      mockReplace.mockClear();

      selectTab('all');
      await nextTick();

      expect(mockReplace).toHaveBeenCalledWith(
        expect.objectContaining({ query: expect.not.objectContaining({ viewTab: expect.anything() }) }),
      );
    });
  });

  // ── isTabLimitReached ──────────────────────────────────────────────────────

  describe('isTabLimitReached', () => {
    it('returns true when at 12 tabs', () => {
      const { saveTab, isTabLimitReached } = useViewMapFilters();
      for (let i = 0; i < 12; i++) {
        saveTab(`Tab ${i}`);
      }

      expect(isTabLimitReached.value).toBe(true);
    });

    it('returns false when under limit', () => {
      const { saveTab, isTabLimitReached } = useViewMapFilters();
      saveTab('One');

      expect(isTabLimitReached.value).toBe(false);
    });
  });
});
